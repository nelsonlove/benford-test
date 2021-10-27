from flask import Flask
from flask_rest_jsonapi import Api
from . import routes
from . import resource
from . import database as db


def create_app(db_path='./benford.db'):
    app = Flask(__name__)

    # Setup db
    db.init(app, db_path)

    # Add routes
    api = Api(app)
    app.add_url_rule('/', view_func=routes.home)
    app.add_url_rule('/upload', view_func=routes.upload, methods=['POST'])
    api.route(resource.CSVList, 'csv_list', '/csv')
    api.route(resource.CSVDetail, 'csv_detail', '/csv/<int:id>')
    api.route(resource.CSVPreview, 'preview', '/csv/<int:id>/preview')
    api.route(resource.CSVAnalysis, 'analysis', '/csv/<int:id>/analysis')

    return app


if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=8000, debug=True)
