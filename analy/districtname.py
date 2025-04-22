from flask import Flask , render_template , request , jsonify
import mysql.connector
from mysql.connector import Error
from flask import Blueprint

districtname_app = Blueprint('districtname_app', __name__)

# MySQL 配置信息
db_config = {
    'host' : 'localhost' ,
    'user' : 'root' ,
    'password' : 'admin' ,
    'database' : 'travel'
}


# 获取数据库连接
def get_db_connection() :
    connection = mysql.connector.connect(**db_config)
    return connection


# 获取所有地区的名称
def get_all_districts() :
    try :
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT districtName FROM attractions")
        districts = cursor.fetchall()
        return [ district[ 0 ] for district in districts ]
    except Error as e :
        print(f"Error fetching districts: {e}")
        return [ ]
    finally :
        if connection.is_connected() :
            cursor.close()
            connection.close()


# 获取某个地区的景点数据（包括评分和评论数量）
def get_attractions_data(district) :
    try :
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT word, commentCount, commentScore 
        FROM attractions 
        WHERE districtName = %s
        """
        cursor.execute(query , (district ,))
        return cursor.fetchall()
    except Error as e :
        print(f"Error fetching attractions data: {e}")
        return [ ]
    finally :
        if connection.is_connected() :
            cursor.close()
            connection.close()


@districtname_app.route('/districtname')
def index() :
    # 获取所有的 districtName 用于下拉框选择
    districts = get_all_districts()
    return render_template('districtname.html' , districts=districts)


@districtname_app.route('/get_data' , methods=[ 'GET' ])
def get_data() :
    # 获取前端传来的选择地区
    district = request.args.get('district')

    # 获取该地区的景点数据
    attractions_data = get_attractions_data(district)

    # 提取数据：景点名称、评论数量、评论评分
    names = [ item[ 'word' ] for item in attractions_data ]
    comment_counts = [ item[ 'commentCount' ] for item in attractions_data ]
    comment_scores = [ item[ 'commentScore' ] for item in attractions_data ]

    # 将数据返回给前端
    return jsonify(
        {
            'names' : names ,
            'commentCounts' : comment_counts ,
            'commentScores' : comment_scores
        })


