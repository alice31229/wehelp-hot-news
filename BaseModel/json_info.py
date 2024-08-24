from pydantic import BaseModel

# 符合 application/json 資料型別
# update member info
# class member_update_info(BaseModel):
#     name: str
#     email: str

# register
class user_info(BaseModel): 
	name: str
	username: str
	email: str
	password: str

# log in
class member_log_in_info(BaseModel): 
	username: str
	password: str
	
# collect / delete article
class collect_info(BaseModel):
	memberId: str
	articleId: str
	