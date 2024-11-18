#匯入套件
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tools import clean_content, get_webdriver_settings, get_random_sleep_time

import os, time, re
from dotenv import load_dotenv

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path)

def get_ebc(scroll_time=3):

    ebc_url = os.getenv('EBC_URL')
    
    driver = get_webdriver_settings()
    driver.get(ebc_url)

    link = [] # 文章連結
    title = [] # 文章標題
    date = [] # 日期
    forum = [] # 文章類別
    content = [] # 文章內容

    link_pre = [] # 文章列表的文章連結 尚未判定日期

    yesterday = datetime.now() - timedelta(days=1)
    #yesterday = datetime.now()
    yesterday = yesterday.strftime('%Y-%m-%d')

    # 先抓到目標文章url
    for current_scroll_time in range(1, scroll_time+1):

        js = "window.scrollTo(0, document.body.scrollHeight);"
        driver.execute_script(js)
        sleep_time = get_random_sleep_time()
        time.sleep(sleep_time)

    # WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div[2]/div/div/div[1]/div[3]/div[2]/div[2]/div/div[1]'))
    # )

    # 開始抓文章連結  //section[@class='story-list__holder--append']//div[@class='story-list__text']//h2
    article_urls = driver.find_elements(By.XPATH, "//main[@id='main']//div[@class='tab_content']//div[@class='list m_group']//a")
    #print(len(article_urls))
    
    for article_url in article_urls:

        target_article = article_url.get_attribute('href')
        #print(target_article)
        link_pre.append(target_article)
        # need to save the urls first for avoiding "stale element reference: stale element not found"

    for target_article in link_pre:

        driver.get(target_article)

        # WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.XPATH, '/html/body/main/div/section[2]/section/article/div/section[1]'))
        # )

        sleep_time = get_random_sleep_time()
        time.sleep(sleep_time)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        article_title = soup.find("div", {'class': 'article_header'}).find('h1').text
        article_kind = soup.find("div", {'class': 'breadcrumb'}).text.replace('首頁','')
        article_date = soup.find('div', {'class': 'article_date'}).text
        article_ps = soup.find('div', {'class': 'article_content'}).find_all('p')
        
        total_txt = ''
        for p in article_ps:
            if '➤' not in p.text: # 廣告
                article_content = p.text.replace('/n', '')
                cleaned_article_content = re.sub(r"（圖／.*?）", "", article_content)
                total_txt += cleaned_article_content

        # print('title', article_title)
        # print('kind', article_kind)
        # print('date', article_date)
        # print('content', total_txt)

        if article_date == yesterday:
            title.append(article_title)
            date.append(article_date)
            forum.append(article_kind)
            content.append(total_txt)
            link.append(target_article)
    
    driver.quit()
    
    # 調整欄位順序順應資料庫資料表
    final = pd.DataFrame()
    final['文章類別'] = forum
    final['文章標題'] = title
    final['文章內容'] = content
    final['文章來源'] = '東森新聞'
    final['日期'] = date
    final['文章網址'] = link

    # make sure the date format at webpage
    final['日期'] = pd.to_datetime(final['日期'], format='%Y-%m-%d', errors='coerce')
    final['日期'] = final['日期'].dt.strftime('%Y-%m-%d')
    #print(final['日期'].unique())

    final = final.drop_duplicates()

    final.to_csv(f'./data_ETL/after_webscrape/ebc-test_{yesterday}.csv', index=False)
    print('ebc done')


if __name__ == '__main__':
    
    get_ebc()