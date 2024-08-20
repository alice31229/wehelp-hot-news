import os
import uuid
from dotenv import load_dotenv

import boto3
import mysql.connector

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../config/.env')
load_dotenv(dotenv_path)

# db config
# local mysql settings
db = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="sql_pool",
    host=os.getenv('MYSQL_HOST'), # in same ec2 use localhost; otherwise, use the endpoint
    user=os.getenv('MYSQL_USER'), 
    password=os.getenv('MYSQL_PASSWORD'),
	database=os.getenv("MYSQL_DB"))

# aws rds mysql settings
# db = mysql.connector.pooling.MySQLConnectionPool(
#         pool_name = "sql_pool",
#         host=os.getenv("AWS_RDS_HOSTNAME"),
#         user=os.getenv("AWS_RDS_USER"),
#         password=os.getenv("AWS_RDS_PASSWORD"),
#         database=os.getenv("AWS_RDS_DB"))

# homepage keyword search data 
def get_12_articles_by_keyword(kw, page=0):

	# sql = 'SELECT * FROM articles WHERE MATCH(title) AGAINST (%s) OR MATCH(content) AGAINST (%s)'
	# sql = "SELECT * FROM articles WHERE title like %s OR content like %s;"

	# 用來完全比對文章類別名稱、或模糊比對文章名稱或文章內文的關鍵字，沒有給定則不做篩選
	sql = '''SELECT * FROM (SELECT forum, title, wordcloud, resource, id FROM articles WHERE title like %s OR content like %s OR forum = %s ) AS subquery LIMIT %s, %s;'''

	page_size = 24 # judge the nextPage
	start = page * 12

	# Escaping wildcards in the parameter
	search_param = f"%{kw}%"
	keyword = (search_param, search_param, kw, start, page_size)

	try:
		
		con = db.get_connection()
		Cursor = con.cursor(dictionary=True)
		Cursor.execute(sql, keyword)
		query_result = Cursor.fetchall()
		next_page_judge = len(query_result)

		if next_page_judge < 13 and next_page_judge > 0:

			return {'nextPage': None,
					'data': query_result[:next_page_judge]}
		
		elif next_page_judge > 12:

			return {'nextPage': page+1,
					'data': query_result[:12]}

		else:

			return {'error': True,
					'message': '文章資料超出頁數'}

	except mysql.connector.Error as err:

		print(f"Error: {err}")
		return {'error': True,
				'message': '文章資料輸出錯誤'}

	finally:

		con.close()
		Cursor.close()


# homepage infinite scroll data
def get_12_articles_by_page(page):

	try:

		con = db.get_connection()
		Cursor = con.cursor(dictionary=True)
		page_size = 24 # judge the nextPage
		start = page * 12

		sql_12 = '''SELECT forum, title, wordcloud, resource, id FROM articles LIMIT %s, %s;'''
		Cursor.execute(sql_12, (start, page_size))
		demand_articles = Cursor.fetchall()


		if len(demand_articles) > 12:
		
			return {'nextPage': page+1,
					'data': demand_articles[:12]}
		
		elif len(demand_articles) < 13 and len(demand_articles) > 0:

			return {'nextPage': None,
					'data': demand_articles}

		else:

			return {'error': True,
				    'message': '請輸入涵蓋文章資料的正確頁數'}
			

	except mysql.connector.Error as err:

		print(f"Error: {err}")
		return {'error': True,
				'message': '文章資料輸出錯誤'}

	finally:

		con.close()
		Cursor.close()


######################################
# member collect article [dynamodb]

