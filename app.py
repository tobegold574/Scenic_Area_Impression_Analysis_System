from flask import Flask, render_template
from flask import Flask
from analy.districtname import districtname_app
from analy.cityname import cityname_app
from emotion.searchmap import searchmap_app
from emotion.search import search_app
from emotion.searchecharts import searchecharts_app
from analy.map import map_app
from analy.recomend import recomend_app
from manage.login import login_app
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
from flask import session, redirect, url_for
import functools
from flask import Flask, render_template, jsonify
import json
from models import User, UserModelView,db
from models import WeiboCommentsModelView,WeiboComments,AttractionsModelView,Attractions
# 创建一个 Flask 应用实例
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
babel = Babel(app)

app.register_blueprint(login_app)
app.register_blueprint(districtname_app)
app.register_blueprint(cityname_app)
app.register_blueprint(search_app)
app.register_blueprint(searchecharts_app)
app.register_blueprint(searchmap_app)
app.register_blueprint(map_app)
app.register_blueprint(recomend_app)


# 配置 MySQL 连接信息
db_user = 'root'
db_password = 'admin'
db_host = 'localhost'
db_name = 'travel'

# 配置数据库 URI
db_uri = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}"

# 设置 Flask 应用的数据库 URI
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

# 创建数据库实例
db.init_app(app)


# 创建管理员视图
admin = Admin(app, name='旅游景区数据分析与推荐系统后台', template_mode='bootstrap3')
admin.add_view(UserModelView(User, db.session , name='用户管理'))
admin.add_view(WeiboCommentsModelView(WeiboComments, db.session , name='景区风评管理'))
admin.add_view(AttractionsModelView(Attractions, db.session , name='景区数据管理'))


# 错误处理路由
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', message="页面未找到"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message="服务器内部错误"), 500


if __name__ == '__main__':
    app.run(debug=True)