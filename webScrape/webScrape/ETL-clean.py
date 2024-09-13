# handle articles data functions
from tools import handle_wordcloud_network_overview, unify_forum_to_db, insert_into_articles, generate_hot_keywords, delete_week_ago_data

# test outcome quality functions

####################################
# function queue
# 1. webScrape -> get_pttbrain(pages=20), get_storm(), get_businesstoday(pages=5), get_udn(scroll_time=3)
# 2. wordcloud, network, overview -> handle_wordcloud_network_overview()
# 3. unify articles category from different resource -> unify_forum_to_db()
# 4. save the clean articles data into db -> insert_into_articles()
# 5. produce hot keywords from new articles -> generate_hot_keywords()
# 6. delete those not in need data from articles and hotKeywords 7 days ago -> delete_week_ago_data()

# 2. wordcloud, network, overview
#handle_wordcloud_network_overview()

# 3. unify articles category from different resource
unify_forum_to_db()

# 4. save the clean articles data into db
insert_into_articles()

# 5. produce hot keywords from new articles
generate_hot_keywords()

# 6. delete 7 days ago related articles records
delete_week_ago_data()

####################################
# unit test for each process of data pipeline
# import pytest

# # 
# def check_web_scrape_results():
#     '''
#     each columns type and empty(nan, float) or not
#     '''
#     return True

# def check_wordcloud_network_overview():
    

#     return True

# def check_unified_category():


#     return True

# def check_data_before_db():


#     return True


####################################
# import pandas as pd

# udn = pd.read_csv('./data_ETL/after_webscrape/udn-test_2024-09-01.csv')
# udn['日期1'] = '2024-09-01'

# udn = udn[['文章類別','文章標題','文章內容','文章來源','日期1','文章網址']]
# udn = udn.rename(columns={'日期1': '日期'})

# udn.to_csv('udn-test2_2024-09-01.csv', index=False)