from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from email.mime.multipart import MIMEMultipart
import json
import os
from models import User,db
from flask import Flask, jsonify, send_from_directory
import json
from flask import session, redirect, url_for
import functools


login_app = Blueprint('login_app', __name__)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'username' not in session:
            return redirect(url_for('login_app.login'))  # 未登录则重定向到登录页面
        return view(**kwargs)
    return wrapped_view


# 注册功能
@login_app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # 管理员或普通用户

        # 创建新用户对象
        new_user = User(username=username, password=password, role=role)

        # 添加新用户到数据库
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login_app.login'))  # 注册成功后重定向到登录页面

    return render_template('register.html')

# 登录功能
@login_app.route('/login', methods=['GET', 'POST'])
def login() :
    if request.method == 'POST' :
        username = request.form[ 'username' ]
        password = request.form[ 'password' ]

        # 查询用户数据库验证用户名和密码
        user = User.query.filter_by(username=username , password=password).first()

        if user :
            session[ 'username' ] = user.username  # 使用会话记录用户登录状态

            if user.role == 'admin' :
                return redirect(url_for('login_app.admin'))  # 管理员重定向到 admin 路由
            else :
                return redirect(url_for('login_app.home'))  # 普通用户重定向到 home 路由
        else :
            return "Invalid username or password"

    return render_template('login.html')

@login_app.route('/')
@login_required
def home():
    # 渲染 home.html 模板
    return render_template('home.html')

@login_app.route('/admin')
@login_required
def admin():
    # 渲染 home.html 模板
    return render_template('admin.html')


# 登出功能
@login_app.route('/logout')
def logout():
    # 清除会话中的用户信息
    session.pop('username', None)
    # 重定向到登录页面
    return redirect(url_for('login_app.login'))

@login_app.route('/profile')
def profile():
    # 检查用户是否已登录
    if 'username' in session:
        # 查询当前登录用户的信息
        user = User.query.filter_by(username=session['username']).first()
        if user:
            return render_template('profile.html', user=user)
    return redirect(url_for('login_app.login'))


@login_app.route('/edit_profile' , methods=[ 'GET' , 'POST' ])
def edit_profile() :
    if 'username' in session :
        user = User.query.filter_by(username=session[ 'username' ]).first()
        if user :
            if request.method == 'POST' :
                # 获取表单提交的数据
                user.email = request.form[ 'email' ]
                user.full_name = request.form[ 'full_name' ]
                user.address = request.form[ 'address' ]
                user.phone_number = request.form[ 'phone_number' ]
                user.birthday = request.form[ 'birthday' ]

                # 保存修改到数据库
                db.session.commit()

                return redirect(url_for('login_app.profile'))
            return render_template('edit_profile.html' , user=user)
    return redirect(url_for('login_app.login'))


@login_app.route('/change_password' , methods=[ 'GET' , 'POST' ])
def change_password() :
    if 'username' in session :
        user = User.query.filter_by(username=session[ 'username' ]).first()
        if user :
            if request.method == 'POST' :
                old_password = request.form[ 'old_password' ]
                new_password = request.form[ 'new_password' ]
                confirm_password = request.form[ 'confirm_password' ]

                # 验证旧密码是否匹配
                if old_password == user.password :
                    # 验证新密码和确认密码是否匹配
                    if new_password == confirm_password :
                        # 更新密码并保存到数据库
                        user.password = new_password
                        db.session.commit()
                        return redirect(url_for('login_app.profile'))
                    else :
                        return "New password and confirm password do not match."
                else :
                    return "Incorrect old password."
            return render_template('change_password.html')
    return redirect(url_for('login_app.login'))



@login_app.route('/send_message' , methods=[ 'GET' , 'POST' ])
def send_message() :
    # 检查当前用户是否是管理员
    if 'username' in session :
        user = User.query.filter_by(username=session[ 'username' ]).first()
        if user and user.role == 'admin' :
            if request.method == 'POST' :
                message = request.form.get('message')
                # 调用发送消息的函数
                send_message_to_all_users(message)
                return "Message sent successfully!"
            return render_template('send_message.html')
    return redirect(url_for('login_app.login'))


