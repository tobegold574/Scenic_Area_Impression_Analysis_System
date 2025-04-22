from flask import Flask, render_template, request, jsonify
import pymysql
import json
from flask import Blueprint
from flask import Flask, render_template, request, redirect, url_for, jsonify

searchmap_app = Blueprint('searchmap_app', __name__)

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


@searchmap_app.route('/searchmap')
def searchmap():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT topic FROM weibo_comments")
        topics = cursor.fetchall()
    connection.close()
    return render_template('searchmap.html', topics=[topic[0] for topic in topics])


@searchmap_app.route('/get_data/search' , methods=[ 'POST' ])
def get_data() :
    selected_topic = request.json[ 'topic' ]
    connection = get_db_connection()
    with connection.cursor() as cursor :
        if selected_topic == 'all' :
            sql = """
                SELECT source, COUNT(*) AS count
                FROM weibo_comments
                GROUP BY source
            """
        else :
            sql = """
                SELECT source, COUNT(*) AS count
                FROM weibo_comments
                WHERE topic = %s
                GROUP BY source
            """
            cursor.execute(sql , (selected_topic ,))
            data = cursor.fetchall()

        # 对于“全部”选项，单独执行查询
        if selected_topic == 'all' :
            cursor.execute(sql)
            data = cursor.fetchall()

    connection.close()

    # 读取城市经纬度信息
    with open('city_coordinates.json' , 'r' , encoding='utf-8') as f :
        geoCoordMap = json.load(f)

    # 将数据转换为适合 ECharts 的格式
    result = [ ]
    for row in data :
        source , count = row  # 确保这里是正确的
        if source in geoCoordMap :
            longitude , latitude = geoCoordMap[ source ]
            result.append({'name' : source , 'value' : count , 'longitude' : longitude , 'latitude' : latitude})

    return jsonify(result)


