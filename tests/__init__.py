import os
from app import create_app


def setup_once(app, db_name='test.db'):
    db_path = os.getcwd() + '/' + db_name

    if os.path.exists(db_path):
        os.remove(db_path)

    create_app(app, db_path)
    return app
