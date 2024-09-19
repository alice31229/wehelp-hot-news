import os
from dotenv import load_dotenv
import mysql.connector
import uvicorn
from fastapi import *
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


import jwt
#import redis
import bcrypt
import mysql.connector
#from typing import Optional
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from BaseModel.json_info import user_info, member_log_in_info, collect_info, member_update_info, articles_requirements, resourceID

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# .env for config
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# 連接 Redis
#redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# trending-news
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/homepage.html", media_type="text/html")

@app.get("/article/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/article.html", media_type="text/html")

@app.get("/member", include_in_schema=False)
async def member(request: Request):
	return FileResponse("./static/member.html", media_type="text/html")



# api for other web page data retrieve
@app.get("/api/articles")
async def handle_articles_page(page: int = Query(0), keyword: str = Query('')):

    from tools import get_12_articles_by_page, get_12_articles_by_keyword

    if keyword == '':

        # call only get_12_attractions_by_page
        status_json = get_12_articles_by_page(page)

    else:

        status_json = get_12_articles_by_keyword(page, keyword)
    
    return status_json


# article content, wordcloud, analysis charts
@app.get("/api/article/{id}")
async def get_target_article_info(id: int):
	
    from tools import db, Cache

    # 如果快取有資料 就直接拿 沒有就去資料庫抓
    result = Cache.get("article-"+str(id))
    if result != None:
         
         return {'data': result}

    try:

        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)

        search_article = '''SELECT a.title, c.category, a.overview, a.content, r.resource, DATE(a.date) AS date, a.url, a.wordcloud, a.network
                            FROM articles AS a
                            INNER JOIN category AS c
                            ON a.category_id = c.id
                            INNER JOIN resource AS r
                            ON a.resource_id = r.id
                            WHERE a.id = %s;'''
        target_ID = (id,)
        Cursor.execute(search_article, target_ID)
        target_article = Cursor.fetchall()


        if target_article != []:
            
            query_result = target_article[0]
            article_json = {'data': query_result}

            # 快取沒抓到 這邊把去資料庫抓的放到快取預備
            Cache.put('article-'+str(id), query_result)

            return article_json

        else:
            article_json = {'error': True,
                            'message': '無此文章'}

            return article_json

    except mysql.connector.Error as err:

        print(f"Error: {err}")
        return {'error': True,
                'message': '文章資料輸出錯誤'}

    finally:
        
        Cursor.close()
        con.close()

		
@app.get("/api/hotkeywords") # elastic?
async def get_hot_keywords():
     
     from tools import db

     hot_keywords = []

     try:
        sql = '''SELECT DISTINCT h.keyword
                 FROM hotKeywords AS h
                 INNER JOIN resource AS r
                 ON h.resource_id = r.id;'''
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        Cursor.execute(sql)
        #Cursor.execute(sql, (resource,))
        hot_keywords_result = Cursor.fetchall()

        for hk in hot_keywords_result:
            # 把數字篩掉
            if hk['keyword'].isdigit():
                pass
            else:
                hot_keywords.append(hk['keyword'])

        forums_json = {'data':hot_keywords}

        return forums_json
     
     except mysql.connector.Error as err:
        
        return {'error': True,
                'message': err}
     
     finally:

        con.close()
        Cursor.close()


# filter category
@app.get("/api/filter-category")
async def get_all_category():
     
    from tools import db

    try:
        sql = '''SELECT * FROM category;'''
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        Cursor.execute(sql)
        category_result = Cursor.fetchall()

        category_json = {'data': category_result}

        return category_json

    except mysql.connector.Error as err:
        
        return {'error': True,
                'message': err}

    finally:

        con.close()
        Cursor.close()


# filter articles requirements query
@app.post("/api/filter-articles-search")
#async def get_demanded_articles(articles_requirements: articles_requirements, page: int = Query(0)):
async def get_demanded_articles(articles_requirements: articles_requirements):

    from tools import get_12_articles_by_filter

    #print(articles_requirements, type(articles_requirements))
    articles_requirements = articles_requirements.dict()

    input_requirement = {}
    page = ''

    for k,v in articles_requirements.items():
        if k == 'keyword':
            input_requirement[k] = v
        elif k == 'resources':
            input_requirement['resource'] = v
        elif k == 'categories':
            input_requirement['category'] = v
        elif k == 'dates':
            input_requirement['date'] = v 
        elif k == 'page':
            page = v

    #print('arrange requirement:', input_requirement)

    result = get_12_articles_by_filter(input_requirement, page)
    #print(result)


    if 'error' in result.keys():

        return {'error': True,
                'message': '文章擷取問題'}

    else:
         
        return result
    

