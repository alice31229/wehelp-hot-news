from pydantic import BaseModel
from fastapi import UploadFile
from typing import List, Optional

# 符合 application/json 資料型別
# update member info
class member_update_info(BaseModel):
    name: str
    email: str
    file: UploadFile = None

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
	
class articles_requirements(BaseModel):
	keyword: Optional[str] = ''
	# resources: str
	# categories: str
	# dates: str
	page: str
	resources: list
	categories: list
	dates: list
