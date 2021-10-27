from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init(app, db_path):
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    db.app = app
    db.init_app(app)
    db.create_all(app=app)
    return app
