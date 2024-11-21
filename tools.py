import os
from dotenv import load_dotenv

import boto3
import mysql.connector

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# db config
def get_db():

    # local mysql settings
    # db = mysql.connector.pooling.MySQLConnectionPool(
    #         pool_name="sql_pool",
    #         host=os.getenv('MYSQL_HOST'), 
    #         user=os.getenv('MYSQL_USER'), 
    #         password=os.getenv('MYSQL_PASSWORD'),
    #         database=os.getenv("MYSQL_DB")
    #     )
    
    # return db

    # aws rds mysql settings
    db_rds = mysql.connector.pooling.MySQLConnectionPool(
                pool_name = "sql_pool",
                host=os.getenv("AWS_RDS_HOSTNAME"),
                user=os.getenv("AWS_RDS_USER"),
                password=os.getenv("AWS_RDS_PASSWORD"),
                database=os.getenv("AWS_RDS_DB")
            )
    
    return db_rds

def get_12_articles_by_keyword(page, kw):
     
    sql = '''SELECT * FROM 
            (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
            FROM articles AS a
            LEFT JOIN resource AS r ON a.resource_id = r.id
            LEFT JOIN category AS c ON a.category_id = c.id
            WHERE a.title LIKE %s OR a.content LIKE %s OR c.category LIKE %s) AS subquery
            ORDER BY date DESC
            LIMIT %s, %s;'''
    
    page_size = 24 # judge the nextPage
    start = page * 12

	# Escaping wildcards in the parameter
    search_param = f"%{kw}%"
    keyword = (search_param, search_param, search_param, start, page_size)

    try:
        db = get_db()
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
                    'message': '資料超出頁數'}

    except mysql.connector.Error as err:

        print(f"Error: {err}")
        return {'error': True,
                'message': '資料輸出錯誤'}

    finally:

        con.close()
        Cursor.close()


