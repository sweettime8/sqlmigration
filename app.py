from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os, sys
from flask_session import Session

# Application initializations
app = Flask(__name__)

isExist = os.path.exists("database")
if not isExist:
    os.makedirs("database")
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir + "\database", 'migrationdb.db')

print("mrd db_path : " + db_path)
session_path = os.path.abspath(os.path.dirname(__file__)) + "\\flask_session"

app.config["SECRET_KEY"] = 'pid-sku-coe.2023'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///{}'.format(db_path)

# Cấu hình ứng dụng sử dụng session
app.config['SESSION_TYPE'] = 'filesystem'  # Lưu trữ session trong tệp hệ thống tạm thời
# Khởi tạo extension Session
Session(app)

def clear_session(session_path):
    # Kiểm tra xem thư mục tồn tại hay không
    if os.path.exists(session_path):
        # Lấy danh sách các tệp và thư mục trong folder
        items = os.listdir(session_path)
        for item in items:
            item_path = os.path.join(session_path, item)
            # Kiểm tra nếu item là thư mục thì gọi đệ quy để xóa nó
            if os.path.isdir(item_path):
                clear_session(item_path)
            else:
                # Nếu item là tệp tin thì xóa nó
                os.remove(item_path)
    else:
        print(f"Thư mục {session_path} không tồn tại.")

clear_session(session_path)

db = SQLAlchemy(app)

class DatabaseInfor(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    dialect = db.Column(db.String(100))
    name = db.Column(db.String(100))
    host = db.Column(db.String(100))
    port = db.Column(db.Integer)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

