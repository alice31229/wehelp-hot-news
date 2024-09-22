import os
from tools import get_db
from dotenv import load_dotenv

# get .env 
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def test_articles_date():

    '''
    suppose to get 7 days articles data
    '''

    db = get_db()

    sql = '''SELECT DISTINCT DATE(date) FROM articles WHERE DATE(date) >= CURDATE() - INTERVAL 7 DAY;'''

    con = db.get_connection()
    Cursor = con.cursor(dictionary=True)

    Cursor.execute(sql)

    result = Cursor.fetchall()

    con.close()
    Cursor.close()

    assert len(result) == 7