# homepage mrt click keyword search api router
@app.get("/api/forums")
async def get_forum_info():

    from tools import db
    
    forums = []

    try:
        sql = '''SELECT c.category, COUNT(*) AS category_cnt
                 FROM articles AS a
                 INNER JOIN category AS c
                 ON a.category_id = c.id
                 GROUP BY c.category
                 ORDER BY 2 DESC;'''
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        Cursor.execute(sql)
        sorted_forums = Cursor.fetchall()

        for sm in sorted_forums:
            forums.append(sm['category'])

        forums_json = {'data':forums}

        return forums_json

    except mysql.connector.Error as err:
        
        return {'error': True,
                'message': err}

    finally:

        con.close()
        Cursor.close()


# homepage mrt click keyword search api router
@app.post("/api/resource-category-distribution")
async def get_resource_category_info(resource_id: resourceID):

    from tools import db

    try:
        # sql = '''SELECT r.resource, c.category, COUNT(*) AS category_cnt
        #          FROM articles AS a
        #          LEFT JOIN category AS c
        #          ON a.category_id = c.id
        #          LEFT JOIN resource AS r
        #          ON a.resource_id = r.id
        #          where DATE(date) = CURDATE() - INTERVAL 1 DAY
        #          GROUP BY r.resource, c.category;'''
        if resource_id.resourceId != 5:
            sql = '''SELECT c.category, COUNT(*) AS category_cnt
                    FROM articles AS a
                    LEFT JOIN category AS c
                    ON a.category_id = c.id
                    WHERE DATE(date) = CURDATE() - INTERVAL 1 DAY
                    AND a.resource_id = %s
                    GROUP BY c.category
                    ORDER BY 2 DESC;'''
            con = db.get_connection()
            Cursor = con.cursor(dictionary=True)
            Cursor.execute(sql, (resource_id.resourceId,))
            resource_category_cnt = Cursor.fetchall()

        else:
            sql = '''SELECT c.category, COUNT(*) AS category_cnt
                    FROM articles AS a
                    LEFT JOIN category AS c
                    ON a.category_id = c.id
                    WHERE DATE(date) = CURDATE() - INTERVAL 1 DAY
                    GROUP BY c.category
                    ORDER BY 2 DESC;'''
            con = db.get_connection()
            Cursor = con.cursor(dictionary=True)
            Cursor.execute(sql)
            resource_category_cnt = Cursor.fetchall()

        forums_json = {'data':resource_category_cnt}

        return forums_json

    except mysql.connector.Error as err:
        
        return {'error': True,
                'message': err}

    finally:

        con.close()
        Cursor.close()


##########################
# 登入驗證機制		
# user enroll or member log in/out JWT settings
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# password handle
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

secret_key = os.getenv('SECRET_KEY')
algorithm = os.getenv('ALGORITHM')

def encode_password(password: str) -> str:

	hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
	return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# token時效為七天
def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
	to_encode = data.copy()
	expire = datetime.now() + expires_delta
	encoded_jwt = jwt.encode({**to_encode, "exp": expire}, secret_key, algorithm=algorithm)
	return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])

        # 檢查token是否在有效期內（七天）
		# 避免aws時區造成問題
        now = datetime.utcnow()  # 使用UTC時間比對，且沒有時區資訊
        exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc).replace(tzinfo=None)  # 轉換為沒有時區資訊的時間
        
        if now < exp:
            return payload
        else:
            return None
		
    except jwt.ExpiredSignatureError: # 驗證是否在有效期七天內
        return None
    
    except jwt.InvalidTokenError: 
        return None
	
# 登入錯誤驗證class
# 自定義的 HTTPException
class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)
        self.content = {"error": True, "message": detail}

# 登入驗證
def login_required(token: str = Depends(oauth2_scheme)):
	payload = decode_access_token(token)
	if payload is None:
		raise CustomHTTPException(status_code=403, detail='尚未登入，收藏文章存取遭拒')
	return payload


##########################
# 各種會員資料

