import os, time
from dotenv import load_dotenv

import pandas as pd
from datetime import datetime, timedelta
# import threading # when there is need to return variable 

# webCrawl
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tools import clean_content, get_webdriver_settings, get_random_sleep_time

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path)


def get_pttbrain(pages=20):

    driver = get_webdriver_settings()
    
    # 打開目標網頁
    ptt_url = os.getenv("PTT_URL")
    driver.get(ptt_url)
    sleep_time = get_random_sleep_time()
    time.sleep(sleep_time)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    forum = []
    title = []
    content = []
    url = []
    date = []
    
    cnt = 1
    while cnt <= pages: # while True?
        
        if cnt > 1:

            soup = BeautifulSoup(driver.page_source, "html.parser")
    
        
        div_section = soup.find_all('div', class_='ui attached segment')[0]
        a_section = div_section.find_all('a', href=True)


        for article in a_section:

            target_date = article.find('div', {'class': 'description'}).getText().strip()
            #today = datetime.now().strftime('%Y-%m-%d')
            yesterday = datetime.now() - timedelta(days=1)
            #yesterday = datetime.now()
            yesterday = yesterday.strftime('%Y-%m-%d')

            if target_date == yesterday: # 只抓目標日期的資訊

                url.append(ptt_url[:-1]+article.get('href'))
                #print(article.get('href'), article.find('div', class_="ui teal small label").getText().strip(), article.find('div', {'class': 'header'}).getText().strip(), article.find('div', {'class': 'description'}).getText().strip())
                forum.append(article.find('div', class_="ui teal small label").getText().strip())

                title.append(article.find('div', {'class': 'header'}).getText().strip())
                #print(article.find('div', {'class': 'description'}).getText().strip())
                date.append(article.find('div', {'class': 'description'}).getText().strip())


        cnt+=1
        next_page = driver.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/div/div[3]/div/div[2]/a[13]')
        next_page.click()
        sleep_time = get_random_sleep_time()
        time.sleep(sleep_time)
        
    
    for u in url:
        
        driver.get(u)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='__next']/div[2]/div[2]/div[1]/div/div/p"))
        )

        sleep_time = get_random_sleep_time()
        time.sleep(sleep_time)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        h2 = soup.find('h2')
        try:
            target_div = h2.find_next_sibling()
        except:
            target_div = ''

        #print(target_div.text)
        clean_target = clean_content(target_div.text)

        content.append(clean_target)


    driver.quit()

    final = pd.DataFrame()
    final['文章類別'] = forum
    final['文章標題'] = title
    final['文章內容'] = content
    final['文章來源'] = 'PTT'
    final['日期'] = date
    final['文章網址'] = url

    final['日期'] = pd.to_datetime(final['日期'], format='%Y-%m-%d', errors='coerce')
    final['日期'] = final['日期'].dt.strftime('%Y-%m-%d')
    #print(final['日期'].unique())

    final.to_csv(f'./data_ETL/after_webscrape/ptt-test_{yesterday}.csv', index=False)
    
    print('ptt done')
    
get_pttbrain()
