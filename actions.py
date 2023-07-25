from flask import Blueprint, request, render_template, redirect, url_for, flash, Response, jsonify, session
import mysql.connector
from app import db, DatabaseInfor

actions = Blueprint('actions', __name__, template_folder='templates')


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


@actions.route('/transfer-actions')
def transfer_actions():
    transfer_data_mysql_to_mysql()
    return jsonify(
        {'status': 'success', 'message': 'Migration successful!', 'data': 'success'})


def transfer_data_mysql_to_mysql():
    print("#### [transfer_data_mysql_to_mysql] ####")
    try:
        source_connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='coe_management',
            user='root',
            password='root'
        )
        source_cursor = source_connection.cursor()

        target_connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='test',
            user='root',
            password='root'
        )
        target_cursor = target_connection.cursor()

        # Lấy danh sách các bảng từ cơ sở dữ liệu nguồn
        table_names = get_table_names("coe_management", "localhost")

        # Bắt đầu transaction trên cơ sở dữ liệu đích
        target_connection.start_transaction()

        # Truy vấn dữ liệu từ các bảng của cơ sở dữ liệu nguồn và chuyển sang cơ sở dữ liệu đích
        for table_name in table_names:
            # Lấy thông tin cấu trúc bảng từ cơ sở dữ liệu nguồn
            columns = get_table_structure(table_name)
            if columns:
                # Tạo truy vấn SQL để tạo bảng tương ứng trong cơ sở dữ liệu đích
                create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
                for column in columns:
                    column_name = column[0]
                    data_type = column[1]
                    create_table_sql += f"{column_name} {data_type}, "
                create_table_sql = create_table_sql.rstrip(", ") + ")"

                # Thực hiện truy vấn để tạo bảng trong cơ sở dữ liệu đích
                target_cursor.execute(create_table_sql)

                # Truy vấn dữ liệu từ cơ sở dữ liệu nguồn
                source_cursor.execute(f"SELECT * FROM {table_name}")
                rows = source_cursor.fetchall()

                # Kiểm tra và thực hiện bulk insert dữ liệu vào cơ sở dữ liệu đích
                if rows:
                    num_values = len(rows[0])
                    if num_values > 0:
                        insert_sql = f"INSERT INTO {table_name} VALUES ({', '.join(['%s'] * num_values)})"
                        target_cursor.executemany(insert_sql, rows)


        # Lưu thay đổi vào cơ sở dữ liệu đích
        target_connection.commit()
        # Đóng kết nối
        source_cursor.close()
        source_connection.close()
        target_cursor.close()
        target_connection.close()

        print("Data transfer successful!")



    except Exception as e:
        print("Error:", e)


@actions.route('/get-list-table', methods=['GET'])
def get_list_table():
    print("### [mrd get_list_table] ###")

    dbname = request.args.get('dbname')
    dbhost = request.args.get('dbhost')

    table_names = get_table_names(dbname, dbhost)
    response_data = {'table_names': table_names}
    return response_data


# Hàm để lấy tên các bảng từ cơ sở dữ liệu MySQL
def get_table_names(dbname, dbhost):
    table_names = []
    try:
        # Lấy thông tin kết nối của database:
        results = DatabaseInfor.query.filter_by(dialect='mysql', name=dbname, host=dbhost).first()

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


        # copy_views()

        # Đóng kết nối
        cursor.close()
        connection.close()

    except Exception as e:
        print("Error:", e)

    return table_names


def get_table_structure(table_name):
    try:
        # Kết nối đến cơ sở dữ liệu nguồn (database A)
        source_connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='coe_management',
            user='root',
            password='root'
        )
        source_cursor = source_connection.cursor()

        # Truy vấn cấu trúc bảng từ cơ sở dữ liệu nguồn
        source_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = source_cursor.fetchall()

        # Đóng kết nối
        source_cursor.close()
        source_connection.close()

        # Chuyển đổi các giá trị bytes sang chuỗi Unicode ( mysql trả cho python kiểu byte)
        columns_decoded = []
        for col in columns:
            column_name = col[0]
            column_type = col[1].decode('utf-8')  # Chuyển đổi từ bytes sang chuỗi Unicode
            # Các thông tin khác về cột (nếu có) vẫn giữ nguyên giá trị bytes
            columns_decoded.append((column_name, column_type) + col[2:])

        # Trả về danh sách các cột của bảng và kiểu dữ liệu tương ứng
        return columns_decoded

    except Exception as e:
        print("Error:", e)
        return None

def copy_views():
    try:
        source_connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='coe_management',
            user='root',
            password='root'
        )
        source_cursor = source_connection.cursor()

        target_connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='test',
            user='root',
            password='root'
        )
        target_cursor = target_connection.cursor()

        # Truy vấn danh sách các view trong cơ sở dữ liệu nguồn
        source_cursor.execute("SHOW FULL TABLES WHERE TABLE_TYPE LIKE 'VIEW'")
        views = source_cursor.fetchall()

        for view in views:
            view_name = view[0]

            # Truy vấn nội dung của view từ cơ sở dữ liệu nguồn
            source_cursor.execute(f"SHOW CREATE VIEW {view_name}")
            create_view_sql = source_cursor.fetchone()[1]

            # Thay đổi tên database trong SQL để tạo view trong cơ sở dữ liệu đích
            create_view_sql = create_view_sql.replace('coe_management', 'test')

            # Thực thi truy vấn để tạo view trong cơ sở dữ liệu đích
            target_cursor.execute(create_view_sql)

        # Lưu thay đổi vào cơ sở dữ liệu đích
        target_connection.commit()

        # Đóng kết nối
        source_cursor.close()
        source_connection.close()
        target_cursor.close()
        target_connection.close()

        print("Copy views successful!")

    except Exception as e:
        print("Error:", e)