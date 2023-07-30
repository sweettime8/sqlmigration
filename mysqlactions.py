from flask import Blueprint, request, render_template, redirect, url_for, flash, Response, jsonify, session
import mysql.connector
import logging

from app import db, DatabaseInfor

mysqlactions = Blueprint('mysqlactions', __name__, template_folder='templates')


def config_logger():
    # Cấu hình logger
    logger = logging.getLogger('copy_procedure')
    # Các cấu hình handler, formatter
    logger.info("Logger initialized!")

    return logger


logger = config_logger()


@mysqlactions.route('/mysql-transfer-actions', methods=['POST'])
def mysql_transfer_actions():
    try:
        # Cấu hình kết nối cơ sở dữ liệu nguồn
        source_config = {
            'host': request.form['sourceHost'],
            'port': int(request.form['sourcePort']),
            'database': request.form['sourceDatabase'],
            'user': request.form['sourceUsername'],
            'password': request.form['sourcePassword']
        }

        target_config = {
            'host': request.form['targetHost'],
            'port': int(request.form['targetPort']),
            'database': request.form['targetDatabase'],
            'user': request.form['targetUsername'],
            'password': request.form['targetPassword']
        }

        sourceDialect = request.form['sourceDialect']
        targetDialect = request.form['targetDialect']

        if sourceDialect == 'mysql' and targetDialect == 'mysql':
            transfer_data_mysql_to_mysql(source_config, target_config)
            return jsonify(
                {'status': 'success', 'message': 'Migration successful!', 'data': 'success'})
        elif sourceDialect == 'mysql' and targetDialect == 'postgresql':
            transfer_data_mysql_to_postgresql(source_config, target_config)
            return jsonify(
                {'status': 'success', 'message': 'Migration successful!', 'data': 'success'})
        else:
            return jsonify(
                {'status': 'error', 'message': 'error! not found config for ' + sourceDialect + ' to ' + targetDialect})

    except Exception as e:
        # Xảy ra lỗi khi kết nối
        print("error : ", e)
        return jsonify({'status': 'error', 'message': str(e)})

##########################################################
#          transfer_data_mysql_to_posgresql              #
##########################################################
def transfer_data_mysql_to_postgresql(source_config, target_config):
    print("#### [transfer_data_mysql_to_posgresql] ####")
    try:
        source_connection = mysql.connector.connect(**source_config)
        source_cursor = source_connection.cursor()

        target_connection = mysql.connector.connect(**target_config)
        target_cursor = target_connection.cursor()
        # Lấy danh sách các bảng từ cơ sở dữ liệu nguồn
        table_names = get_table_names('mysql', source_config['database'], source_config['host'])

        # Bắt đầu transaction trên cơ sở dữ liệu đích
        target_connection.start_transaction()

        # Truy vấn dữ liệu từ các bảng của cơ sở dữ liệu nguồn và chuyển sang cơ sở dữ liệu đích
        for table_name in table_names:
            # Lấy thông tin cấu trúc bảng từ cơ sở dữ liệu nguồn
            columns = get_table_structure(source_config, table_name)

            # Kiểm tra xem bảng có tồn tại trong cơ sở dữ liệu đích hay không ( nếu chạy lần 2)

        print("#### [transfer_data_mysql_to_postgresql] : Success ####")
        logger.info("#### [transfer_data_mysql_to_posgresql] : Success ####")
    except Exception as e:
        logger.info("[transfer_data_mysql_to_postgresql]_Error:", e)
        print("Error:", e)

##########################################################
#              transfer_data_mysql_to_mysql              #
##########################################################
def transfer_data_mysql_to_mysql(source_config, target_config):
    print("#### [transfer_data_mysql_to_mysql] ####")
    try:
        source_connection = mysql.connector.connect(**source_config)
        source_cursor = source_connection.cursor()

        target_connection = mysql.connector.connect(**target_config)
        target_cursor = target_connection.cursor()

        # Lấy danh sách các bảng từ cơ sở dữ liệu nguồn
        table_names = get_table_names('mysql', source_config['database'], source_config['host'])

        # Bắt đầu transaction trên cơ sở dữ liệu đích
        target_connection.start_transaction()

        # Truy vấn dữ liệu từ các bảng của cơ sở dữ liệu nguồn và chuyển sang cơ sở dữ liệu đích
        for table_name in table_names:
            # Lấy thông tin cấu trúc bảng từ cơ sở dữ liệu nguồn
            columns = get_table_structure(source_config, table_name)

            # Kiểm tra xem bảng có tồn tại trong cơ sở dữ liệu đích hay không ( nếu chạy lần 2)
            target_cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            table_exists = target_cursor.fetchone()
            if table_exists:
                # Nếu bảng tồn tại, thực hiện câu lệnh DELETE để xóa toàn bộ dữ liệu trong bảng tránh bị duplicate
                delete_all_sql = f"DELETE FROM {table_name}"
                target_cursor.execute(delete_all_sql)

            if columns:
                # Tạo truy vấn SQL để tạo bảng tương ứng trong cơ sở dữ liệu đích
                create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
                primary_key_columns = []

                for column in columns:
                    column_name = column[0]
                    data_type = column[1]
                    create_table_sql += f"{column_name} {data_type}, "

                    # Kiểm tra xem cột có phải là khóa chính hay không
                    if column[3] == 'PRI':
                        # Nếu là khóa chính, thêm cột vào danh sách khóa chính
                        primary_key_columns.append(column_name)
                # Thêm phần tạo khóa chính vào câu truy vấn
                if primary_key_columns:
                    create_table_sql += f"PRIMARY KEY ({', '.join(primary_key_columns)}), "
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

        copy_views(source_config, target_config)
        copy_procedure(source_config, target_config)
        copy_functions(source_config, target_config)

        print("#### [transfer_data_mysql_to_mysql] : Success ####")
        logger.info("#### [transfer_data_mysql_to_mysql] : Success ####")

    except Exception as e:
        logger.info("[transfer_data_mysql_to_mysql]_Error:", e)
        print("Error:", e)


