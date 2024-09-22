import requests, random

import os
from dotenv import load_dotenv

# get .env 
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def test_homepage_api():

    #homepage = os.getenv("HOMEPAGE_URL") 
    homepage = os.getenv("ROUTER_API_ARTICLES")
    response = requests.get(homepage, verify=False)

    homepage_status_code = response.status_code

    articles_cnt = len(response.json()['data'])

    assert homepage_status_code == 200 and articles_cnt == 12
    

def test_article_page_api():

    api_id = requests.get(os.getenv("ROUTER_API_ARTICLES"), verify=False)
    api_id = api_id.json()

    random_number = random.randint(0, len(api_id['data'])-1)
    id = api_id['data'][random_number]['id']

    article_page = os.getenv("ROUTER_API_ARTICLE") + str(id)
    
    response = requests.get(article_page, verify=False)

    status_code = response.status_code

    article = response.json()

    assert status_code == 200 and 'data' in article
