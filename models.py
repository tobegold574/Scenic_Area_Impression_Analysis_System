from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from datetime import datetime

db = SQLAlchemy()



# 定义用户模型
class User(db.Model) :
    id = db.Column(db.Integer , primary_key=True)
    username = db.Column(db.String(50) , unique=True , nullable=False)
    password = db.Column(db.String(100) , nullable=False)
    role = db.Column(db.Enum('admin' , 'user') , nullable=False)
    email = db.Column(db.String(100) , nullable=True)
    full_name = db.Column(db.String(100) , nullable=True)
    address = db.Column(db.String(200) , nullable=True)
    phone_number = db.Column(db.String(20) , nullable=True)
    birthday = db.Column(db.Date , nullable=True)


# 自定义用户模型视图
class UserModelView(ModelView) :
    column_labels = {
        'username' : '用户名' ,
        'password' : '密码' ,
        'role' : '角色' ,
        'email' : '邮箱' ,
        'full_name' : '姓名' ,
        'address' : '地址' ,
        'phone_number' : '电话号码' ,
        'birthday' : '生日'
    }

    # 启用搜索功能
    column_searchable_list = [ 'username' , 'email' , 'full_name','password','address','phone_number', 'birthday']  # 设定可以搜索的字段

    # 可以选择启用过滤功能，例：按角色过滤
    column_filters = [  'username' , 'email' , 'full_name','password','address','phone_number', 'birthday' ]


# 定义微博评论模型
class WeiboComments(db.Model) :
    id = db.Column(db.Integer , primary_key=True)  # 主键
    topic_index = db.Column(db.Integer , nullable=True)
    topic = db.Column(db.String(255) , nullable=True)
    mid = db.Column(db.String(255) , nullable=True)
    comment_index = db.Column(db.Integer , nullable=True)
    created_at = db.Column(db.DateTime , default=datetime.utcnow)  # 默认使用当前时间
    user_id = db.Column(db.String(255) , nullable=True)
    text = db.Column(db.Text , nullable=True)
    source = db.Column(db.String(255) , nullable=True)
    screen_name = db.Column(db.String(255) , nullable=True)
    followers_count = db.Column(db.Integer , nullable=True)
    statuses_count = db.Column(db.Integer , nullable=True)
    gender = db.Column(db.String(10) , nullable=True)
    like_count = db.Column(db.Integer , nullable=True)
    total_number = db.Column(db.Integer , nullable=True)

    # 情感分析
    sentiment = db.Column(db.String(10) , nullable=True)  # 情感分类
    sentiment_score = db.Column(db.Float , nullable=True)  # 情感得分


# 自定义微博评论模型视图
class WeiboCommentsModelView(ModelView) :
    column_labels = {
        'topic_index' : '话题索引' ,
        'topic' : '话题' ,
        'mid' : '微博 ID' ,
        'comment_index' : '评论索引' ,
        'created_at' : '创建时间' ,
        'user_id' : '用户 ID' ,
        'text' : '评论内容' ,
        'source' : '来源' ,
        'screen_name' : '用户昵称' ,
        'followers_count' : '粉丝数' ,
        'statuses_count' : '发布微博数' ,
        'gender' : '性别' ,
        'like_count' : '点赞数' ,
        'total_number' : '评论数' ,
        'sentiment' : '情感分类' ,
        'sentiment_score' : '情感得分'
    }

    # 启用搜索功能
    column_searchable_list = [
        'topic' , 'mid' , 'user_id' , 'text' , 'source' , 'screen_name' , 'gender' , 'sentiment'
    ]

    # 启用过滤功能
    column_filters = [
        'topic' , 'mid' , 'created_at' , 'user_id' , 'sentiment' , 'gender'
    ]

    # 你可以自定义排序、分页等操作
    column_default_sort = ('created_at' , True)  # 默认按创建时间倒序排序


# 定义景点模型
class Attractions(db.Model) :
    id = db.Column(db.Integer , primary_key=True)  # 主键
    external_id = db.Column(db.Integer , nullable=True)
    code = db.Column(db.String(255) , nullable=True)
    word = db.Column(db.String(255) , nullable=True)
    eName = db.Column(db.String(255) , nullable=True)
    type = db.Column(db.String(50) , nullable=True)
    productId = db.Column(db.Integer , nullable=True)
    url = db.Column(db.String(255) , nullable=True)
    lat = db.Column(db.Float , nullable=True)
    lon = db.Column(db.Float , nullable=True)
    cityId = db.Column(db.Integer , nullable=True)
    cityName = db.Column(db.String(255) , nullable=True)
    districtId = db.Column(db.Integer , nullable=True)
    districtName = db.Column(db.String(255) , nullable=True)
    poiId = db.Column(db.Integer , nullable=True)
    alias = db.Column(db.String(255) , nullable=True)
    commentCount = db.Column(db.Integer , nullable=True)
    commentScore = db.Column(db.Float , nullable=True)
    recommend = db.Column(db.String(50) , nullable=True)
    address = db.Column(db.Text , nullable=True)


# 自定义景点模型视图
class AttractionsModelView(ModelView) :
    column_labels = {
        'external_id' : '外部ID' ,
        'code' : '编码' ,
        'word' : '名称' ,
        'eName' : '英文名' ,
        'type' : '类型' ,
        'productId' : '产品ID' ,
        'url' : 'URL' ,
        'lat' : '纬度' ,
        'lon' : '经度' ,
        'cityId' : '城市ID' ,
        'cityName' : '城市名称' ,
        'districtId' : '区ID' ,
        'districtName' : '区名称' ,
        'poiId' : 'POI ID' ,
        'alias' : '别名' ,
        'commentCount' : '评论数' ,
        'commentScore' : '评分' ,
        'recommend' : '推荐' ,
        'address' : '地址'
    }

    # 启用搜索功能
    column_searchable_list = [
        'code' , 'word' , 'eName' , 'type' , 'cityName' , 'districtName' , 'alias' , 'address'
    ]

    # 启用过滤功能
    column_filters = [
        'code' , 'word' , 'type' , 'cityName' , 'districtName' , 'recommend' , 'commentScore'
    ]

