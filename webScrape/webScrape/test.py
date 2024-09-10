import pandas as pd
# from datetime import datetime, timedelta

# yesterday = datetime.now() - timedelta(days=1)
# yesterday = yesterday.strftime('%Y-%m-%d')

# ptt = pd.read_csv(f'./data_ETL/after_webscrape/ptt-test_{yesterday}.csv')
# storm = pd.read_csv(f'./data_ETL/after_webscrape/storm-test_{yesterday}.csv')
# udn = pd.read_csv(f'./data_ETL/after_webscrape/udn-test_{yesterday}.csv')
# businesstoday = pd.read_csv(f'./data_ETL/after_webscrape/businesstoday-test_{yesterday}.csv')

# df = pd.concat([ptt, storm, udn, businesstoday], ignore_index=True)
# df = df[df['文章內容'].notnull()]


# df.to_csv('clean-test.csv', index=False)

import os
import boto3
import mysql.connector
from dotenv import load_dotenv

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../../config/.env')
load_dotenv(dotenv_path)

# db config
# local mysql settings
db = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="sql_pool",
    host=os.getenv('MYSQL_HOST'), # in same ec2 use localhost; otherwise, use the endpoint
    user=os.getenv('MYSQL_USER'), 
    password=os.getenv('MYSQL_PASSWORD'),
	database=os.getenv("MYSQL_DB"))


def delete_by_article_id_with_scan(article_ids):

    # 建立 DynamoDB client
    # session = boto3.Session(
    #     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    #     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    #     region_name=os.getenv("AWS_REGION")
    # )

    # dynamodb = session.client('dynamodb')
    # table = os.getenv("AWS_DYNAMODB") 

    # 直接使用 boto3.client 或 boto3.resource
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    table_name = os.getenv("AWS_DYNAMODB") 
    table = dynamodb.Table(table_name)

    try:
        # 扫描符合条件的记录
        # response = table.scan(
        #     FilterExpression=boto3.dynamodb.conditions.Attr('article_id').eq(article_id)
        # )
        response = table.scan()
        items = response['Items']

        # 遍历扫描结果并删除
        for item in items:
            
            article_id = item['article_id']
            if article_id in article_ids:
                member_id = item['member_id']
                # 删除指定记录
                table.delete_item(
                    Key = {
                        'member_id': member_id,
                        'article_id': article_id
                    }
                )
                print(f"Deleted record with member_id: {member_id}, article_id: {article_id}")

    except Exception as e:
        print(f"Error deleting records: {e}")


def delete_collect_records_week_ago():

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        
        collect_articles_delete = '''SELECT id FROM articlesDelete;'''

        Cursor.execute(collect_articles_delete)
        delete_list_result = Cursor.fetchall()

        df = pd.DataFrame(delete_list_result)
        df['id'] = df['id'].astype(str)

        check_ids = set(df['id'])


        delete_by_article_id_with_scan(check_ids)

            # try:
            #     # 刪除要用key參數傳遞
            #     key = {
            #         'member_id': {'S': str(delete_data.memberId)},
            #         'article_id': {'S': str(d)}
            #     }
                
            #     dynamodb.delete_item(TableName=table_name, Key=key)

            # except:
            #     pass

        return True

        #delete_articlesDelete_data = '''TRUNCATE TABLE articlesDelete;'''


    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")
        

    finally:
        con.close()
        Cursor.close()

delete_collect_records_week_ago()