def judge_filter_options(filter_requirements, page):
    
    page = int(page)

    start = page * 12
    page_size = 24

    category_lst = filter_requirements['category']
    category_str = ','.join(['%s'] * len(category_lst))
    #print(category_lst, category_str, *category_lst)

    resource_lst = filter_requirements['resource']
    resource_str = ','.join(['%s'] * len(resource_lst))
    #print(resource_lst, resource_str, *resource_lst)

    kw = filter_requirements['keyword']
    if kw != '':
        search_param = f"%{kw}%"
    else:
        search_param = ''

    if filter_requirements['date'] != []:
        date = filter_requirements['date'][0]
    else:
         date = ''

    variable = '%s'

    if len(category_lst) == 0 and len(resource_lst) != 0 and kw != '':
         
        sql = f'''SELECT * FROM 
                (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                FROM articles AS a
                LEFT JOIN resource AS r ON a.resource_id = r.id
                LEFT JOIN category AS c ON a.category_id = c.id
                WHERE (a.title LIKE {variable} OR a.content LIKE {variable}) 
                AND (a.resource_id IN ({resource_str}))
                AND (DATE(a.date) >= CURDATE() - INTERVAL {variable} DAY)) AS subquery
                ORDER BY date DESC
                LIMIT {variable}, {variable};'''

        variables = (search_param, search_param, *resource_lst, date, start, page_size)


    elif len(category_lst) != 0 and len(resource_lst) == 0 and kw != '':
         
        sql = f'''SELECT * FROM 
                (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                FROM articles AS a
                LEFT JOIN resource AS r ON a.resource_id = r.id
                LEFT JOIN category AS c ON a.category_id = c.id
                WHERE (a.title LIKE {variable} OR a.content LIKE {variable})
                AND (a.category_id IN ({category_str})) 
                AND (DATE(a.date) >= CURDATE() - INTERVAL {variable} DAY)) AS subquery
                ORDER BY date DESC
                LIMIT {variable}, {variable};'''

        variables = (search_param, search_param, *category_lst, date, start, page_size)


    elif len(category_lst) != 0 and len(resource_lst) != 0 and kw == '':
         
        sql = f'''SELECT * FROM 
                (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                FROM articles AS a
                LEFT JOIN resource AS r ON a.resource_id = r.id
                LEFT JOIN category AS c ON a.category_id = c.id
                WHERE (a.category_id IN ({category_str})) 
                AND (a.resource_id IN ({resource_str}))
                AND (DATE(a.date) >= CURDATE() - INTERVAL {variable} DAY)) AS subquery
                ORDER BY date DESC
                LIMIT {variable}, {variable};'''

        variables = (*category_lst, *resource_lst, date, start, page_size)


    elif len(category_lst) != 0 and len(resource_lst) == 0 and kw == '':
         
        sql = f'''SELECT * FROM 
                (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                FROM articles AS a
                LEFT JOIN resource AS r ON a.resource_id = r.id
                LEFT JOIN category AS c ON a.category_id = c.id
                WHERE (a.category_id IN ({category_str})
                AND (DATE(a.date) >= CURDATE() - INTERVAL {variable} DAY)) AS subquery
                ORDER BY date DESC
                LIMIT {variable}, {variable};'''

        variables = (*category_lst, date, start, page_size)


    elif len(category_lst) == 0 and len(resource_lst) != 0 and kw == '':
         
        sql = f'''SELECT * FROM 
                (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                FROM articles AS a
                LEFT JOIN resource AS r ON a.resource_id = r.id
                LEFT JOIN category AS c ON a.category_id = c.id
                WHERE (a.resource_id IN ({resource_str}))
                AND (DATE(a.date) >= CURDATE() - INTERVAL {variable} DAY)) AS subquery
                ORDER BY date DESC
                LIMIT {variable}, {variable};'''

        variables = (*resource_lst, date, start, page_size)


    elif len(category_lst) == 0 and len(resource_lst) == 0 and kw != '' and date == '':
         
        sql = f'''SELECT * FROM 
                (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                FROM articles AS a
                LEFT JOIN resource AS r ON a.resource_id = r.id
                LEFT JOIN category AS c ON a.category_id = c.id
                WHERE (a.title LIKE {variable} OR a.content LIKE {variable})) AS subquery
                ORDER BY date DESC
                LIMIT {variable}, {variable};'''

        variables = (search_param, search_param, start, page_size)


    elif len(category_lst) == 0 and len(resource_lst) == 0 and kw != '':
         
        sql = f'''SELECT * FROM 
                (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                FROM articles AS a
                LEFT JOIN resource AS r ON a.resource_id = r.id
                LEFT JOIN category AS c ON a.category_id = c.id
                WHERE (a.title LIKE {variable} OR a.content LIKE {variable})
                AND (DATE(a.date) >= CURDATE() - INTERVAL {variable} DAY)) AS subquery
                ORDER BY date DESC
                LIMIT {variable}, {variable};'''

        variables = (search_param, search_param, date, start, page_size)


    elif len(category_lst) != 0 and len(resource_lst) != 0 and kw != '':
         
        sql = f'''SELECT * FROM 
                (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                FROM articles AS a
                LEFT JOIN resource AS r ON a.resource_id = r.id
                LEFT JOIN category AS c ON a.category_id = c.id
                WHERE (a.title LIKE {variable} OR a.content LIKE {variable})
                AND (a.category_id IN ({category_str})) 
                AND (a.resource_id IN ({resource_str}))
                AND (DATE(a.date) >= CURDATE() - INTERVAL {variable} DAY)) AS subquery
                ORDER BY date DESC
                LIMIT {variable}, {variable};'''

        variables = (search_param, search_param, *category_lst, *resource_lst, date, start, page_size)


    elif len(category_lst) == 0 and len(resource_lst) == 0 and kw == '' and date == '':
         
        sql = f'''SELECT * FROM 
                (SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                FROM articles AS a
                LEFT JOIN resource AS r ON a.resource_id = r.id
                LEFT JOIN category AS c ON a.category_id = c.id) AS subquery
                ORDER BY date DESC
                LIMIT {variable}, {variable};'''

        variables = (start, page_size)

    return sql, variables 


