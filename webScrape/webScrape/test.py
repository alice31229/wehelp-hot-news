import pandas as pd
from datetime import datetime, timedelta

yesterday = datetime.now() - timedelta(days=1)
yesterday = yesterday.strftime('%Y-%m-%d')

ptt = pd.read_csv(f'./data_ETL/after_webscrape/ptt-test_{yesterday}.csv')
storm = pd.read_csv(f'./data_ETL/after_webscrape/storm-test_{yesterday}.csv')
udn = pd.read_csv(f'./data_ETL/after_webscrape/udn-test_{yesterday}.csv')
businesstoday = pd.read_csv(f'./data_ETL/after_webscrape/businesstoday-test_{yesterday}.csv')

df = pd.concat([ptt, storm, udn, businesstoday], ignore_index=True)
df = df[df['文章內容'].notnull()]


df.to_csv('clean-test.csv', index=False)