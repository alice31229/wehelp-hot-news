#匯入套件
from bs4 import BeautifulSoup

# 操作 browser 的 API
from selenium import webdriver

# 強制等待 (執行期間休息一下)
from time import sleep
from datetime import datetime, timedelta
import pandas as pd
from tools import generate_image_upload_s3, get_summary_of_article, insert_into_articles, clean_content

import os
from dotenv import load_dotenv

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../../config/.env')
load_dotenv(dotenv_path)


def get_storm():

    storm_url = "https://www.storm.mg/articles/"
    
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
    options.chrome_executable_path='./chromedriver'
    driver = webdriver.Chrome(options=options)

    forum = []
    title = []
    date = []
    url = []
    content = []

    page = 1
    while True:
    #for i in range(pages):
        # base_url = storm_url+str(i+1)
        base_url = storm_url+str(page)
        driver.get(base_url)
        sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        elements = soup.find_all("div", {"class": "category_card card_thumbs_left"})

        stop_scraping = False
    
        for element in elements:

            time = element.find("span", {'class': 'info_time'}).getText().strip()

            time = time[:10]
            date_judge = datetime.strptime(time, '%Y-%m-%d').date()
            #today = datetime.now().date()
            yesterday = (datetime.now() - timedelta(days=1)).date()
            #yesterday = yesterday.strftime('%Y-%m-%d')
            
            if date_judge == yesterday:
            #if date_judge == today:

                date.append(time)

                t = element.find('h3').getText().strip()
                title.append(t)
                
                category = element.find('div', {'class': 'tags_wrapper'}).getText().strip()
                category = category.replace('\n', ' ')
                forum.append(category)
                website = element.find('a')['href']
                url.append(website)

                driver.get(website)
                sleep(5)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                ps = soup.find_all('p', attrs={'aid': True})

                txt = ''
                for p in ps:
                    txt+=p.text

                clean_txt = clean_content(txt)

                content.append(clean_txt)

            else:
                stop_scraping = True
                break

        if stop_scraping:
            break
        else:
            page+=1


            
    driver.quit()

    final = pd.DataFrame()
    final['文章類別'] = forum
    final['文章標題'] = title
    final['文章內容'] = content
    final['文章來源'] = '風傳媒'
    final['日期'] = date
    final['文章網址'] = url

    final['日期'] = pd.to_datetime(final['日期'], format='%Y-%m-%d', errors='coerce')
    final['日期'] = final['日期'].dt.strftime('%Y-%m-%d')
    print(final['日期'].unique())

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    print(yesterday)
    final = final[final['日期']==yesterday]

    final.to_csv(f'storm-test_{yesterday}.csv', index=False)

    return final

    # wordcloud operations
    wordcloud = []
    network = []
    overview = []
    for i in range(final.shape[0]):

        s3_uuid_wc, s3_uuid_nw = generate_image_upload_s3(final['文章標題'][i], final['文章內容'][i])
        wordcloud.append(s3_uuid_wc)
        network.append(s3_uuid_nw)
        summary = get_summary_of_article(final['文章標題'][i], final['文章內容'][i])
        overview.append(summary)

    final['文字雲'] = wordcloud
    final['關係圖'] = network
    final['文章摘要'] = overview

    if insert_into_articles(final):

        print('Storm \Y/')

    else:

        print('Storm error...')
    
    #return final

get_storm()