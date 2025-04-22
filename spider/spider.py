import requests
import json
import pandas as pd
import mysql.connector
from mysql.connector import Error
from concurrent.futures import ThreadPoolExecutor
import time

# 读取 world.json 文件，假设文件内容为您提供的格式
with open("world.json" , "r" , encoding="utf-8") as f :
    world_data = json.load(f)

# 定义基础API的URL格式
base_url = "https://m.ctrip.com/restapi/h5api/globalsearch/search?action=gsonline&source=globalonline&keyword={}&t=1731491818781"

# 创建一个 Excel Writer 对象
excel_writer = pd.ExcelWriter('city_hotspots.xlsx' , engine='openpyxl')

# MySQL 配置信息
db_config = {
    'host' : 'localhost' ,
    'user' : 'root' ,
    'password' : 'admin' ,
    'database' : 'travel'
}

# 添加 Cookie 和 User-Agent 到 Headers
headers = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0' ,
    'Cookie' : 'Hm_lvt_a8d6737197d542432f4ff4abc6e06384=1731482043; HMACCOUNT=0EE5EB04603C2C68; UBT_VID=1731482043807.d671VyeyEwXp; MKT_CKID=1731482044144.9q2hf.bd7e; GUID=09031029210048009062; _RSG=3wquAHlGHa3tbVO5MtvNdB; _RDG=285651f721be2624a629ab07c29c863750; _RGUID=391142f4-4ae3-4e83-b9d7-e7758561f977; _ga=GA1.1.45184786.1731482045; Session=smartlinkcode=U130727&smartlinklanguage=zh&SmartLinkKeyWord=&SmartLinkQuary=&SmartLinkHost=; Union=AllianceID=4902&SID=130727&OUID=&createtime=1731482045&Expires=1732086845360; MKT_Pagesource=PC; nfes_isSupportWebP=1; StartCity_Pkg=PkgStartCity=158; login_type=0; login_uid=FF3F259839B7E137A63619CAED66D465; _bfaStatusPVSend=1; ibulanguage=CN; ibulocale=zh_cn; cookiePricesDisplayed=CNY; fin_logincfg="{\"acc\":\"\",\"id\":0,\"cmyid\":0,\"logintype\":0,\"timeLimitN\":1,\"loginUserList\":null,\"cmyname\":\"\"}"; Hm_lpvt_a8d6737197d542432f4ff4abc6e06384=1731490657; _ga_9BZF483VNQ=GS1.1.1731490632.2.1.1731490661.0.0.0; _ga_5DVRDQD429=GS1.1.1731490637.2.1.1731490661.0.0.0; _ga_B77BES1Z8Z=GS1.1.1731490637.2.1.1731490661.36.0.0; _bfi=p1%3D600001375%26p2%3D600001375%26v1%3D27%26v2%3D24; _bfaStatus=send; _ubtstatus=%7B%22vid%22%3A%221731482043807.d671VyeyEwXp%22%2C%22sid%22%3A2%2C%22pvid%22%3A36%2C%22pid%22%3A600001375%7D; _RF1=2408%3A8435%3A7510%3A44e%3A59f1%3A63e7%3Ac5f7%3Af116; _jzqco=%7C%7C%7C%7C1731482045346%7C1.1720112539.1731482044149.1731499764919.1731499929492.1731499764919.1731499929492.undefined.0.0.51.51; _bfa=1.1731482043807.d671VyeyEwXp.1.1731499767039.1731499938702.3.3.290510'  # 填入有效的cookie
}