# 登入帳號
@app.put("/api/user/auth")
async def sign_in(member_info: member_log_in_info):
#async def sign_in(email: str = Form(...), password: str = Form(...)):

    from tools import db

    response_json = {}

    if member_info.username == '' or member_info == '':
         
         response_json['error'] = True
         response_json['message'] = '請輸入使用者名稱、密碼'

         return response_json

    try:

        query = '''SELECT id, name, email, password, username, selfie FROM members WHERE username = %s;'''
        account = (member_info.username,)

        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        Cursor.execute(query, account)
        fetch_result = Cursor.fetchall()

        if len(fetch_result) == 0:
             
            response_json["error"] = True
            response_json["message"] = '無此會員，請先註冊'
        
            return response_json

        elif not fetch_result or not verify_password(member_info.password, fetch_result[0]['password']):

            error_message = '使用者名稱或密碼輸入錯誤'

            response_json["error"] = True
            response_json["message"] = error_message

            return response_json

        else:

            # check query result
            member_id = fetch_result[0]['id']
            name = fetch_result[0]['name']
            email = fetch_result[0]['email']
            username = fetch_result[0]['username']
            selfie = fetch_result[0]['selfie']

            # 生成 JWT token
            token = create_access_token(data={"user_id": member_id, "email": email, "name": name, "username": username, "selfie": selfie})
            
            response_json["token"] = token

            return response_json

    except Exception as e:

        raise CustomHTTPException(status_code=500, detail=str(e))
        
    finally:

        Cursor.close()
        con.close()


# 登入會員資訊
@app.get("/api/user/auth")
async def get_user_info(token: str = Depends(oauth2_scheme)):

	response_json = {"data": ''}
	payload = decode_access_token(token)

	if payload is None:
		response_json['data'] = None

	else:
		response_json["data"] = {
			"id": payload["user_id"],
			"name": payload["name"],
			"email": payload["email"],
			"username": payload["username"],
            "selfie": payload["selfie"]
		}

	return response_json


# 登出帳號
# 使用 JWT 機制 不需要設置登出路由 從前端刪除token即可

# 註冊帳號
@app.post("/api/user")
async def enroll_account(user_info: user_info):

    from tools import db

    response_json = {}

    # 確認是否已註冊
    try:

        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)

        if user_info.name == '' or user_info.username == '' or user_info.password == '' or user_info.email == '':

            error_message = "請輸入使用者名稱、密碼、姓名、電子信箱"
            response_json['error'] = True
            response_json['message'] = error_message

            return response_json

        else:

            query = '''SELECT * FROM members WHERE username = %s;'''
            username = (user_info.username,)
            Cursor.execute(query, username)
            
            if Cursor.fetchone():

                error_message = "帳號已經被註冊"
                response_json['error'] = True
                response_json['message'] = error_message

                return response_json
            
            else:

                query = '''INSERT INTO members (name, username, password, email) VALUES (%s, %s, %s, %s);'''
                encoded_password = encode_password(user_info.password)
                apply_form = (user_info.name, user_info.username, encoded_password, user_info.email)
                Cursor.execute(query, apply_form)
                con.commit()

                response_json['ok'] = True

                return response_json

    except Exception as e:

        raise CustomHTTPException(status_code=500, detail=str(e))

    finally:

        Cursor.close()
        con.close()


