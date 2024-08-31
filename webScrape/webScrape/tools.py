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
db = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="sql_pool",
    host=os.getenv('MYSQL_HOST'), # in same ec2 use localhost; otherwise, use the endpoint
    user=os.getenv('MYSQL_USER'), 
    password=os.getenv('MYSQL_PASSWORD'),
	database=os.getenv("MYSQL_DB"))

# aws rds mysql settings
# db_rds = mysql.connector.pooling.MySQLConnectionPool(
#         pool_name = "sql_pool",
#         host=os.getenv("AWS_RDS_HOSTNAME"),
#         user=os.getenv("AWS_RDS_USER"),
#         password=os.getenv("AWS_RDS_PASSWORD"),
#         database="messagePhoto")

# article content clean
def clean_content(content):
    '''
    清理文章內容，去除網址
    '''
    url_pattern = r'https?://[^\s]+'
    result_content = re.sub(url_pattern, '', content)

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

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)

        # 查詢過往已統一的類別
        prev_forum_query = '''SELECT category FROM category;'''
        # '''SELECT DISTINCT forum 
        #     FROM articles 
        #     WHERE DATE(date) != CURDATE() - INTERVAL 1 DAY;'''
        Cursor.execute(prev_forum_query)
        prev_forum_result = Cursor.fetchall()

        # 新文章尚未統一的類別
        # new_forum_query = '''SELECT DISTINCT forum 
        #                      FROM articles 
        #                      WHERE DATE(date) = CURDATE() - INTERVAL 1 DAY;'''
        # Cursor.execute(new_forum_query)
        # new_forum_result = Cursor.fetchall()

        # read csv of ptt, udn, storm, businesstoday
        yesterday = datetime.now() - timedelta(days=1)
        yesterday = yesterday.strftime('%Y-%m-%d')
        ptt = pd.read_csv(f'ptt-test_{yesterday}.csv', usecols=['文章類別'])
        storm = pd.read_csv(f'storm-test_{yesterday}.csv', usecols=['文章類別'])
        udn = pd.read_csv(f'udn-test_{yesterday}.csv', usecols=['文章類別'])
        businesstoday = pd.read_csv(f'businesstoday-test_{yesterday}.csv', usecols=['文章類別'])

        new_forum_result = list(ptt['文章類別'].unique()) + list(storm['文章類別'].unique()) + list(udn['文章類別'].unique()) + list(businesstoday['文章類別'].unique())

        ###

        chat_model = ChatOpenAI(model_name="gpt-4o", temperature=0.7)

        # 創建 PromptTemplate
        prompt_template = PromptTemplate(
            input_variables=["prev_forum_result", "new_forum_result"],
            template="""
            請根據提供的先前文章類別來對新的文章類別進行歸類。
            我希望得到一個dictionary，其中key是歸類後的文章類別，value是先前的文章類別，且統一的類別不要出現英文。
            像是 風生活 國內 理財 時事話題 對應 生活
            風生活 財經 對應 財經...。
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

        ###

    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")
        return False

    finally:
        con.close()
        Cursor.close()


def unify_forum_to_db(new_df):
    '''
    -> mapping original to new
    -> update articles table with category_id
    -> insert into articles with new data and unified category_id
    '''

    forum_mapping_dict = unify_forum_category()

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

        new_df['統一文章類別'] = new_df['文章類別'].map(forum_mapping_dict) 
        final_df = new_df.merge(category_id_mapping_df, left_on='統一文章類別', right_on='category', how='left')
        final_df = final_df.merge(resource_id_mapping_df, left_on='文章來源', right_on='resource', how='left')

        # rename column names

        final_df = final_df[['id','文章類別','文章標題','文章內容','resource_id','日期','文章網址','文字雲','關係圖','文章摘要']]
        final_df = final_df.rename(columns={'id': '文章類別編號', 'resource_id': '文章來源編號'})

        return final_df
    

    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")
        return False

    finally:
        con.close()
        Cursor.close()




# local mysql insert test
def insert_into_articles(df):

    #data = list(df.to_records(index=False))
    
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
        # 可以打印 DataFrame 的前幾行，查看資料
        #print([:3])
        # 可以打印 SQL 語句，檢查語法
        #print(sql)

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

        hot_kwds_sql = '''SELECT title, content, resource
                          FROM articles AS a
                          INNER JOIN resource AS r
                          ON a.resource_id = r.id
                          WHERE DATE(date) = CURDATE() - INTERVAL 1 DAY;'''
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)
        Cursor.execute(hot_kwds_sql)
        yesterday_words = Cursor.fetchall()
        articles_df = pd.DataFrame(yesterday_words)

        # nx2 -> nx1
        articles_df['combined_text'] = articles_df.apply(lambda x: ' '.join([x['title'], x['content']]), axis=1)

        # nx1 -> 1
        all_text = ' '.join(articles_df['combined_text'])

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

        #result_string = title + content

        jieba.set_dictionary('./dict.txt.big.txt')
        #titleTxt_jb1 = jieba.cut_for_search(result_string)

        titleTxt_jb1 = jieba.lcut(all_text)

        # 篩選出長度大於1且不在停用詞列表中的詞彙
        titleTxt_jb1 = [word for word in titleTxt_jb1 if len(word) > 1 and word not in combine_stop]

        # 生成詞頻字典
        word_freq = Counter(titleTxt_jb1)

        # 將 Counter 轉換為 list of tuples，方便排序
        word_freq_list = word_freq.most_common()
        # word_freq_list 現在是一個 list，每個元素是一個 tuple (word, count)，按照 count 降序排列



        return 
    
    except mysql.connector.Error as e:

        print(f"An error occurred: {str(e)}")

        return False
    
    finally:

        con.close()
        Cursor.close()



# each resource and overall category calculation
sql_each_resource = '''SELECT resource, category, COUNT(*) AS cnt
                        FROM articles AS a
                        LEFT JOIN category AS c
                        ON a.category_id = c.id
                        LEFT JOIN resource AS r
                        ON a.resource_id = r.id
                        GROUP BY resource, category
                        ORDER BY resource, category'''

sql_overall_category = '''SELECT category, COUNT(*) AS cnt
                            FROM articles AS a
                            LEFT JOIN category AS c
                            ON a.category_id = c.id
                            GROUP BY category
                            '''



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
        font_size=10#, 
        #bbox=dict(facecolor='#FFFFE0', edgecolor='none', boxstyle='round,pad=0.3')  # Light yellow background
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
        請為以下文章生成一段300字以內的繁體中文摘要。
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
    # print('摘要')
    # print(overview.content)
    # print('原文')
    # print(content)


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
