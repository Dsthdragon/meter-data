import os


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('JAWSDB_MARIA_URL') or "mysql+pymysql://root:""@localhost/meter_data"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    IMAGE_UPLOAD_FOLDER = os.path.abspath(
        os.path.join("app", "static", "upload", "images")
    )
    IMAGE_SIZE = [500, 500]
    ALLOWED_EXTENSIONS = ['png', 'jpeg', 'jpg', 'gif']
