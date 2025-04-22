from flask import Flask , request , render_template , Blueprint
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from snownlp import SnowNLP
import pandas as pd
import mysql.connector

# 创建 Flask Blueprint
search_app = Blueprint('search_app' , __name__)

# MySQL数据库配置
db_config = {
    'host' : 'localhost' ,
    'user' : 'root' ,
    'password' : 'admin' ,
    'database' : 'travel'
}


# 创建数据库连接
def get_db_connection() :
    return mysql.connector.connect(**db_config)


# 创建表的SQL语句
create_table_sql = '''
CREATE TABLE IF NOT EXISTS weibo_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_index INT,
    topic VARCHAR(255),
    mid VARCHAR(255),
    comment_index INT,
    created_at DATETIME,
    user_id VARCHAR(255),
    text TEXT,
    source VARCHAR(255),
    screen_name VARCHAR(255),
    followers_count INT,
    statuses_count INT,
    gender VARCHAR(10),
    like_count INT,
    total_number INT,
    sentiment VARCHAR(10),
    sentiment_score FLOAT
)
'''

# 清空表的SQL语句
clear_table_sql = 'TRUNCATE TABLE weibo_comments'


# 创建表
def create_table() :
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(create_table_sql)
    connection.commit()
    cursor.close()
    connection.close()


# 初始化数据库表
create_table()


# 辅助函数：解析粉丝数
def parse_followers_count(followers_count) :
    if isinstance(followers_count , str) :
        if '万' in followers_count :
            return int(float(followers_count.replace('万' , '').strip()) * 10000)
        elif '亿' in followers_count :
            return int(float(followers_count.replace('亿' , '').strip()) * 100000000)
    return int(followers_count) if followers_count is not None else 0


