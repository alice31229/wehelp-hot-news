import os
import re
import json
import uuid
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta

import boto3
import mysql.connector

import jieba
import jieba.analyse
from wordcloud import WordCloud
import io
from collections import Counter

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), '../../config/.env')
load_dotenv(dotenv_path)

# db config
# local mysql settings
def get_db():

    db = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="sql_pool",
            host=os.getenv('MYSQL_HOST'), 
            user=os.getenv('MYSQL_USER'), 
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv("MYSQL_DB")
        )
    
    return db

# aws rds mysql settings
# def get_db():

#     db_rds = mysql.connector.pooling.MySQLConnectionPool(
#                 pool_name = "sql_pool",
#                 host=os.getenv("AWS_RDS_HOSTNAME"),
#                 user=os.getenv("AWS_RDS_USER"),
#                 password=os.getenv("AWS_RDS_PASSWORD"),
#                 database=os.getenv("AWS_RDS_DB")
#             )
    
#     return db_rds

# 定義一個函數來處理空格
def clean_spaces(text):
    # 使用正則表達式將多個空格替換為單一空格
    return re.sub(r'\s+', ' ', text.strip())

def delete_s3_wc_nw_imgs():

    db = get_db()

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        
        query_wordcloud_network_delete = '''SELECT wordcloud, network FROM articlesDelete;'''

        Cursor.execute(query_wordcloud_network_delete)
        wordcloud_network_result = Cursor.fetchall()

        df = pd.DataFrame(wordcloud_network_result)

        #print(df)


        # AWS S3 settings
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        s3 = session.client('s3')

        # S3 bucket & photo id
        bucket_name = os.getenv('AWS_BUCKET_NAME')

        for ind in range(df.shape[0]):

            wc = df['wordcloud'][ind][48:]
            nw = df['network'][ind][46:]

            s3_object_key_wc = f'wordcloud/{wc}'
            s3_object_key_nw = f'network/{nw}'

            
            # delete photo from S3
            s3.delete_object(Bucket=bucket_name, Key=s3_object_key_wc)
            s3.delete_object(Bucket=bucket_name, Key=s3_object_key_nw)
            
            print(str(ind) + ' done')

        #delete_articlesDelete_data = '''TRUNCATE TABLE articlesDelete;'''


    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")
        

    finally:
        con.close()
        Cursor.close()


def delete_by_article_id_with_scan(article_ids):

    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    table_name = os.getenv("AWS_DYNAMODB") 
    table = dynamodb.Table(table_name)

    try:
        
        response = table.scan()
        items = response['Items']

        # 遍历扫描结果并删除
        for item in items:
            
            article_id = item['article_id']
            if article_id not in article_ids:
                member_id = item['member_id']
                # 删除指定记录
                table.delete_item(
                    Key = {
                        'member_id': member_id,
                        'article_id': article_id
                    }
                )
                print(f"Deleted record with member_id: {member_id}, article_id: {article_id}")

    except Exception as e:
        print(f"Error deleting records: {e}")


def delete_collect_records_week_ago():

    db = get_db()

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        
        collect_articles_delete = '''SELECT id FROM articles;'''

        Cursor.execute(collect_articles_delete)
        delete_list_result = Cursor.fetchall()

        df = pd.DataFrame(delete_list_result)
        df['id'] = df['id'].astype(str)

        check_ids = set(df['id'])


        delete_by_article_id_with_scan(check_ids)


        return True


    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")
        

    finally:

        con.close()
        Cursor.close()


