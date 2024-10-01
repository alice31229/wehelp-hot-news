
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tools import clean_content, get_webdriver_settings, get_random_sleep_time

import os, time
from dotenv import load_dotenv

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path)


def get_udn(scroll_time=3):

    driver = get_webdriver_settings()
    driver.get(os.getenv('UDN_URL'))

    link = [] # 文章連結
    #view = [] # 觀看數
    title = [] # 文章標題
    date = [] # 日期
    forum = [] # 文章類別

    for current_scroll_time in range(1, scroll_time+1):

        if driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__text']//h2")!=[]:
            #time.sleep(1)

            titles = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__text']//h2")
            hrefs = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__text']//h2//a")
            #views = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__info']//span[@class = 'story-list__view']")
            times = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__info']//time[@class = 'story-list__time']")
            category = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__info']//a[@class = 'story-list__cate btn btn-blue']")

            
            for i in range(len(titles)):

                time_judge = times[i].text[:10]
                yesterday = datetime.now() - timedelta(days=1)
                #yesterday = datetime.now()
                yesterday = yesterday.strftime('%Y-%m-%d')
                
                if time_judge == yesterday:

                    title.append(titles[i].text)
                    link.append(hrefs[i].get_attribute('href'))
                    #view.append(views[i].text)
                    date.append(time_judge)
                    forum.append(category[i].text)

            js = "window.scrollTo(0, document.body.scrollHeight);"
            driver.execute_script(js)
            time.sleep(get_random_sleep_time())

        else:

            #time.sleep(1)
            titles = driver.find_elements(By.XPATH, "//div[@class='story-list__text']//h2")
            hrefs = driver.find_elements(By.XPATH, "//div[@class='story-list__text']//h2//a")
            #views = driver.find_elements(By.XPATH, "//div[@class='story-list__info']//span[@class = 'story-list__view']")
            times = driver.find_elements(By.XPATH, "//div[@class='story-list__info']//time[@class = 'story-list__time']")
            category = driver.find_elements(By.XPATH, "//div[@class='story-list__info']//a[@class = 'story-list__cate btn btn-blue']")

            
            for i in range(len(titles)):

                time_judge = times[i].text[:10]
                yesterday = datetime.now() - timedelta(days=1)
                #yesterday = datetime.now()
                yesterday = yesterday.strftime('%Y-%m-%d')
                
                if time_judge == yesterday:

                    title.append(titles[i].text)
                    link.append(hrefs[i].get_attribute('href'))
                    #view.append(views[i].text)
                    date.append(time_judge)
                    forum.append(category[i].text)


            js = "window.scrollTo(0, document.body.scrollHeight);"
            driver.execute_script(js)
            time.sleep(get_random_sleep_time())
    
    content = []
    for url in link:
        driver.get(url)

        # WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.XPATH, '/html/body/main/div/section[2]/section/article/div/section[1]'))
        # )

        time.sleep(get_random_sleep_time())

        soup = BeautifulSoup(driver.page_source, "html.parser")
        section = soup.find("section", {'class': 'article-content__editor'})
        content_ps = section.find_all('p')

        txt = ''
        for p in content_ps:
            if p.text != '&nbsp;' and p.text != '':
                txt+=p.text

        clean_txt = clean_content(txt)

        content.append(clean_txt)
    
    driver.quit()
    
    # 調整欄位順序順應資料庫資料表
    final = pd.DataFrame()
    final['文章類別'] = forum
    final['文章標題'] = title
    final['文章內容'] = content
    final['文章來源'] = '聯合新聞網'
    final['日期'] = date
    final['文章網址'] = link

    # make sure the date format at webpage
    final['日期'] = pd.to_datetime(final['日期'], format='%Y-%m-%d', errors='coerce')
    final['日期'] = final['日期'].dt.strftime('%Y-%m-%d')
    #print(final['日期'].unique())

    final = final.drop_duplicates()

    final.to_csv(f'./data_ETL/after_webscrape/udn-test_{yesterday}.csv', index=False)
    print('udn done')

get_udn()