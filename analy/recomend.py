import math
from flask import Flask , render_template , request
import mysql.connector
from geopy.distance import geodesic
from flask import Blueprint

recomend_app = Blueprint('recomend_app', __name__)


# MySQL 配置信息
db_config = {
    'host' : 'localhost' ,
    'user' : 'root' ,
    'password' : 'admin' ,
    'database' : 'travel'
}


# Haversine 公式计算两点之间的距离，返回的距离单位是公里
def haversine(lat1 , lon1 , lat2 , lon2) :
    # 将角度转换为弧度
    R = 6371  # 地球半径，单位：公里
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine 公式
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a) , math.sqrt(1 - a))

    return R * c  # 返回公里数


# 获取 MySQL 数据库中的景点数据
def get_nearby_attractions(user_lat , user_lon , max_distance_km=15) :
    try :
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查询数据库中的所有景点
        cursor.execute(
            """
            SELECT word, url, lat, lon, districtName, commentCount, commentScore,address
            FROM attractions
        """)
        attractions = cursor.fetchall()

        # 筛选出距离用户位置 15 公里内的景点
        nearby_attractions = [ ]
        for attraction in attractions :
            attraction_lat = attraction[ 'lat' ]
            attraction_lon = attraction[ 'lon' ]

            # 计算景点与用户的距离
            distance = haversine(user_lat , user_lon , attraction_lat , attraction_lon)

            if distance <= max_distance_km :
                attraction[ 'distance' ] = distance
                nearby_attractions.append(attraction)

        return nearby_attractions

    except mysql.connector.Error as e :
        print(f"Error: {e}")
        return [ ]
    finally :
        if connection.is_connected() :
            cursor.close()
            connection.close()


# 显示景点的页面
@recomend_app.route('/recomend')
def recomend() :
    # 获取用户的位置参数（经纬度）
    user_lat = float(request.args.get('lat' , 41.7989))  # 默认
    user_lon = float(request.args.get('lon' , 123.3502))  # 默认

    # 获取附近景点
    nearby_attractions = get_nearby_attractions(user_lat , user_lon)

    # 渲染网页并显示景点信息
    return render_template('recomend.html' , attractions=nearby_attractions , user_lat=user_lat , user_lon=user_lon)