# delete unnecessary data from articles and hotKeywords 7 days ago part
def delete_week_ago_data():

    '''
    1. insert into articlesDelete from articles for s3 images handles
    2. delete articles and hotKeywords data 7 days ago
    3. s3 images of wordcloud and network deletion
    4. delete collect data for those articles 7 days ago 
    5. delete data from articlesDelete
    '''

    db = get_db()

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)

        insert_sql = '''INSERT INTO articlesDelete
                        SELECT *
                        FROM articles
                        WHERE date(date) < CURDATE() - INTERVAL 7 DAY;'''
        
        Cursor.execute(insert_sql)
        con.commit()
        print('get 7 days ago data')
        
        delete_articles_sql = '''DELETE FROM articles
                                 WHERE DATE(date) < CURDATE() - INTERVAL 7 DAY;'''
        Cursor.execute(delete_articles_sql)
        con.commit()
        print('delete 7 days ago articles')
        
        delete_hot_keywords_sql = '''DELETE FROM hotKeywords
                                     WHERE DATE(hot_kwd_date) < CURDATE() - INTERVAL 7 DAY;'''
        Cursor.execute(delete_hot_keywords_sql)
        con.commit()
        print('delete 7 days ago hot keywords')
        
        #query_wordcloud_network_delete = '''SELECT wordcloud, network FROM articlesDelete;'''
        delete_s3_wc_nw_imgs()
        print('delete 7 days agor wordcloud and network imgs')

        delete_collect_records_week_ago()
        print('delete 7 days ago articles collected records')

        delete_articlesDelete_data = '''TRUNCATE TABLE articlesDelete;'''
        Cursor.execute(delete_articlesDelete_data)
        con.commit()
        print('clear articlesDelete records')


    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")
        

    finally:
        con.close()
        Cursor.close()


# article content clean
def clean_content(content):
    '''
    清理文章內容，去除網址
    '''
    url_pattern = r'https?://[^\s]+'
    result_content = re.sub(url_pattern, '', content)
    result_content = result_content.replace('原文連結', '')

    return result_content

# unique forum column
def unify_forum_category():
    '''
    use previous unified forum to unify new webscrape articles forums:
    new articles 
    -> openai new category 
    -> update category table 
    '''

    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate

    db = get_db()

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)

        # 查詢過往已統一的類別
        prev_forum_query = '''SELECT category FROM category;'''
        Cursor.execute(prev_forum_query)
        prev_forum_result = Cursor.fetchall()

        # read csv of ptt, udn, storm, businesstoday
        yesterday = datetime.now() - timedelta(days=1)
        yesterday = yesterday.strftime('%Y-%m-%d')
        all = pd.read_csv(f'./data_ETL/wordcloud_network_overview/all_{yesterday}.csv', usecols=['文章類別'])

        new_forum_result = all['文章類別'].unique()

        chat_model = ChatOpenAI(model_name="gpt-4o", temperature=0.7)

        # 創建 PromptTemplate
        prompt_template = PromptTemplate(
            input_variables=["prev_forum_result", "new_forum_result"],
            template="""
            請根據提供的先前文章類別來對新的文章類別進行歸類。若發現現有類別不適合，可以創建新的類別，
            我希望得到一個dictionary，其中key是先前文章類別，不要更動值，例如'八卦 ( Gossiping )'請保留完整'八卦 ( Gossiping )'，'風生活 國內  台北 時事話題'就是'風生活 國內  台北 時事話題'，value是歸類後的文章類別，其中歸類後的文章類別不要出現英文。
            像是 {{'風生活 國內 理財 時事話題': '生活', '風生活 財經': '財經', '八卦 ( Gossiping )': '八卦', 'NBA ( NBA )': '運動'}}。
            不用解釋整理過程，我只需要整理結果即可。
            先前文章類別: {prev_forum_result}
            新的文章類別: {new_forum_result}
            """
        )

        # 創建 LLMChain
        summary_chain = prompt_template | chat_model

        input_data = {
            "prev_forum_result": prev_forum_result,
            "new_forum_result": new_forum_result
        }

        # 文章類別生成鏈
        forum_unify = summary_chain.invoke(input_data)
        forum_unify = forum_unify.content
        forum_unify = forum_unify.replace('python', '')
        forum_unify = forum_unify.replace('\n', '')
        forum_unify = forum_unify.replace("'", '"')

        start = forum_unify.find('{')
        end = forum_unify.find('}') + 1

        json_str = forum_unify[start:end]
        json_str = json_str.replace(r'\n', '')
        forum_dict = json.loads(json_str)

        #print(forum_dict)

        # new category unique
        unique_forum_value = set(forum_dict.values())

        # update category table with new unified result
        #format_strings = ','.join(['%s'] * len(unique_forum_value))
        category_values = ', '.join(["('{}')".format(category) for category in unique_forum_value])
        #sql_query = f"SELECT id, forum, title, resource, date, url, wordcloud FROM articles WHERE id IN ({format_strings})"
        
        # ignore -> will not insert into those already exist category previously in the category table
        update_category = f'''INSERT IGNORE INTO category (category)
                              VALUES {category_values}'''
        Cursor.execute(update_category)
        con.commit()

        return forum_dict


    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")

    finally:
        con.close()
        Cursor.close()


