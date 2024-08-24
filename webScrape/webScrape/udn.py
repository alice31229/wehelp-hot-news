
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from tools import generate_image_upload_s3, get_summary_of_article, insert_into_articles, clean_content

import os
from dotenv import load_dotenv

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../config/.env')
load_dotenv(dotenv_path)


def get_udn(scroll_time):

    opt = webdriver.ChromeOptions()
    opt.chrome_executable_path='./chromedriver'
    opt.add_argument('disable-infobars')
    opt.add_argument("--disable-extensions")
    opt.add_argument("--start-maximized")
    opt.add_argument('--user-agent=%s' % os.getenv('USER_AGENT'))

    driver = webdriver.Chrome(options=opt)
    driver.get('https://udn.com/rank/pv/2')

    #scroll_time = int(input('請輸入想要捲動幾次'))

    link = [] # 文章連結
    #view = [] # 觀看數
    title = [] # 文章標題
    date = [] # 日期
    forum = [] # 文章類別

    for now_time in range(1, scroll_time+1):

        if driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__text']//h2")!=[]:
            #time.sleep(1)
            titles = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__text']//h2")
            hrefs = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__text']//h2//a")
            #views = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__info']//span[@class = 'story-list__view']")
            times = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__info']//time[@class = 'story-list__time']")
            category = driver.find_elements(By.XPATH, "//section[@class='story-list__holder--append']//div[@class='story-list__info']//a[@class = 'story-list__cate btn btn-blue']")

            
            for i in range(len(titles)):
                title.append(titles[i].text)
                link.append(hrefs[i].get_attribute('href'))
                #view.append(views[i].text)
                date.append(times[i].text)
                forum.append(category[i].text)

            js = "window.scrollTo(0, document.body.scrollHeight);"
            driver.execute_script(js)
            #time.sleep(2)

        else:

            #time.sleep(1)
            titles = driver.find_elements(By.XPATH, "//div[@class='story-list__text']//h2")
            hrefs = driver.find_elements(By.XPATH, "//div[@class='story-list__text']//h2//a")
            #views = driver.find_elements(By.XPATH, "//div[@class='story-list__info']//span[@class = 'story-list__view']")
            times = driver.find_elements(By.XPATH, "//div[@class='story-list__info']//time[@class = 'story-list__time']")
            category = driver.find_elements(By.XPATH, "//div[@class='story-list__info']//a[@class = 'story-list__cate btn btn-blue']")

            
            for i in range(len(titles)):
                title.append(titles[i].text)
                link.append(hrefs[i].get_attribute('href'))
                #view.append(views[i].text)
                date.append(times[i].text)
                forum.append(category[i].text)


            js = "window.scrollTo(0, document.body.scrollHeight);"
            driver.execute_script(js)
            #time.sleep(2)
    
    content = []
    for url in link:
        driver.get(url)
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

    final['日期'] = pd.to_datetime(final['日期'], format='%Y-%m-%d %H:%M', errors='coerce')

    yesterday = datetime.now() - timedelta(days=1)
    final = final[final['日期']==yesterday]
    
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

        print('udn \Y/')

    else:

        print('udn error...')

    #return final

get_udn(3)