# Hàm để lấy tên các bảng từ cơ sở dữ liệu MySQL
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


def get_table_structure(soure_config, table_name):
    try:
        # Kết nối đến cơ sở dữ liệu nguồn (database A)
        source_connection = mysql.connector.connect(**soure_config)
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
        logger.info("[get_table_structure]_Error:", e)
        return None


def copy_views(source_config, target_config):
    try:
        logger.info("Bắt đầu quá trình copy copy_views")
        source_connection = mysql.connector.connect(**source_config)
        source_cursor = source_connection.cursor()

        target_connection = mysql.connector.connect(**target_config)
        target_cursor = target_connection.cursor()

        # Truy vấn danh sách các view trong cơ sở dữ liệu nguồn
        source_cursor.execute("SHOW FULL TABLES WHERE TABLE_TYPE LIKE 'VIEW'")
        views = source_cursor.fetchall()

        target_database = target_config['database']
        for view in views:
            view_name = view[0]
            # Kiểm tra xem view đã tồn tại trong cơ sở dữ liệu đích hay chưa
            # target_cursor.execute(f"SHOW FULL TABLES WHERE TABLE_NAME = '{view_name}' AND TABLE_TYPE = 'VIEW'")
            target_cursor.execute(
                f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{view_name}' AND TABLE_SCHEMA = '{target_database}' AND TABLE_TYPE = 'VIEW'")
            target_views = target_cursor.fetchall()

            if target_views:
                # Nếu view đã tồn tại trong cơ sở dữ liệu đích, thực hiện xóa view cũ
                target_cursor.execute(f"DROP VIEW IF EXISTS {view_name}")

            # Truy vấn nội dung của view từ cơ sở dữ liệu nguồn
            source_cursor.execute(f"SHOW CREATE VIEW {view_name}")
            create_view_sql = source_cursor.fetchone()[1]

            # Thay đổi tên database trong SQL để tạo view trong cơ sở dữ liệu đích
            create_view_sql = create_view_sql.replace(source_config['database'], target_config['database'])

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
        logger.info("[copy_views]_Error:", e)


############################# xử lý copy procedure ###############################:
def get_procedures(cursor, db):
    cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s", (db,))
    procedures = cursor.fetchall()
    return procedures


def get_procedure_details(cursor, procedure_name):
    cursor.execute(f"SHOW CREATE PROCEDURE `{procedure_name}`")
    try:
        create_procedure_sql = cursor.fetchone()[2]
        return create_procedure_sql
    except Exception as e:
        print("Error:", e)
        logger.info("[copy_procedure]_Error:", e)


def copy_procedure(source_db_config, target_db_config):
    try:
        print("### [copy_procedure] ###")
        # Kết nối đến cơ sở dữ liệu nguồn
        source_conn = mysql.connector.connect(**source_db_config)
        source_cursor = source_conn.cursor()

        # dung pymysql mới tạo được procedure
        target_conn = mysql.connector.connect(**target_db_config)
        target_cursor = target_conn.cursor()

        procedures = get_procedures(source_cursor, source_db_config['database'])
        for procedure in procedures:
            procedure_name = procedure[1]
            sql = get_procedure_details(source_cursor, procedure_name)

            try:
                target_cursor.execute(sql)
                target_conn.commit()

            except Exception as e:
                print("Error:", e)

        source_cursor.close()
        source_conn.close()
        target_cursor.close()
        target_conn.close()

        print("All procedures copied successfully!")
        logger.info("Copy procedures successful!")

    except Exception as e:
        print("Error:", e)
        logger.info("[copy_procedure]_Error:", e)


############################# xử lý copy functions ###############################
def copy_functions(source_config, target_config):
    print("### [copy_functions] ###")
    try:
        source_conn = mysql.connector.connect(**source_config)
        source_cursor = source_conn.cursor()

        target_conn = mysql.connector.connect(**target_config)
        target_cursor = target_conn.cursor()

        # Escape tên database nguồn, chỉ sử dụng backtick
        source_db = source_config['database']

        # Câu truy vấn INFO_SCHEMA, dùng format() để nhúng tên DB
        query = "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = '{}' AND  ROUTINE_TYPE='FUNCTION'".format(
            source_db)

        # Thực thi truy vấn
        source_cursor.execute(query)

        source_functions = source_cursor.fetchall()

        # Duyệt qua từng function
        for func in source_functions:
            # Lấy định nghĩa function
            source_cursor.execute("SHOW CREATE FUNCTION {}".format(func[0]))
            func_sql = source_cursor.fetchone()[2]

            # Tạo function trong DB đích
            target_cursor.execute(func_sql)

            # Lưu lại và đóng kết nối
            target_conn.commit()

            source_cursor.close()
            source_conn.close()

            target_cursor.close()
            target_conn.close()
    except Exception as e:
        print("Error:", e)
        logger.info("[copy_functions]_Error:", e)