def unify_forum_to_db():
    '''
    -> mapping original to new
    -> update articles table with category_id
    -> insert into articles with new data and unified category_id
    '''

    forum_mapping_dict = unify_forum_category()
    for k,v in forum_mapping_dict.items():
        print(k, ':',v)
        print('##############')

    db = get_db()

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)

        # category id 
        sql = 'SELECT id, category FROM category;'
        Cursor.execute(sql)
        category_id_mapping = Cursor.fetchall()

        category_id_mapping_df = pd.DataFrame(category_id_mapping)

        # resource id remember
        sql = 'SELECT id AS resource_id, resource FROM resource;'
        Cursor.execute(sql)
        resource_id_mapping = Cursor.fetchall()

        resource_id_mapping_df = pd.DataFrame(resource_id_mapping)

        # new articles load here
        yesterday = datetime.now() - timedelta(days=1)
        yesterday = yesterday.strftime('%Y-%m-%d')
        new_df = pd.read_csv(f'./data_ETL/wordcloud_network_overview/all_{yesterday}.csv')

        new_df['統一文章類別'] = new_df['文章類別'].map(forum_mapping_dict) 
        new_df.to_csv('category-test.csv', index=False)

        new_df.loc[new_df['文章類別'] == '風生活  娛樂 影視', '統一文章類別'] = '生活'
        new_df.loc[new_df['文章類別'] == '風生活 房地產  台北 房市', '統一文章類別'] = '房地產'

        final_df = new_df.merge(category_id_mapping_df, left_on='統一文章類別', right_on='category', how='left')
        final_df = final_df.merge(resource_id_mapping_df, left_on='文章來源', right_on='resource', how='left')

        #final_df.to_csv('category-check-20240912.csv', index=False)

        # rename column names

        final_df = final_df[['id','文章類別','文章標題','文章內容','resource_id','日期','文章網址','文字雲','關係圖','文章摘要']]
        final_df = final_df.rename(columns={'id': '文章類別編號', 'resource_id': '文章來源編號'})

        #print(final_df['文章類別編號'].unique())
        #print(final_df[final_df['文章類別編號'].isna()], final_df.shape, final_df[final_df['文章類別編號'].isna()].shape)

        final_df['文章類別編號'] = final_df['文章類別編號'].astype(int)

        final_df.to_csv(f'./data_ETL/ready_for_db/all_{yesterday}.csv', index=False)

        print('new articles to db done')
    

    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")

    finally:
        con.close()
        Cursor.close()


# local mysql insert test
def insert_into_articles():

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    df = pd.read_csv(f'./data_ETL/ready_for_db/all_{yesterday}.csv')

    db = get_db()
    
    try:
        # 建立插入語句  update current columns
        sql = '''INSERT INTO articlesLand.articles (category_id, forum, title, content, resource_id, date, url, wordcloud, network, overview) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'''

        # 執行插入操作
        con = db.get_connection()

        with con.cursor(dictionary=True) as cursor:
            for row in df.itertuples(index=False):
                cursor.execute(sql, row)
            con.commit()


        return True

    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")

        return False
    
    finally:

        con.close()
        cursor.close()