def get_all_collection_member(member_id):
    """
    Fetches the list of articles collected by a member from DynamoDB.

    Args:
        member_id (string): The ID of the member.

    Returns:
        list: A list of collected articles.
    """

    # Create DynamoDB client
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    dynamodb = session.client('dynamodb')
    table_name = os.getenv("AWS_DYNAMODB")

    member_id = str(member_id)

    try:
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression='#member_id = :member_id',
            ExpressionAttributeNames={
                '#member_id': 'member_id'
            },
            ExpressionAttributeValues={
                ':member_id': {'S': member_id}
            }
        )

        items = response['Items']

        while 'LastEvaluatedKey' in response:
            response = dynamodb.query(
                TableName=table_name,
                KeyConditionExpression='#member_id = :member_id',
                ExpressionAttributeNames={
                    '#member_id': 'member_id'
                },
                ExpressionAttributeValues={
                    ':member_id': {'S': member_id}
                },
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])

        return items

    except Exception as e:
        print(f"An error occurred: {e}")
        return []



# insert into dynamodb
def insert_into_dynamodb(collect_data):
    """
    將 會員收藏文章 的資料插入 DynamoDB

    Args:
        collect_data (dict)

    Returns:
        bool
    """

    # 建立 DynamoDB client
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    dynamodb = session.client('dynamodb')
    table_name = os.getenv("AWS_DYNAMODB") 

    try:
        item = { # forum, title, content, resource, date, url
            #'id': {'S': uuid.uuid4()},  # 使用uuid作為主鍵
            'member_id': {'S': str(collect_data['member_id'])},
            'article_id': {'S': str(collect_data['article_id'])},
            'collect_date': {'N': str(collect_data['collect_date'])}
            # ... 其他欄位
        }
        dynamodb.put_item(TableName=table_name, Item=item)

        return True
    
    except Exception as e:

        print(f"An error occurred: {str(e)}")

        return False
    

# delete from dynamodb
def delete_from_dynamodb(delete_data):
    """
    將 會員收藏文章 的資料從 DynamoDB 刪除

    Args:
        delete_data (dict)

    Returns:
        bool
    """

    # 建立 DynamoDB client
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    dynamodb = session.client('dynamodb')
    table_name = os.getenv("AWS_DYNAMODB")  

    try:
        # 刪除要用key參數傳遞
        key = {
            'member_id': {'S': str(delete_data.memberId)},
            'article_id': {'S': str(delete_data.articleId)}
        }
        
        dynamodb.delete_item(TableName=table_name, Key=key)

        return True
    
    except Exception as e:

        print(f"An error occurred: {str(e)}")

        return False


################## update member info ####################

def update_selfie_s3(member_selfie_id, img_input, img_type):

    try:

        # AWS S3 settings
        session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
        )
        s3 = session.client('s3')

        # S3 bucket & photo id
        bucket_name = os.getenv('AWS_BUCKET_NAME')

        s3_object_key = f'member_selfie/{member_selfie_id}'
        
        # upload photo to S3
        s3.put_object(Bucket=bucket_name, Key=s3_object_key, Body=img_input, ContentType=img_type)

        return True

    except:

        return False
    

def update_member_info_rds(new_info):

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)


        update_info = '''UPDATE articlesLand.members 
                        SET name = %s, email = %s, selfie = %s
                        WHERE username = %s;'''
        member_info = (new_info['name'], new_info['email'], str(new_info['selfie']), new_info['username'])

        Cursor.execute(update_info, member_info)
        con.commit()

        return True

    except Exception as e:

        return False
    
    finally:

        con.close()
        Cursor.close()


# insert message and image url into rds db
def save_data_to_db(df, type):

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)

        if type == 'article':

            insert_sql = '''INSERT INTO articlesLand.articles (forum, title, content, resource, date, url, wordcloud) VALUES (%s, %s, %s, %s, %s, %s, %s);'''

            with con.cursor(dictionary=True) as cursor:
                for row in df.itertuples(index=False):
                    cursor.execute(insert_sql, row)
                con.commit()


        elif type == 'member':

            insert_member = '''INSERT INTO articlesLand.members (name, username, password, email) VALUES (%s, %s, %s, %s);'''
            member_data = (df['name'], df['username'], df['password'], df['email'])

            Cursor.execute(insert_member, member_data)
            con.commit()

        return True

    except Exception as e:

        return False
    
    finally:

        con.close()
        Cursor.close()

    