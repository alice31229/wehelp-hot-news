#匯入套件
from bs4 import BeautifulSoup

# 操作 browser 的 API
from selenium import webdriver

# 強制等待 (執行期間休息一下)
from time import sleep
from datetime import datetime, timedelta
import pandas as pd
from tools import clean_content

import os
from dotenv import load_dotenv

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../../config/.env')
load_dotenv(dotenv_path)

def get_businesstoday(pages=5):

    # selenium settings
    options = webdriver.ChromeOptions()
    options.add_argument('--user-agent=%s' % os.getenv('USER_AGENT'))
    options.add_argument('disable-infobars')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--incognito")
    options.add_argument("--disable-plugins-discovery")
    options.add_argument("--start-maximized")
    options.add_argument(f'user-agent={os.getenv("USER_AGENT")}')
    options.chrome_executable_path='./chromedriver'
    driver = webdriver.Chrome(options=options)

    title = []
    date = []
    url = []
    content = []
    forum = []

    for i in range(pages):
        base_url = str("https://www.businesstoday.com.tw/hot/"+str(i+1))
        driver.get(base_url)
        sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        elements = soup.find_all("a", {"class": "article__item"})
        #elements = soup.find_all("div", {"class": "article__itembox"})
    
        for element in elements:

            #if 'businesstoday' in element['href']: # 過濾廣告
            time = element.find("p", {'class': 'article__item-date'}).getText().strip()[:10]
            yesterday = datetime.now() - timedelta(days=1)
            #yesterday = datetime.now()
            yesterday = yesterday.strftime('%Y-%m-%d')
            
            if time == yesterday:

                article_title = element.find("h4").getText().strip()
                title.append(article_title)
                
                date.append(time)
                website = element['href']
                url.append('https://www.businesstoday.com.tw'+website)
                driver.get('https://www.businesstoday.com.tw'+website)
                sleep(3)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                category = soup.find('p',{'class': 'context__info-item context__info-item--type'}).getText().strip()
                forum.append(category)
                #print(category)
                
                target_div = soup.find('div', class_='Zi_ad_ar_iR')
                content_ps = target_div.find_all("p")
                #content_ps = ps.find_all_previous('div', id_='fb-root')

                txt = ''
                for p in content_ps:
                    
                    if p.text != '&nbsp;' and p.text != '':
                        txt+=p.text

                clean_txt = clean_content(txt)

                content.append(clean_txt)

    driver.quit()

    final = pd.DataFrame()
    final['文章類別'] = forum
    final['文章標題'] = title
    final['文章內容'] = content
    final['文章來源'] = '今周刊'
    final['日期'] = date
    final['文章網址'] = url

    final['日期'] = pd.to_datetime(final['日期'], format='%Y-%m-%d', errors='coerce')

    final['日期'] = final['日期'].dt.strftime('%Y-%m-%d')

    # yesterday = datetime.now() - timedelta(days=1)
    # yesterday = yesterday.strftime('%Y-%m-%d')
    # final = final[final['日期']==yesterday]

    final.to_csv(f'./data_ETL/businesstoday-test_{yesterday}.csv', index=False)
    print('businesstoday done')

get_businesstoday()