def generate_hot_keywords():

    '''
    after saving articles data into db
    generate hot keywords from it
    '''

    try:

        db = get_db()

        hot_kwds_sql = '''SELECT title, content, resource_id
                          FROM articles
                          WHERE DATE(date) = CURDATE() - INTERVAL 1 DAY;'''
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        Cursor.execute(hot_kwds_sql)
        yesterday_words = Cursor.fetchall()
        articles_df = pd.DataFrame(yesterday_words)

        resource_type_sql = '''SELECT * FROM resource;'''
        Cursor.execute(resource_type_sql)
        resource_type = Cursor.fetchall()
        resource_type_df = pd.DataFrame(resource_type)

        # nx2 -> nx1
        articles_df['combined_text'] = articles_df.apply(lambda x: ' '.join([x['title'], x['content']]), axis=1)

        # load stop words
        STOP_ch2 = []
        with open("./stop_words_ch_filer.txt", 'r', encoding='utf-8') as f:
            for line in f:
                STOP_ch2.append(line.strip())

        stop2 = pd.DataFrame()
        stop2['stop_word'] = STOP_ch2

        stop_txt = []
        with open('./stopwords.txt', 'r', encoding='utf-8') as f:
            for line in f:
                stop_txt.append(line.strip())


        combine_stop = STOP_ch2 + stop_txt

        resource_lst = [i for i in articles_df['resource_id'].unique()]
        resource_lst = resource_lst.append(5)

        final_lst = []

        # each resource and overall 
        for r in resource_type_df['id'].unique():

            if r != 5:
                target_df = articles_df[articles_df['resource_id']==r]
            else:
                target_df = articles_df

            # nx1 -> 1
            all_text = ' '.join(target_df['combined_text'])
        

            #result_string = title + content

            jieba.set_dictionary('./dict.txt.big.txt')

            titleTxt_jb1 = jieba.lcut(all_text)

            # 篩選出長度大於1且不在停用詞列表中的詞彙
            titleTxt_jb1 = [word for word in titleTxt_jb1 if len(word) > 1 and word not in combine_stop]

            # 生成詞頻字典
            word_freq = Counter(titleTxt_jb1)

            # 將 Counter 轉換為 list of tuples，方便排序
            word_freq_list = word_freq.most_common()
            # word_freq_list 現在是一個 list，每個元素是一個 tuple (word, count)，按照 count 降序排列


            for ind in range(len(word_freq_list[:10])):

                final_lst.append({'resource_id': int(r), 'keyword': word_freq_list[ind][0], 'hot_rank': int(ind+1)})
        
        # for r in final_lst:
        #     print(r)

        yesterday = datetime.now() - timedelta(days=1)
        yesterday = yesterday.strftime('%Y-%m-%d')

        # save to hotKeywords
        # 準備 SQL 插入語句
        sql = "INSERT INTO hotKeywords (resource_id, keyword, hot_rank, hot_kwd_date) VALUES (%s, %s, %s, %s)"

        # 批量插入
        values = [(item['resource_id'], item['keyword'], item['hot_rank'], yesterday) for item in final_lst]
        Cursor.executemany(sql, values)

        con.commit()
    
    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")

        return False
    
    finally:

        con.close()
        Cursor.close()


######################################

def create_relationship_graph(word_freq, top_n=10):

    import networkx as nx
    from itertools import combinations

    G = nx.Graph()

    # 只保留最高频的词汇进行关系图构建
    most_common_words = [word for word, freq in word_freq.most_common(top_n)]

    for word in most_common_words:
        G.add_node(word, label=word)

    token_pairs = combinations(most_common_words, 2)

    for word1, word2 in token_pairs:
        G.add_edge(word1, word2, weight=word_freq[word1] + word_freq[word2])

    return G