# homepage filter search articles 
def get_12_articles_by_filter(filter_requirements, page):
    
    page = int(page)
    #print(filter_requirements, page)

    sql, variables = judge_filter_options(filter_requirements, page)
    #print(sql, variables)

    try:
        db = get_db()
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        Cursor.execute(sql, variables)
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

        db = get_db()
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        page_size = 24 # judge the nextPage
        start = page * 12

        sql_12 = '''SELECT c.category, a.title, a.wordcloud, r.resource, DATE(a.date) AS date, a.id 
                    FROM articles AS a 
                    LEFT JOIN resource AS r ON a.resource_id = r.id 
                    LEFT JOIN category AS c ON a.resource_id = c.id 
                    ORDER BY date DESC
                    LIMIT %s, %s;'''
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
# article page Cache 
# 順序上 資料由舊到新

# # 設定鍵值對
# client.set('mykey', 'Hello, Redis!')

# # 讀取鍵值對
# value = client.get('mykey')
# print(value.decode())  # Output: Hello, Redis!

class Cache():
    def __init__(self):
          self.data = []
          self.max = 10
    
    def get(self, key):
        for i in range(len(self.data)-1, -1, -1):
            if self.data[i]['key'] == key:
                item = self.data[i]
                del self.data[i]
                self.data.append(item)
                return item['value']
        return None
    
    def put(self, key, value):
        if len(self.data) > self.max:
            self.data = self.data[self.max//2:]
        self.data.append({
             "key": key, "value": value
        })

Cache = Cache()                


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
            IndexName='member_id-index',  # 如果有局部索引，可以利用
            KeyConditionExpression='#member_id = :member_id',
            ExpressionAttributeNames={
                '#member_id': 'member_id'
            },
            ExpressionAttributeValues={
                ':member_id': {'S': member_id}
            },
            ScanIndexForward=False
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
        db = get_db()
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

    
##########################
# 會員文章收藏 RDMS version

# get collections
# @app.get("/api/collect")
# async def get_previous_collection(member_id: int, page: int = Query(1)):
	
#     result_json = {}
	
#     try:
    
#         sql = '''SELECT * FROM (
# 		         SELECT a.title, a.forum, a.resource, a.date, a.url
# 		         FROM collections AS c
# 		         INNER JOIN articles AS a ON c.article_id = a.id
# 				 WHERE c.member_id = %s
# 				 ORDER BY c.collect_date DESC
# 				 ) AS t
# 				 LIMIT %s, %s;'''
		
#         con = db.get_connection()
#         Cursor = con.cursor(dictionary=True)
		
#         page_size = 12 
#         start = (page - 1) * 12
#         get_collect = (member_id, (start, page_size))
#         Cursor.execute(sql, get_collect)
#         collect_articles = Cursor.fetchall()

#         result_json['data'] = collect_articles
		
#         return result_json

#     except Exception as e:

#         raise CustomHTTPException(status_code=500, detail=str(e))

#     finally:
		
#         con.close()
#         Cursor.close()
		

# # collect article
# @app.post("/api/collect")
# async def insert_collection(collect_info: collect_info):
	
#     result_json = {}
	
#     try:
    
#         sql = '''INSERT INTO collections (member_id, article_id) VALUES (%s, %s);'''
#         con = db.get_connection()
#         Cursor = con.cursor(dictionary=True)
		
#         insert_collect = (collect_info.member_id, collect_info.article_id)
#         Cursor.execute(sql, insert_collect)
#         con.commit()

#         result_json['ok'] = True
		
#         return result_json

#     except Exception as e:

#         raise CustomHTTPException(status_code=500, detail=str(e))

#     finally:
		
#         con.close()
#         Cursor.close()
		

# # delete article collection
# @app.delete("/api/collect")
# async def delete_collection(collect_info: collect_info):
	
#     result_json = {}
	
#     try:
    
#         sql = '''DELETE FROM collections WHERE member_id = %s AND article_id = %s;'''
#         con = db.get_connection()
#         Cursor = con.cursor(dictionary=True)
		
#         insert_collect = (collect_info.member_id, collect_info.article_id)
#         Cursor.execute(sql, insert_collect)
#         con.commit()

#         result_json['ok'] = True
		
#         return result_json

#     except Exception as e:

#         raise CustomHTTPException(status_code=500, detail=str(e))

#     finally:
		
#         con.close()
#         Cursor.close()