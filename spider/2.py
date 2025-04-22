import requests
import json

# 读取world.json文件，假设文件内容为您提供的格式
with open("world.json" , "r" , encoding="utf-8") as f :
    world_data = json.load(f)

# 定义基础API的URL格式
base_url = "https://m.ctrip.com/restapi/h5api/globalsearch/search?action=gsonline&source=globalonline&keyword={}&t=1731491818781"


# 函数：获取每个城市的热门景点数据
def get_city_hotspots(city_name) :
    url = base_url.format(city_name + "热门景点")
    response = requests.get(url)

    if response.status_code == 200 :
        # 解析返回的JSON数据
        data = response.json()

        # 检查是否有"data"字段并处理
        if "data" in data :
            print(f"\n{city_name} 的热门景点信息:")
            for item in data[ "data" ] :
                # 跳过ID为0的景点
                if item.get("id") == 0 :
                    continue  # 跳过此景点

                # 输出景点的必要字段信息（去掉不需要的字段）
                print(f"ID: {item.get('id' , '暂无信息')}")
                print(f"编码: {item.get('code' , '暂无信息')}")
                print(f"景点名称: {item.get('word' , '暂无信息')}")
                print(f"英文名称: {item.get('eName' , '暂无信息')}")
                print(f"类型: {item.get('type' , '暂无信息')}")
                print(f"产品ID: {item.get('productId' , '暂无信息')}")
                print(f"URL: {item.get('url' , '暂无链接')}")
                print(f"纬度: {item.get('lat' , '暂无纬度')}")
                print(f"经度: {item.get('lon' , '暂无经度')}")
                print(f"城市ID: {item.get('cityId' , '暂无城市ID')}")
                print(f"城市名称: {item.get('cityName' , '暂无城市名称')}")
                print(f"区域ID: {item.get('districtId' , '暂无区域ID')}")
                print(f"区域名称: {item.get('districtName' , '暂无区域名称')}")
                print(f"POI ID: {item.get('poiId' , '暂无POI ID')}")
                print(f"别名: {item.get('alias' , '暂无别名')}")
                print(f"评论数: {item.get('commentCount' , '暂无评论')}")
                print(f"评论评分: {item.get('commentScore' , '暂无评分')}")
                print(f"推荐: {item.get('recommend' , '暂无推荐')}")
                print(f"地址: {item.get('address' , '暂无地址')}")
                print("-" * 50)
        else :
            print(f"未找到 {city_name} 的景点数据")
    else :
        print(f"请求失败，状态码: {response.status_code}，城市: {city_name}")


# 循环遍历每个城市并获取热门景点
for city_name in world_data.keys() :
    get_city_hotspots(city_name)