def save_relationship_graph(G):
    """
    Return the relationship graph with byteIO type.

    Args:
        G (nx.Graph): The networkx graph object.
    """
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm


    font_path = '/System/Library/Fonts/Hiragino Sans GB.ttc'
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()

    plt.figure(figsize=(5.5, 4))
    pos = nx.spring_layout(G)
    
    # Extract weights and normalize them for better visual effect
    weights = nx.get_edge_attributes(G, 'weight')
    max_weight = max(weights.values()) if weights else 1
    edge_widths = [3 * weights.get(edge, 0) / max_weight for edge in G.edges]

    # Normalize edge weights for color mapping
    norm = plt.Normalize(vmin=min(weights.values()), vmax=max(weights.values()))
    cmap = plt.cm.YlOrBr  # Choose a color map (e.g., Blues, Reds, Greens) yellow -> orange -> brown

    nx.draw_networkx_nodes(G, pos, node_size=888, node_color='orange', alpha=0.6)

    # Draw edges with color mapping based on weights
    for edge, width in zip(G.edges, edge_widths):
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=[edge],
            width=width,
            alpha=0.5,
            edge_color=[cmap(norm(weights[edge]))]
        )

    labels = {node: node for node in G.nodes()}  # Create labels using node names
    nx.draw_networkx_labels(
        G, 
        pos, 
        labels=labels, 
        font_family=font_prop.get_name(), 
        font_size=10
    )

    plt.axis('off')
    # plt.savefig(file_name, format='png')
    img_data = io.BytesIO()
    plt.savefig(img_data, format='PNG')
    plt.close()

    # Seek to the beginning of the BytesIO object
    img_data.seek(0)

    return img_data


#######
# openai summary part
def get_summary_of_article(title, content):
    '''
    generate summary from openai by giving article title and content
    '''

    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate

    chat_model = ChatOpenAI(model_name="gpt-4o", temperature=0.7)

    # 創建 PromptTemplate
    prompt_template = PromptTemplate(
        input_variables=["title", "content"],
        template="""
        請為以下文章生成一段300字以內的繁體中文摘要。不需要特別註明'摘要：'、'文章摘要：'跟'標題：'、'文章標題：'，不用解釋整理過程，我只需要整理結果即可。
        範例：
        輸入：[問卦] 鏡週刊一早又出了N篇獨家 喊到千萬了 看了一下  那個偵查全公開代言人鏡週刊一早出了N篇獨家  除了原本700萬 又多喊了逾千萬不明再加上什麼質詢影片  便簽等所以一定知情的消息都從這裡跑出來鏡週刊真的什麼都知道欸  偵查全公開有沒有八卦--原文連結
        輸出：鏡週刊一早又發佈了多篇獨家報導，內容包括原本的700萬事件，現在又額外增加了超過千萬的不明款項，並且還包含了質詢影片和便簽等資訊。這些消息讓人覺得鏡週刊彷彿什麼都知道，讓偵查全公開的情況更加明顯。讀者不禁懷疑鏡週刊是否有內幕消息，對此討論也引發了更多八卦。
        。
        文章標題: {title}
        文章内容: {content}

        """
    )

    # 創建 LLMChain
    summary_chain = prompt_template | chat_model

    input_data = {
        "title": title,
        "content": content
    }

    # 摘要生成鏈
    overview = summary_chain.invoke(input_data)

    return overview.content


