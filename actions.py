from flask import Blueprint, request, render_template, redirect, url_for, flash, Response, jsonify, session
import mysql.connector
import logging
from logging.handlers import RotatingFileHandler

from app import db, DatabaseInfor

actions = Blueprint('actions', __name__, template_folder='templates')


# Cấu hình logging
def config_logger():
    # Cấu hình logger
    logger = logging.getLogger('copy_procedure')
    # Các cấu hình handler, formatter
    logger.info("Logger initialized!")

    return logger


logger = config_logger()

@actions.route('/')
def index():
    if request.method == 'GET':
        results = db.session.query(DatabaseInfor).all()
        # Lưu trữ dữ liệu vào session
        session['connectionInfo'] = results

        return render_template('index.html', connectionInfo=session['connectionInfo'])

    return render_template('index.html')


@actions.route('/general', methods=['GET'])
def general():
    if request.method == 'GET':
        results = db.session.query(DatabaseInfor).all()
        session['connectionInfo'] = results
        return render_template('general.html', connectionInfo=session['connectionInfo'])

    return render_template('general.html')


@actions.route('/test-connection', methods=['POST'])
def test_connection():
    print("test_connection")

    try:
        if request.method == 'POST':
            # Lấy dữ liệu từ form
            dialect = request.form['dialect']
            host = request.form['host']
            port = request.form['port']
            database = request.form['database']
            username = request.form['username']
            password = request.form['password']

            if dialect == 'mysql':
                # Tạo kết nối tới MySQL database
                connection = mysql.connector.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password
                )
                if connection.is_connected():
                    connection.close()
                    return jsonify({'status': 'success', 'message': 'Connection successful!'})
                else:
                    return jsonify({'status': 'error', 'message': 'Connection failed!'})

            return jsonify({'status': 'error', 'message': 'Connection failed!'})
    except Exception as e:
        # Xảy ra lỗi khi kết nối
        print('Connection error: ' + str(e))
        return jsonify({'status': 'error', 'message': str(e)})


@actions.route('/connection-database', methods=['POST'])
def connection_database():
    print("connection_database")
    try:
        if request.method == 'POST':
            # Lấy dữ liệu từ form
            dialect = request.form['dialect']
            host = request.form['host']
            port = request.form['port']
            database = request.form['database']
            username = request.form['username']
            password = request.form['password']

            if dialect == 'mysql':
                # Tạo kết nối tới MySQL database
                connection = mysql.connector.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password
                )
            else:
                connection = None
                return jsonify({'status': 'error', 'message': 'Connection failed!'})

            if connection.is_connected():
                connection.close()
                connectionInfo = {
                    'dialect': dialect,
                    'host': host,
                    'port': port,
                    'database': database,
                    'username': username,
                    'password': password,

                }

                # insert to database :
                # 1. check database is existed
                results = DatabaseInfor.query.filter_by(dialect=dialect, name=database, host=host).first()
                if results is None:
                    new_database = DatabaseInfor(dialect=dialect, name=database, host=host,
                                                 port=port,
                                                 username=username, password=password)

                    db.session.add(new_database)
                    db.session.commit()

                    return jsonify(
                        {'status': 'success', 'message': 'Add connection successful!', 'data': connectionInfo})
                else:
                    return jsonify({'status': 'error', 'message': 'Connection is existed, add connection failed!'})

            else:
                return jsonify({'status': 'error', 'message': 'Connection failed!'})

    except Exception as e:
        # Xảy ra lỗi khi kết nối
        print("error : ", e)
        return jsonify({'status': 'error', 'message': str(e)})


@actions.route
def remove_connection():
    print("remove_connection")


@actions.route('/db-actions')
def db_action():
    print("#### [db_action] ####")
    dbname = request.args.get('dbname')
    dbhost = request.args.get('dbhost')
    results = DatabaseInfor.query.filter_by(dialect='mysql', name=dbname, host=dbhost).first()
    session['dbTargetInfor'] = results
    return render_template('dbaction.html', dbTargetInfor=results, connectionInfo=session['connectionInfo'])


@actions.route('/get-list-table', methods=['GET'])
def get_list_table():
    print("### [get_list_table] ###")

    dbdialect = request.args.get('dbdialect')
    dbname = request.args.get('dbname')
    dbhost = request.args.get('dbhost')

    table_names = get_table_names(dbdialect, dbname, dbhost)
    response_data = {'table_names': table_names}
    return response_data

def get_table_names(dbdialect, dbname, dbhost):
    table_names = []
    try:
        # Lấy thông tin kết nối của database:
        results = DatabaseInfor.query.filter_by(dialect=dbdialect, name=dbname, host=dbhost).first()

        # Kết nối đến cơ sở dữ liệu
        connection = mysql.connector.connect(
            host=results.host,
            port=results.port,
            database=results.name,
            user=results.username,
            password=results.password
        )
        cursor = connection.cursor()

        # Truy vấn SQL để lấy tên các bảng và loại bỏ các view trong cơ sở dữ liệu
        cursor.execute("SHOW FULL TABLES")
        rows = cursor.fetchall()

        # Lấy tên các bảng và lưu vào list table_names (chỉ lấy bảng thực tế, loại bỏ view)
        for row in rows:
            if row[1].lower() == 'base table':
                table_names.append(row[0])

        # Đóng kết nối
        cursor.close()
        connection.close()

    except Exception as e:
        print("Error:", e)
        logger.info("[get_table_names]_Error:", e)

    return table_names