# 创建数据库和表的函数
def create_db_and_table() :
    try :
        # 连接到 MySQL
        connection = mysql.connector.connect(
            host=db_config[ 'host' ] ,
            user=db_config[ 'user' ] ,
            password=db_config[ 'password' ]
        )

        if connection.is_connected() :
            cursor = connection.cursor()

            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS travel")
            cursor.execute("USE travel")

            # 创建表格，如果表格不存在
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS attractions (
                id INT AUTO_INCREMENT PRIMARY KEY,  # 设置自增ID
                external_id INT,  # API 返回的 ID 改为 external_id
                code VARCHAR(255),
                word VARCHAR(255),
                eName VARCHAR(255),
                type VARCHAR(50),
                productId INT,
                url VARCHAR(255),
                lat FLOAT,
                lon FLOAT,
                cityId INT,
                cityName VARCHAR(255),
                districtId INT,
                districtName VARCHAR(255),
                poiId INT,
                alias VARCHAR(255),
                commentCount INT,
                commentScore FLOAT,
                recommend VARCHAR(50),
                address TEXT
            )
            """)
            connection.commit()

    except Error as e :
        print(f"Error: {e}")
    finally :
        if connection.is_connected() :
            cursor.close()
            connection.close()


# 插入数据到 MySQL
def insert_to_mysql(city_name , city_data) :
    try :
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 插入数据
        for item in city_data :
            # 打印数据，确保所有字段和参数数量一致
            print(f"Inserting data for {city_name}: {item}")

            cursor.execute(
                """
                INSERT INTO attractions (
                    external_id, code, word, eName, type, productId, url, lat, lon,
                    cityId, cityName, districtId, districtName, poiId, alias, commentCount,
                    commentScore, recommend, address
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """ , (
                    item.get('id' , 0) ,  # external_id
                    item.get('code' , '') ,
                    item.get('word' , '') ,
                    item.get('eName' , '') ,
                    item.get('type' , '') ,
                    item.get('productId' , 0) ,
                    item.get('url' , '') ,
                    item.get('lat' , 0.0) ,
                    item.get('lon' , 0.0) ,
                    item.get('cityId' , 0) ,
                    item.get('cityName' , '') ,
                    item.get('districtId' , 0) ,
                    item.get('districtName' , '') ,
                    item.get('poiId' , 0) ,
                    item.get('alias' , '') ,
                    item.get('commentCount' , 0) ,
                    item.get('commentScore' , 0.0) ,
                    item.get('recommend' , '') ,
                    item.get('address' , '')
                ))

            # 提交每次插入
            connection.commit()

            # 插入成功打印反馈
            print(f"插入成功: {city_name} - {item[ 'word' ]}")

    except Error as e :
        print(f"Error inserting data into MySQL: {e}")
    finally :
        if connection.is_connected() :
            cursor.close()
            connection.close()


# 获取每个城市的热门景点数据
def get_city_hotspots(city_name) :
    url = base_url.format(city_name + "热门景点")
    response = requests.get(url , headers=headers)

    if response.status_code == 200 :
        # 解析返回的JSON数据
        data = response.json()

        # 检查是否有"data"字段并处理
        if "data" in data :
            city_data = [ ]  # 用来存储每个城市的景点数据

            for item in data[ "data" ] :
                # 跳过ID为0的景点
                if item.get("id") == 0 :
                    continue  # 跳过此景点

                # 获取所需的字段，并重命名 API 返回的 id 为 external_id
                city_data.append(
                    {
                        "id" : item.get('id' , '暂无信息') ,  # 这里的 id 将作为 external_id 存储到数据库
                        "code" : item.get('code' , '') ,
                        "word" : item.get('word' , '') ,
                        "eName" : item.get('eName' , '') ,
                        "type" : item.get('type' , '') ,
                        "productId" : item.get('productId' , 0) ,
                        "url" : item.get('url' , '') ,
                        "lat" : item.get('lat' , 0.0) ,
                        "lon" : item.get('lon' , 0.0) ,
                        "cityId" : item.get('cityId' , 0) ,
                        "cityName" : item.get('cityName' , '') ,
                        "districtId" : item.get('districtId' , 0) ,
                        "districtName" : item.get('districtName' , '') ,
                        "poiId" : item.get('poiId' , 0) ,
                        "alias" : item.get('alias' , '') ,
                        "commentCount" : item.get('commentCount' , 0) ,
                        "commentScore" : item.get('commentScore' , 0.0) ,
                        "recommend" : item.get('recommend' , '') ,
                        "address" : item.get('address' , '')
                    })

            # 将数据转为 DataFrame 并写入 Excel 中
            if city_data :
                df = pd.DataFrame(city_data)
                df.to_excel(excel_writer , sheet_name=city_name , index=False)
                print(f"{city_name} 的景点数据已写入 Excel")

            # 将数据插入 MySQL
            insert_to_mysql(city_name , city_data)

        else :
            print(f"未找到 {city_name} 的景点数据")
    else :
        print(f"请求失败，状态码: {response.status_code}，城市: {city_name}")


# 创建数据库和表
create_db_and_table()

# 创建线程池并行获取多个城市的景点数据
with ThreadPoolExecutor(max_workers=5) as executor :
    # 为每个城市启动一个线程
    executor.map(get_city_hotspots , world_data.keys())

# 保存 Excel 文件
excel_writer.save()
print("所有城市的景点数据已保存到 'city_hotspots.xlsx' 文件")
