
import webview
from actions import actions
import configparser
from app import app, db

app.register_blueprint(actions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    parser = configparser.ConfigParser()
    parser.read("./config/config.txt")
    http_port = parser.get("config", "http_port")
    http_server = parser.get("config", "http_server")
    app_width = parser.get("config", "app_width")
    app_height = parser.get("config", "app_height")

    window = webview.create_window('App - SQL Migration', app, width=int(app_width), height=int(app_height))
    webview.start(http_port=http_port, http_server=http_server)
