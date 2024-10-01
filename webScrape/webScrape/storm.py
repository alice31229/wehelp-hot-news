#匯入套件
from bs4 import BeautifulSoup

from datetime import datetime, timedelta
import pandas as pd
from tools import clean_content, clean_spaces, get_webdriver_settings, get_random_sleep_time

import os, time
from dotenv import load_dotenv

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path)


def get_storm(pages=3):

    storm_url = os.getenv('STORM_URL')
    
    driver = get_webdriver_settings()

    forum = []
    title = []
    date = []
    url = []
    content = []

    # page = 1
    # while True:
    for i in range(pages):
        base_url = storm_url+str(i+1)
        #base_url = storm_url+str(page)
        driver.get(base_url)
        time.sleep(get_random_sleep_time())
        soup = BeautifulSoup(driver.page_source, "html.parser")
        elements = soup.find_all("div", {"class": "category_card card_thumbs_left"})

        # stop_scraping = False
    
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
                time.sleep(get_random_sleep_time())
                soup = BeautifulSoup(driver.page_source, "html.parser")
                ps = soup.find_all('p', attrs={'aid': True})

                txt = ''
                for p in ps:
                    txt+=p.text

                clean_txt = clean_content(txt)

                content.append(clean_txt)

            else:
                # stop_scraping = True
                # break
                pass

        # if stop_scraping:
        #     break
        # else:
        #     page+=1
        

            
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
    #print(final['日期'].unique())

    final = final[final['日期']!=''] # 排除非會員點擊顯示的行銷文章頁面

    final['文章類別'] = final['文章類別'].apply(clean_spaces)

    final.to_csv(f'./data_ETL/after_webscrape/storm-test_{yesterday}.csv', index=False)
    #final.to_csv(f'./data_ETL/after_webscrape/storm-test_{today}.csv', index=False)
    print('storm done')

get_storm()