def send_message_to_all_users(message) :
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header

    # 发件人邮箱
    sender_email = "3577441407@qq.com"
    # 发件人邮箱密码（注意：这里不是邮箱的登录密码，而是授权码）
    password = "ivouktyohlzmchcd"
    # 收件人邮箱列表，这里假设用户的邮箱存储在 email 字段中
    users = User.query.all()
    receivers = [ user.email for user in users if user.email ]

    # 创建一个带有 "From" 头部信息的 MIMEMultipart 对象
    msg = MIMEMultipart()
    msg[ "From" ] = sender_email  # 设置发件人邮箱地址
    msg[ "To" ] = ", ".join(receivers)  # 设置收件人邮箱地址，多个邮箱地址之间用逗号分隔
    msg[ "Subject" ] = "旅游景区数据分析与推荐系统"  # 设置邮件主题

    # 邮件内容
    body = message
    msg.attach(MIMEText(body , "plain"))  # 添加纯文本邮件正文

    try :
        smtpObj = smtplib.SMTP_SSL('smtp.qq.com' , 465)
        smtpObj.login(sender_email , password)
        smtpObj.sendmail(sender_email , receivers , msg.as_string())  # 将 MIMEMultipart 对象转换为字符串发送
        smtpObj.quit()
        print("邮件发送成功")
    except smtplib.SMTPException as e :
        print("Error: 无法发送邮件" , e)



# 确保 JSON 文件存在
def ensure_json_file():
    if not os.path.exists('announcements.json'):
        with open('announcements.json', 'w') as file:
            json.dump([], file)

# 在应用启动时调用函数确保 JSON 文件存在
ensure_json_file()



@login_app.route('/send_announcement', methods=['GET', 'POST'])
def send_announcement():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user and user.role == 'admin':
            if request.method == 'POST':
                announcement_content = request.form.get('announcement_content')
                # 读取现有的公告信息
                with open('announcements.json', 'r') as file:
                    announcements = json.load(file)
                # 添加新的公告
                announcements.append({'content': announcement_content})
                # 将更新后的公告信息写入 JSON 文件
                with open('announcements.json', 'w') as file:
                    json.dump(announcements, file, indent=4)
                return redirect(url_for('login_app.send_announcement'))
            return render_template('send_announcement.html')
    return redirect(url_for('login_app.login'))

@login_app.route('/announcements')
def view_announcements():
    # 读取公告信息
    with open('announcements.json', 'r') as file:
        announcements = json.load(file)
    return render_template('announcements.html', announcements=announcements)


@login_app.route('/manage_announcements', methods=['GET', 'POST'])
def manage_announcements():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user and user.role == 'admin':
            # 读取公告信息
            with open('announcements.json', 'r') as file:
                announcements = json.load(file)
            if request.method == 'POST':
                if 'edit_announcement' in request.form:
                    # 编辑公告
                    edited_announcement = request.form.get('edited_announcement')
                    announcement_id = int(request.form.get('announcement_id'))
                    announcements[announcement_id]['content'] = edited_announcement
                    # 将更新后的公告信息写入 JSON 文件
                    with open('announcements.json', 'w') as file:
                        json.dump(announcements, file, indent=4)
                elif 'delete_announcement' in request.form:
                    # 删除公告
                    announcement_id = int(request.form.get('announcement_id'))
                    del announcements[announcement_id]
                    # 将更新后的公告信息写入 JSON 文件
                    with open('announcements.json', 'w') as file:
                        json.dump(announcements, file, indent=4)
                return redirect(url_for('login_app.manage_announcements'))
            return render_template('manage_announcements.html', announcements=announcements)
    return redirect(url_for('login_app.login'))

