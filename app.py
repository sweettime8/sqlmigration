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

app.config["SECRET_KEY"] = 'pid-sku-coe.2023'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///{}'.format(db_path)

# Cấu hình ứng dụng sử dụng session
app.config['SESSION_TYPE'] = 'filesystem'  # Lưu trữ session trong tệp hệ thống tạm thời
# Khởi tạo extension Session
Session(app)

db = SQLAlchemy(app)

class DatabaseInfor(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    dialect = db.Column(db.String(100))
    name = db.Column(db.String(100))
    host = db.Column(db.String(100))
    port = db.Column(db.Integer)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