def generate_image_upload_s3(title, content):
    '''
    使用文章標題、內文來繪製文字雲、關係圖
    並將繪製的圖存儲至S3
    再將存儲至S3的圖檔名稱回傳
    '''

    STOP_ch2 = []
    with open("./stop_words_ch_filer.txt", 'r', encoding='utf-8') as f:
        for line in f:
            STOP_ch2.append(line.strip())

    stop2 = pd.DataFrame()
    stop2['stop_word'] = STOP_ch2

    stop_txt = []
    with open('./stopwords.txt', 'r', encoding='utf-8') as f:
        for line in f:
            stop_txt.append(line.strip())


    combine_stop = STOP_ch2 + stop_txt

    result_string = title + content

    jieba.set_dictionary('./dict.txt.big.txt')
    #titleTxt_jb1 = jieba.cut_for_search(result_string)

    titleTxt_jb1 = jieba.lcut(result_string)

    # 篩選出長度大於1且不在停用詞列表中的詞彙
    titleTxt_jb1 = [word for word in titleTxt_jb1 if len(word) > 1 and word not in combine_stop]

    # 生成詞頻字典
    word_freq = Counter(titleTxt_jb1)

    # generate wordcloud
    wc = WordCloud(
        background_color='white',
        width=550,
        height=400, 
        font_path="/System/Library/Fonts/Hiragino Sans GB.ttc",
        prefer_horizontal=1.0, 
        stopwords=combine_stop
    ).generate_from_frequencies(word_freq)

    
    # 存地端
    #wc.to_file('wordcloud-testF.png')
    

    ########S3 part##########
    # Create a BytesIO object to store the image data
    img_data_wc = io.BytesIO()
    
    relationshipG = create_relationship_graph(word_freq)
    #print('G', relationshipG)
    img_data_nw = save_relationship_graph(relationshipG)

    # # Save the WordCloud to the BytesIO object as a PNG
    wc.to_image().save(img_data_wc, format='PNG')

    # # Seek to the beginning of the BytesIO object
    img_data_wc.seek(0)

    
    # # AWS S3 settings
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    s3 = session.client('s3')

    # S3 bucket & photo id
    bucket_name = os.getenv('AWS_BUCKET_NAME')
    uni_name_wc = uuid.uuid4()
    uni_name_nw = uuid.uuid4()

    s3_object_key_wc = f'wordcloud/{uni_name_wc}'
    s3_object_key_nw = f'network/{uni_name_nw}'
    
    # upload photo to S3
    s3.put_object(Bucket=bucket_name, Key=s3_object_key_wc, Body=img_data_wc, ContentType='image/png')
    s3.put_object(Bucket=bucket_name, Key=s3_object_key_nw, Body=img_data_nw, ContentType='image/png')

    print('done')

    cloudfront = os.getenv('AWS_CLOUDFRONT_DOMAIN')

    return f"https://{cloudfront}/wordcloud/" + str(uni_name_wc), f"https://{cloudfront}/network/" + str(uni_name_nw)


def handle_wordcloud_network_overview():

    # new articles load here
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    ptt = pd.read_csv(f'./data_ETL/after_webscrape/ptt-test_{yesterday}.csv')
    storm = pd.read_csv(f'./data_ETL/after_webscrape/storm-test_{yesterday}.csv')
    udn = pd.read_csv(f'./data_ETL/after_webscrape/udn-test_{yesterday}.csv')
    businesstoday = pd.read_csv(f'./data_ETL/after_webscrape/businesstoday-test_{yesterday}.csv')

    df = pd.concat([ptt, storm, udn, businesstoday], ignore_index=True)
    df = df[df['文章內容'].notnull()]

    # wordcloud operations
    wordcloud = []
    network = []
    overview = []
    for index, row in df.iterrows():
        title = row['文章標題']
        content = row['文章內容']

        content = content.replace('closeAdvertisementstaiwanese_weather [webstory]-20240909-23:00CANCELNEXT VIDEOplay_arrowvolume_mutePausePlay% buffered00:0000:0000:42UnmuteMutePlayPowered by GliaStudio', '')

        s3_uuid_wc, s3_uuid_nw = generate_image_upload_s3(title, content)
        wordcloud.append(s3_uuid_wc)
        network.append(s3_uuid_nw)
        summary = get_summary_of_article(title, content)
        overview.append(summary)


    df['文字雲'] = wordcloud
    df['關係圖'] = network
    df['文章摘要'] = overview

    df.to_csv(f'./data_ETL/wordcloud_network_overview/all_{yesterday}.csv', index=False)

    print('wordcloud_network_overview done')