# 爬虫函数
def fetch_comments(query) :
    query = requests.utils.quote(query)  # URL编码
    search_url = f"https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26t%3D10%26q%3D{query}&page_type=searchall"

    headers = {
        "accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7" ,
        "accept-encoding" : "gzip, deflate, br, zstd" ,
        "accept-language" : "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6" ,
        "cache-control" : "max-age=0" ,
        "cookie" : "_T_WM=fa9530ba7d3a7eaa7dc71e912a095dd4; SCF=AqWzPIv4mnXL4zdy4SZ59CzstoF9maDwlkUx5ZyaKCnwaKbzGZg9WpBcp5PnjdWKusQddPSCGcAs_ycZM39d0LU.; SUB=_2A25K5MtoDeRhGeFG6FUS-SrIzDSIHXVpmEKgrDV6PUJbktANLRClkW1NebcAAh3jlCDEuOMjZ3VTWoOxdyjQeT_q; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9Whrg7RFHMN_kuERDD.mhVyG5NHD95QN1heNe0.XShMRWs4Dqc_zi--ciKL8iKLhi--fi-82iK.7i--NiKLWiKnXi--ciKL8iKLhi--ciKL2iKy8i--fi-82iK.7i--NiKLWiKnXi--ciKL2iKy8; SSOLoginState=1742781240; ALF=1745373240" ,
        "priority" : "u=0, i" ,
        "referer" : "https://weibo.cn/?since_id=0&max_id=ODn079gW5&prev_page=1&page=2" ,
        "sec-ch-ua" : "\"Chromium\";v=\"130\", \"Microsoft Edge\";v=\"130\", \"Not?A_Brand\";v=\"99\"" ,
        "sec-ch-ua-mobile" : "?0" ,
        "sec-ch-ua-platform" : "\"Windows\"" ,
        "sec-fetch-dest" : "document" ,
        "sec-fetch-mode" : "navigate" ,
        "sec-fetch-site" : "same-origin" ,
        "sec-fetch-user" : "?1" ,
        "upgrade-insecure-requests" : "1" ,
        "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
    }

    results = [ ]
    new_data = False  # 标记是否有新数据

    search_response = requests.get(search_url , headers=headers)
    if search_response.status_code == 200 :
        data = search_response.json()
        if 'data' in data and 'cards' in data[ 'data' ] :
            for card in data[ 'data' ][ 'cards' ] :
                if 'mblog' in card :
                    mid = card[ 'mblog' ][ 'id' ]
                    topic = card[ 'mblog' ][ 'text' ][ :255 ]  # 截断以避免超出长度限制

                    comments_url = f"https://m.weibo.cn/comments/hotflow?id={mid}&mid={mid}&max_id_type=0"
                    comments_response = requests.get(comments_url , headers=headers)

                    if comments_response.status_code == 200 :
                        comments_data = comments_response.json()
                        if 'data' in comments_data and 'data' in comments_data[ 'data' ] :
                            for comment_index , comment in enumerate(comments_data[ 'data' ][ 'data' ] , start=1) :
                                created_at = comment.get('created_at')
                                raw_text = comment.get('text' , '')
                                cleaned_text = BeautifulSoup(raw_text , 'html.parser').get_text()
                                user_info = comment.get('user' , {})
                                user_id = user_info.get('id')
                                screen_name = user_info.get('screen_name')
                                followers_count = parse_followers_count(user_info.get('followers_count'))
                                statuses_count = user_info.get('statuses_count')
                                gender = user_info.get('gender')
                                like_count = comment.get('like_count')
                                total_number = comment.get('total_number')
                                source = comment.get('source' , '').replace('来自' , '').strip()

                                # 格式化日期
                                if created_at :
                                    created_at_dt = datetime.strptime(created_at , '%a %b %d %H:%M:%S +0800 %Y')
                                    formatted_created_at = created_at_dt.strftime('%Y-%m-%d %H:%M')

                                # 情感分析
                                if cleaned_text :
                                    sentiment = SnowNLP(cleaned_text)
                                    sentiment_score = sentiment.sentiments
                                    sentiment_label = "中性"
                                    if sentiment_score > 0.6 :
                                        sentiment_label = "正面"
                                    elif sentiment_score < 0.4 :
                                        sentiment_label = "负面"

                                    # 构建新数据行
                                    new_row = {
                                        "话题序号" : 1 ,
                                        "话题" : topic ,
                                        "mid" : mid ,
                                        "评论序号" : comment_index ,
                                        "Created At" : formatted_created_at ,
                                        "User ID" : user_id ,
                                        "Text" : cleaned_text ,
                                        "Source" : source ,
                                        "Screen Name" : screen_name ,
                                        "Followers Count" : followers_count ,
                                        "Statuses Count" : statuses_count ,
                                        "Gender" : gender ,
                                        "Like Count" : like_count ,
                                        "Total Number" : total_number ,
                                        "情感" : sentiment_label ,
                                        "情感分值" : sentiment_score
                                    }
                                    results.append(new_row)
                                    new_data = True  # 标记为有新数据

    # 只有在有新数据的情况下才清空旧数据并插入新数据
    if new_data :
        # 删除旧数据
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(clear_table_sql)
        connection.commit()

        # 插入新数据
        insert_sql = '''
        INSERT INTO weibo_comments (
            topic_index, topic, mid, comment_index, created_at, 
            user_id, text, source, screen_name, followers_count, 
            statuses_count, gender, like_count, total_number, 
            sentiment, sentiment_score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        for row in results :
            cursor.execute(
                insert_sql , (
                    row[ "话题序号" ] , row[ "话题" ] , row[ "mid" ] , row[ "评论序号" ] , row[ "Created At" ] ,
                    row[ "User ID" ] , row[ "Text" ] , row[ "Source" ] , row[ "Screen Name" ] ,
                    row[ "Followers Count" ] , row[ "Statuses Count" ] , row[ "Gender" ] ,
                    row[ "Like Count" ] , row[ "Total Number" ] , row[ "情感" ] , row[ "情感分值" ]
                ))
        connection.commit()
        cursor.close()
        connection.close()

    # 返回 DataFrame，如果没有新数据，返回空 DataFrame
    return pd.DataFrame(results) if new_data else pd.DataFrame()


# Flask 路由，用于查询页面
@search_app.route('/search' , methods=[ 'GET' , 'POST' ])
def search() :
    results = pd.DataFrame()  # 初始化一个空的 DataFrame
    if request.method == 'POST' :
        query = request.form[ 'query' ]
        results = fetch_comments(query)
        return render_template('search.html' , results=results.to_dict(orient='records') , query=query)
    return render_template('search.html' , results=results.to_dict(orient='records'))
