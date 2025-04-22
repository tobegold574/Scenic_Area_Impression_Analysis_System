from flask import Flask, render_template, jsonify,request
import pymysql
import pandas as pd
from datetime import datetime
from flask import Blueprint
from flask import Flask, render_template, request, redirect, url_for, jsonify

searchecharts_app = Blueprint('searchecharts_app', __name__)

# MySQL 数据库配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin',
    'database': 'travel',
    'charset': 'utf8mb4'
}

# 数据库连接函数
def get_db_connection():
    connection = pymysql.connect(**db_config)
    return connection

# 路由：主页
@searchecharts_app.route('/searchecharts')
def hotss():
    connection = get_db_connection()
    query = "SELECT DISTINCT mid FROM weibo_comments"
    df_mids = pd.read_sql(query, connection)
    connection.close()
    mids = df_mids['mid'].tolist()
    return render_template('searchechartshots.html', mids=mids)

# 路由：获取话题的情感数据
@searchecharts_app.route('/get_sentiment_datas/<mid>', methods=['GET'])
def get_sentiment_datas(mid):
    connection = get_db_connection()

    # 获取评论数据
    query = f"SELECT sentiment, sentiment_score, created_at FROM weibo_comments WHERE mid = '{mid}'"
    df = pd.read_sql(query, connection)
    connection.close()

    # 数据处理
    if df.empty:
        return jsonify({"error": "No data found for the mid."}), 404

    # 确保情感列的数据类型正确
    df['sentiment'] = df['sentiment'].astype(str)

    # 计算情感分类的数量
    sentiment_counts = df['sentiment'].value_counts()

    # 将 created_at 列转换为 datetime 类型
    df['created_at'] = pd.to_datetime(df['created_at'])

    # 按小时分组，计算情感得分的平均值
    hourly_sentiment = df.groupby([pd.Grouper(key='created_at', freq='H'), 'sentiment']).agg({'sentiment_score': 'mean'}).unstack(fill_value=0)
    hourly_sentiment.columns = hourly_sentiment.columns.droplevel(0)  # Drop the first level of the multi-index
    hourly_sentiment.reset_index(inplace=True)

    # 转换为字典格式
    sentiment_counts_dict = sentiment_counts.to_dict()
    hourly_sentiment_dict = hourly_sentiment.to_dict(orient='records')

    return jsonify({
        "sentiment_counts": sentiment_counts_dict,
        "hourly_sentiment": hourly_sentiment_dict
    })


