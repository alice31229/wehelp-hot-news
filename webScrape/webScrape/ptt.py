import os
from dotenv import load_dotenv

import time
import pandas as pd
# import threading # when there is need to return variable 


# webCrawl
from bs4 import BeautifulSoup

from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from tools import generate_image_upload_s3, get_summary_of_article, insert_into_articles

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../config/.env')
load_dotenv(dotenv_path)


def get_pttbrain(pages):

    options = Options()
    options.add_argument('disable-infobars')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--incognito")
    options.add_argument("--disable-plugins-discovery")
    options.add_argument("--start-maximized")
    options.add_argument(f'user-agent={os.getenv("USER_AGENT")}')
    options.add_argument('cookie=over18=1')
    options.chrome_executable_path = './chromedriver'
    driver = webdriver.Chrome(options=options)
    
    # 打開目標網頁
    ptt_url = os.getenv("PTT_URL")
    driver.get(ptt_url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    forum = []
    title = []
    content = []
    url = []
    date = []
    
    cnt = 1
    while cnt <= pages:
        
        if cnt > 1:

            soup = BeautifulSoup(driver.page_source, "html.parser")
    
        
        div_section = soup.find_all('div', class_='ui attached segment')[0]


        a_section = div_section.find_all('a', href=True)

        for article in a_section:

            #print(article)

            url.append(ptt_url[:-1]+article.get('href'))
            #print(article.get('href'), article.find('div', class_="ui teal small label").getText().strip(), article.find('div', {'class': 'header'}).getText().strip(), article.find('div', {'class': 'description'}).getText().strip())
            forum.append(article.find('div', class_="ui teal small label").getText().strip())

            title.append(article.find('div', {'class': 'header'}).getText().strip())
            #print(article.find('div', {'class': 'description'}).getText().strip())
            date.append(article.find('div', {'class': 'description'}).getText().strip())
            
        cnt+=1
        next_page = driver.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/div/div[3]/div/div[2]/a[13]')
        next_page.click()
        time.sleep(5)
        
    
    for u in url:
        
        driver.get(u)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        h2 = soup.find('h2')
        target_div = h2.find_next_sibling()

        content.append(target_div.text)


    driver.quit()

    final = pd.DataFrame()
    final['文章類別'] = forum
    final['文章標題'] = title
    final['文章內容'] = content
    final['文章來源'] = 'PTT'
    final['日期'] = date
    final['文章網址'] = url

    final['日期'] = pd.to_datetime(final['日期'], format='%Y-%m-%d', errors='coerce')

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

        print('ptt \Y/')

    else:

        print('ptt error...')

    #return final

get_pttbrain(5)


########################
# title
# def article_title_link(scrolls, keywords):

#     date = []
#     title = []
#     url = []
#     forum = []
    
#     # 每滑到底多增10筆文章
#     pttURL = f'{url}search?platform=ptt&q={keywords}'

#     driver.get(pttURL)
#     time.sleep(np.random.randint(5, 20))

#     number = 1

#     while number<=scrolls:
        
#         driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
#         time.sleep(np.random.randint(5, 20))
#         number+=1

#     articles_urls = driver.find_elements(By.CLASS_NAME,'summary')
#     forums = driver.find_elements(By.CSS_SELECTOR,'.ui.teal.small.label')
    
#     for a in articles_urls:
#         date.append(a.find_element(By.CLASS_NAME, 'date').text)
#         title.append(a.find_element(By.TAG_NAME,'span').text)
#         url.append(a.find_element(By.TAG_NAME,'a').get_attribute('href'))
        
#     for f in forums:
#         forum.append(f.text)
    
#     articles_df = pd.DataFrame({
#         'date':date,
#         'forum':forum,
#         'title':title,
#         'articleURL':url
#     }) 
    
#     articles_df['date'] = pd.to_datetime(articles_df['date'])
    
#     # 一週內 文章
#     end_date = pd.Timestamp(datetime.now().date())
#     start_date = end_date - timedelta(days=7)

#     # 日期篩選文章
#     articles_df = articles_df[(articles_df['date'] >= start_date) & (articles_df['date'] <= end_date)]
    
#     driver.close()
    
#     return articles_df


# # comment
# def get_comments():
    
#     date = []
#     topic = []
#     floor = []
#     person = []
#     comment = []
#     forum = []
#     url = []

#     target_articles = article_title_link(1, '薪資')
    
#     for ind in range(len(target_articles['title'])):
        
#         driver.get(target_articles['articleURL'][ind])
#         time.sleep(np.random.randint(7, 20))
        
#         comments = driver.find_elements(By.CLASS_NAME, 'comment')
        
#         for c in comments:
#             spans = c.find_elements(By.TAG_NAME, 'span')
#             author = c.find_element(By.CLASS_NAME, 'author')
            
#             date.append(target_articles['date'][ind])
#             topic.append(target_articles['title'][ind])
#             forum.append(target_articles['forum'][ind])
#             url.append(target_articles['articleURL'][ind])
            
#             floor.append(spans[0].text)
#             person.append(author.text)
#             comment.append(spans[1].text)

#     comments_df = pd.DataFrame({'日期':date, '文章標題':topic, '版面':forum, '樓數':floor,
#                                '留言人':person, '留言':comment, '文章網址':url})
    
#     comments_df['文章來源'] = 'ptt'
    
#     # comments cleaning
#     comments_df['留言'] = comments_df['留言'].str.replace(r'(https?://\S+)|\n', '', regex=True)
#     pattern = re.compile(r'[^\w\s!@#$%^&*()_+\-=\[\]{};\'\\:"|<,./<>?`~]')
#     comments_df['留言'] = comments_df['留言'].apply(lambda x: re.sub(pattern, '', x))
#     comments_df = comments_df[comments_df['留言'] != '']
#     comments_df = comments_df.drop_duplicates()
    
#     driver.close()

#     if insert_into_articles(comments_df):

#         print('ptt \Y/')

#     else:

#         print('ptt error...')
                
#     #return comments_df


# # content
# def get_contents():

#     date = []
#     forum = []
#     topic = []
#     content = []
#     url = []

#     target_articles = article_title_link(1, '薪資')
    
#     for ind in range(len(target_articles['title'])):
        
#         driver.get(target_articles['articleURL'][ind])
#         time.sleep(np.random.randint(7, 20))
        
#         contents = driver.find_elements(By.TAG_NAME, 'p')
            
#         #topic.append(target_articles['title'][ind])
        
#         content_txt = ''
#         for c in contents:
#             if '\n' not in c.text:
#                 content_txt+=c.text
#             else:
#                 content_txt+=c.text.replace('\n','')
                
#         print(content_txt)
        
#         date.append(target_articles['date'][ind])
#         topic.append(target_articles['title'][ind])
#         forum.append(target_articles['forum'][ind])
#         url.append(target_articles['articleURL'][ind])
        
#         content.append(content_txt)

#     #print(len(date), len(topic), len(forum), len(content))
#     contents_df = pd.DataFrame({'日期':date, '文章標題':topic, '版面':forum, 
#                                 '文章內容':content, '文章網址':url})
    
#     contents_df['文章來源'] = 'ptt'
    
#     # comments cleaning
#     contents_df['文章內容'] = contents_df['文章內容'].str.replace(r'(https?://\S+)|\n', '', regex=True)
#     contents_df['文章內容'] = contents_df['文章內容'].str.replace(r'原文連結/ptt/article/M\.\d+\.\w+\.\w+', '', regex=True)
#     pattern = re.compile(r'[^\w\s!@#$%^&*()_+\-=\[\]{};\'\\:"|<,./<>?`~]')
#     contents_df['文章內容'] = contents_df['文章內容'].apply(lambda x: re.sub(pattern, '', x))
#     contents_df = contents_df[contents_df['文章內容'] != '']
#     contents_df = contents_df.drop_duplicates()
    
#     driver.close()

#     # df 欄位順序調整符合加入資料庫函式
#     contents_df = contents_df[['文章標題', '文章內容', '文章來源', '日期', '文章網址']]

#     if insert_into_articles(contents_df):

#         print('ptt \Y/')

#     else:

#         print('ptt error...')
                
#     #return contents_df
