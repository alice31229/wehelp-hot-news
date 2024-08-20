import os
import io
import uuid
import boto3
import pandas as pd
from dotenv import load_dotenv
from collections import Counter

# get .env under config directory
dotenv_path = os.path.join(os.path.dirname(__file__), './config/.env')
load_dotenv(dotenv_path)

# import boto3

# # 建立 DynamoDB client
# session = boto3.Session(
# aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
# aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
# region_name=os.getenv("AWS_REGION")
# )

# dynamodb = session.client('dynamodb')
# table_name = 'wehelp-collect'  

import jieba
import jieba.analyse
from wordcloud import WordCloud
import io
import matplotlib.pyplot as plt

import mysql.connector

#print(os.getenv('MYSQL_HOST'), os.getenv('MYSQL_USER'), os.getenv("MYSQL_DB"))

db = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="sql_pool",
    host=os.getenv('MYSQL_HOST'), # in same ec2 use localhost; otherwise, use the endpoint
    user=os.getenv('MYSQL_USER'), 
    password=os.getenv('MYSQL_PASSWORD'),
	database=os.getenv("MYSQL_DB"))

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
    

def get_wordcloud_relationship(title, content):
    '''
    generate wordcloud, network graph from article title and content
    '''

    STOP_ch2 = []
    with open("./webScrape/stop_words_ch_filer.txt", 'r', encoding='utf-8') as f:
        for line in f:
            STOP_ch2.append(line.strip())

    stop2 = pd.DataFrame()
    stop2['stop_word'] = STOP_ch2

    stop_txt = []
    with open('./webScrape/stopwords.txt', 'r', encoding='utf-8') as f:
        for line in f:
            stop_txt.append(line.strip())


    combine_stop = STOP_ch2 + stop_txt

    result_string = title + content

    jieba.set_dictionary('./webScrape/dict.txt.big.txt')
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
    wc.to_file('wordcloud-testF.png')
    

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

    return uni_name_wc, uni_name_nw


def get_db_article_title_content():

    try:
        con = db.get_connection()
        Cursor = con.cursor(dictionary=True)


        fetch_one = '''SELECT title, content FROM articlesLand.articles 
                    LIMIT 1;'''

        Cursor.execute(fetch_one)
        data = Cursor.fetchall()

        data_content = data[0]['content'].replace('\n', '')
        data_content = data_content.replace('\xa0', '')

        #print(data_content)

        return data[0]['title'], data_content

        #get_wordcloud(data[0]['title'], data_content)

        

    except Exception as e:

        print(e)

    finally:

        con.close()
        Cursor.close()


# t, c = get_db_article_title_content()
# get_wordcloud_relationship(t, c)

########## upload default member selfie ############
# AWS S3 settings
# session = boto3.Session(
# aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
# aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
# region_name=os.getenv("AWS_REGION")
# )
# s3 = session.client('s3')

# # S3 bucket & photo id
# bucket_name = os.getenv('AWS_BUCKET_NAME')
# uni_name = uuid.uuid4()

# s3_object_key = f'member_selfie/default_selfie'

# with open('./static/photo_icon/99899d8a-f65e-4611-9114-ca9fcd37085d.png', 'rb') as file_data:
#         # 上传到 S3
#         s3.put_object(
#             Bucket=bucket_name,
#             Key=s3_object_key,
#             Body=file_data,
#             ContentType='image/png'  # 根据文件类型设置适当的 ContentType
#         )

# # upload photo to S3
# #s3.put_object(Bucket=bucket_name, Key=s3_object_key, Body=img_data, ContentType='image/png')

# print('done')

#######
# relationship graph
# def visualize_relationship(title, content):
#     '''
#     generate network graph from article title and content
#     '''

#     import jieba
#     from sklearn.feature_extraction.text import TfidfVectorizer
#     import networkx as nx
#     import matplotlib.pyplot as plt

#     article_title, article_content = get_db_article_title_content()

# def arrange_topic_from_resource():
#     '''
#     from ptt, storm, businesstoday, udn
#     get the unique topic and transform the topic to unify different categories
#     '''




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

article_title, article_content = get_db_article_title_content()
get_summary_of_article(article_title, article_content)