# 新的路由：获取性别相关情感数据
@searchecharts_app.route('/get_gender_sentiment_datas/<mid>')
def get_gender_sentiment_datas(mid):
    connection = get_db_connection()
    query = """
        SELECT gender, sentiment, created_at, sentiment_score
        FROM weibo_comments
        WHERE mid = %s
    """
    df = pd.read_sql(query, connection, params=[mid])
    connection.close()

    # 计算男女情感评论数量堆叠数据
    gender_sentiment_counts = df.groupby(['gender', 'sentiment']).size().unstack().fillna(0).to_dict(orient='index')

    # 计算男女情感评论比例饼图数据
    total_male = df[df['gender'] == 'm'].shape[0]
    total_female = df[df['gender'] == 'f'].shape[0]
    male_sentiment_counts = df[df['gender'] == 'm']['sentiment'].value_counts().to_dict()
    female_sentiment_counts = df[df['gender'] == 'f']['sentiment'].value_counts().to_dict()
    male_sentiment_percentages = {k: v / total_male * 100 for k, v in male_sentiment_counts.items()}
    female_sentiment_percentages = {k: v / total_female * 100 for k, v in female_sentiment_counts.items()}

    # 男女随时间变化的情感分数
    df['created_hour'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:00:00')
    hourly_gender_sentiment = df.groupby(['created_hour', 'gender', 'sentiment']).sentiment_score.mean().unstack().fillna(0)
    male_hourly_sentiment = hourly_gender_sentiment.xs('m', level='gender').reset_index().to_dict(orient='records')
    female_hourly_sentiment = hourly_gender_sentiment.xs('f', level='gender').reset_index().to_dict(orient='records')

    return jsonify({
        'gender_sentiment_counts': gender_sentiment_counts,
        'male_sentiment_percentages': male_sentiment_percentages,
        'female_sentiment_percentages': female_sentiment_percentages,
        'male_hourly_sentiment': male_hourly_sentiment,
        'female_hourly_sentiment': female_hourly_sentiment
    })


@searchecharts_app.route('/searchecharts/sentiment_like_analysis' , methods=[ 'GET' ])
def sentiment_like_analysis() :
    topic = request.args.get('topic')
    connection = get_db_connection()

    # 获取所有话题列表
    topics_query = "SELECT DISTINCT topic FROM weibo_comments"
    topics_df = pd.read_sql(topics_query , connection)
    topics = topics_df[ 'topic' ].tolist()

    # 获取每个情感的 like_count 和 total_number
    query = """
        SELECT like_count, total_number, sentiment
        FROM weibo_comments
        WHERE topic = %s
    """
    df = pd.read_sql(query , connection , params=(topic ,))
    connection.close()

    # 将数据转换为 JSON 格式返回
    data = df.to_dict(orient='records')

    return render_template('searchechartslike_analysis.html' , topic=topic , data=data , topics=topics)

@searchecharts_app.route('/searchecharts/wordcloud_analysis', methods=['GET', 'POST'])
def wordcloud_analysis():
    topics = []
    selected_topic = None
    data = []
    all_comments = []  # 用于存储所有评论

    # 从数据库获取话题列表
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT topic FROM weibo_comments")
        topics = [row[0] for row in cursor.fetchall()]

    # 默认选择第一个话题
    if not selected_topic and topics:
        selected_topic = topics[0]

    # 处理表单提交
    if request.method == 'POST':
        selected_topic = request.form.get('topic')

    # 如果选定话题不为空，查询相关评论
    if selected_topic:
        with get_db_connection() as connection:
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            # 获取正面、负面、中性各三条点赞数最多的评论
            cursor.execute("""
                (SELECT text, like_count, sentiment 
                 FROM weibo_comments 
                 WHERE topic = %s AND sentiment = '正面' 
                 ORDER BY like_count DESC 
                 LIMIT 3)
                UNION ALL
                (SELECT text, like_count, sentiment 
                 FROM weibo_comments 
                 WHERE topic = %s AND sentiment = '负面' 
                 ORDER BY like_count DESC 
                 LIMIT 3)
                UNION ALL
                (SELECT text, like_count, sentiment 
                 FROM weibo_comments 
                 WHERE topic = %s AND sentiment = '中性' 
                 ORDER BY like_count DESC 
                 LIMIT 3)
            """, (selected_topic, selected_topic, selected_topic))

            data = cursor.fetchall()

            # 获取所有评论
            cursor.execute("SELECT text FROM weibo_comments WHERE topic = %s", (selected_topic,))
            all_comments = [row['text'] for row in cursor.fetchall()]

    return render_template('searchechartswordcloud_analysis.html', topics=topics, selected_topic=selected_topic, data=data, all_comments=all_comments)

@searchecharts_app.route('/searchecharts/api/sentiment_distribution')
def sentiment_distributions():
    conn = get_db_connection()
    query = '''
    SELECT sentiment, COUNT(*) AS count 
    FROM weibo_comments 
    GROUP BY sentiment
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    return jsonify(df.set_index('sentiment').to_dict()['count'])


# 将日期转换为字符串格式的函数
def serialize_date(date) :
    return date.strftime("%Y-%m-%d %H:%M:%S")


@searchecharts_app.route('/searchecharts/api/time_series')
def time_seriess() :
    conn = get_db_connection()
    query = '''
    SELECT created_at, COUNT(*) AS count 
    FROM weibo_comments 
    GROUP BY created_at
    ORDER BY created_at
    '''
    df = pd.read_sql(query , conn)
    conn.close()

    # 将 datetime 转换为字符串
    df[ 'created_at' ] = df[ 'created_at' ].apply(serialize_date)

    return jsonify(df.set_index('created_at').to_dict()[ 'count' ])


@searchecharts_app.route('/searchecharts/api/gender_distribution')
def gender_distributions():
    conn = get_db_connection()
    query = '''
    SELECT gender, COUNT(*) AS count 
    FROM weibo_comments 
    GROUP BY gender
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    return jsonify(df.set_index('gender').to_dict()['count'])

@searchecharts_app.route('/searchecharts/api/user_activity')
def user_activitys():
    conn = get_db_connection()
    query = '''
    SELECT screen_name, COUNT(*) AS count 
    FROM weibo_comments 
    GROUP BY screen_name 
    ORDER BY count DESC 
    LIMIT 10
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    return jsonify(df.set_index('screen_name').to_dict()['count'])

@searchecharts_app.route('/searchecharts/api/source_distribution')
def source_distributions():
    conn = get_db_connection()
    query = '''
    SELECT source, COUNT(*) AS count 
    FROM weibo_comments 
    GROUP BY source
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    return jsonify(df.set_index('source').to_dict()['count'])

@searchecharts_app.route('/searchecharts/api/likes_comments')
def likes_commentss():
    conn = get_db_connection()
    query = '''
    SELECT like_count, total_number 
    FROM weibo_comments
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

@searchecharts_app.route('/searchechartswebs')
def searchechartswebs():
    return render_template('searchechartswebs.html')