# 更改資訊、大頭貼  *記得修不更新大頭照的狀況 *第一次以後的更新大頭照要把本來的圖檔刪掉
@app.put("/api/member")
#async def edit_member_info(name: str = Form(""),  email: str = Form(""), file: Optional[UploadFile] = File(None), payload: dict = Depends(login_required)):
async def edit_member_info(member_update_info: member_update_info, payload: dict = Depends(login_required)):
	
    import re
    import uuid
    from tools import update_selfie_s3, update_member_info_rds

    result_json = {}

    ## check img file
    # PNG: image/png
    # JPEG: image/jpeg
    # GIF: image/gif
    # BMP: image/bmp
    # WebP: image/webp

    if member_update_info.file:

        ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"]
        if member_update_info.file.content_type not in ALLOWED_IMAGE_TYPES:

            result_json['error'] = True
            result_json['message'] = '請提供正確的圖檔形式檔案'

            return result_json
        
        img_input = await member_update_info.file.read()
        if 'default_selfie' not in payload['selfie']:
            s3_selfie_id_url = payload['selfie']
            uuid_pattern = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

            # 搜尋並提取符合的部分
            match = re.search(uuid_pattern, s3_selfie_id_url)
            if match:
                s3_selfie_id = match.group()
            
        else:  # 本來的大頭照要刪掉
            aws_settings = os.getenv('AWS_CLOUDFRONT_DOMAIN')
            s3_selfie_id = str(uuid.uuid4())
            s3_selfie_id_url = f'https://{aws_settings}/member_selfie/' + s3_selfie_id

        #print(s3_selfie_id)    

        name = member_update_info.name
        email = member_update_info.email

        if name == '':
            name = payload['name']

        if email == '':
            email = payload['email']

        member_data = {'name': name, 'username': payload['username'], 'email': email, 'selfie': s3_selfie_id_url}
        
        if update_selfie_s3(s3_selfie_id, img_input, member_update_info.file.content_type) and update_member_info_rds(member_data):
            
            result_json['ok'] = True
            result_json['member_update'] = {'name': name, 'selfie': s3_selfie_id_url}
            
            return result_json
            
        else:
            
            result_json['error'] = True
            result_json['message'] = '資訊更新失敗'
            
            return result_json
	
    else:
         
        s3_selfie_id_url = payload['selfie']
        name = member_update_info.name or payload['name']
        email = member_update_info.email or payload['email']

        # 更新用户信息
        member_data = {'name': name, 'username': payload['username'], 'email': email, 'selfie': s3_selfie_id_url}

        if update_member_info_rds(member_data):
            result_json['ok'] = True
            result_json['member_update'] = {'name': name, 'selfie': s3_selfie_id_url}
            return result_json
        else:
            result_json['error'] = True
            result_json['message'] = '資訊更新失敗'
            return result_json
        

##########################
# 會員文章收藏 NoSQL version (Dynamodb)
@app.get("/api/collect")
#async def get_previous_collection(member_id: int, page: int = Query(1)):
async def get_previous_collection(payload: dict = Depends(login_required)):
	
    from tools import db, get_all_collection_member

    result_json = {}  

    collect_articles = get_all_collection_member(payload['user_id'])
    

    # 無收藏文章紀錄
    if collect_articles == []:
         
         result_json['data'] = None

         return result_json
    
    # 有收藏文章紀錄
    else:

        article_ids = [item['article_id']['S'] for item in collect_articles]

        try:
            if article_ids != []:
                # get article info from rds
                con = db.get_connection()
                Cursor = con.cursor(dictionary=True)
                format_strings = ','.join(['%s'] * len(article_ids))
                sql_query = f'''SELECT a.id, c.category, a.title, r.resource, DATE(a.date) AS date, a.url, a.wordcloud 
                                FROM articles AS a
                                LEFT JOIN resource AS r
                                ON a.resource_id = r.id
                                LEFT JOIN category AS c
                                ON a.category_id = c.id
                                WHERE a.id IN ({format_strings})
                                ORDER BY date DESC;'''
                
                Cursor.execute(sql_query, tuple(article_ids))
                
                articles_info = Cursor.fetchall()
            
                result_json['data'] = articles_info

            else:
                
                result_json['data'] = None
            
            return result_json
        
        except Exception as e:

            raise CustomHTTPException(status_code=500, detail=str(e))

        finally:
            
            con.close()
            Cursor.close()

		

# collect article
@app.post("/api/collect")
async def insert_collection(collect_info: collect_info):
	
    from tools import insert_into_dynamodb

    result_json = {}  

    timestamp = int(datetime.now().timestamp())
    data_for_dynamodb = {'member_id': collect_info.memberId,
                         'article_id': collect_info.articleId,
                         'collect_date': timestamp}
	
    result = insert_into_dynamodb(data_for_dynamodb)
	
    if result:
		
        result_json['ok'] = True
        return result_json
	
    else:
		
        result_json['error'] = True
        return result_json
		

# delete article collection
@app.delete("/api/collect")
async def delete_collection(collect_info: collect_info):
	
    from tools import delete_from_dynamodb

    result_json = {}
	
    result = delete_from_dynamodb(collect_info)
	
    if result:
		
        result_json['ok'] = True
        return result_json
	
    else:
		
        result_json['error'] = True
        return result_json
    

if __name__ == '__main__':
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
	#uvicorn.run("app:app", port=8000, reload=True)
     
    
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

