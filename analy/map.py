from flask import Flask , render_template , jsonify
import mysql.connector
from collections import Counter
import time

from mysql.connector import cursor
from flask import Blueprint

map_app = Blueprint('map_app', __name__)

# MySQL配置
db_config = {
    'host' : 'localhost' ,
    'user' : 'root' ,
    'password' : 'admin' ,
    'database' : 'travel'
}


# 连接到数据库的函数
def get_db_connection() :
    connection = mysql.connector.connect(**db_config)
    return connection


# 获取所有的景区数据
def get_all_attractions() :
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT word, url, lat, lon, districtName, commentCount, commentScore FROM attractions")
    attractions = cursor.fetchall()
    cursor.close()
    connection.close()
    return attractions


# 获取每个districtName的唯一景区数量
def get_district_statistics(attractions) :
    # 使用字典按区县统计，避免重复的景区名(word)计入
    district_count = {}
    for attraction in attractions :
        district = attraction[ 'districtName' ]
        word = attraction[ 'word' ]
        if district not in district_count :
            district_count[ district ] = set()
        district_count[ district ].add(word)  # 使用set避免重复的景区名
    # 计算每个district的景区数量（去重后的数量）
    return {district : len(words) for district , words in district_count.items()}


# 获取评论数最高的5个景区
def get_top_commentCount(attractions) :
    sorted_attractions = sorted(attractions , key=lambda x : x[ 'commentCount' ] , reverse=True)
    return sorted_attractions[ :5 ]



# 获取评分最高的5个景区
def get_top_commentScore(attractions) :
    sorted_attractions = sorted(attractions , key=lambda x : x[ 'commentScore' ] , reverse=True)
    return sorted_attractions[ :5 ]


@map_app.route('/map')
def map() :
    # 获取景区数据
    attractions = get_all_attractions()

    # 去重
    unique_attractions = {attraction[ 'word' ] : attraction for attraction in attractions}.values()

    # 获取district统计数据
    district_count = get_district_statistics(unique_attractions)

    # 获取评论数和评分最高的景区
    top_commentCount = get_top_commentCount(unique_attractions)
    top_commentScore = get_top_commentScore(unique_attractions)

    # 获取区县坐标
    geo_coord_map = {attraction[ 'districtName' ] : [ attraction[ 'lon' ] , attraction[ 'lat' ] ] for attraction in
                     unique_attractions}

    # 整理数据以便前端使用
    district_data = [
        {"name" : district , "value" : count} for district , count in district_count.items()
        if district in geo_coord_map  # 确保只处理有坐标的区县
    ]

    # 获取最多景区的六个区县
    top_districts = sorted(district_count.items() , key=lambda x : x[ 1 ] , reverse=True)[ :6 ]

    return render_template(
        'index.html' ,
        district_data=district_data ,
        geo_coord_map=geo_coord_map ,
        top_commentCount=top_commentCount ,
        top_commentScore=top_commentScore ,
        top_districts=top_districts)


@map_app.route('/get_attractions/<district_name>', methods=['GET'])
def get_attractions(district_name):
    # 获取指定区县的所有景区名称、经纬度
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT word, lat, lon
        FROM attractions
        WHERE districtName = %s
    """, (district_name,))
    attractions = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(attractions)


