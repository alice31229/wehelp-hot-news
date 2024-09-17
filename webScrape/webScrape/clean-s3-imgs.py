import os
import boto3
import datetime
from dotenv import load_dotenv

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path)

session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
s3 = session.client('s3')

# S3 bucket & photo id
bucket_name = os.getenv('AWS_BUCKET_NAME')

# 計算七天前的日期
seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)

# 列出 S3 存儲桶中的所有檔案
response = s3.list_objects_v2(Bucket=bucket_name)
# print(response)
# print('#################')
# print(response['Contents'])

# 設定要篩選的資料夾
directories_to_check = ['wordcloud/', 'network/']

# 遍歷每個資料夾
for directory in directories_to_check:
    print(f"Checking files in {directory}...")

    continuation_token = None

    while True:
        # 列出資料夾中的檔案
        if continuation_token:
            response = s3.list_objects_v2(Bucket=bucket_name, Prefix=directory, ContinuationToken=continuation_token)
        else:
            response = s3.list_objects_v2(Bucket=bucket_name, Prefix=directory)

        # 如果有檔案的情況下
        if 'Contents' in response:
            for obj in response['Contents']:

                file_key = obj['Key']
                last_modified = obj['LastModified']

                if file_key != directory and last_modified < seven_days_ago:

                    # 列印每個檔案的完整 Key
                    print(f"File found in {directory}: {file_key}")

                    # 如果檔案修改日期早於七天前，則執行刪除
                    
                    print(f"Deleting {file_key}, last modified: {last_modified}")
                    s3.delete_object(Bucket=bucket_name, Key=file_key)
        else:
            print(f"No files found in {directory}.")

        # 檢查是否還有更多分頁
        if response.get('IsTruncated'):  # 是否還有更多結果
            continuation_token = response['NextContinuationToken']
        else:
            break
