import csv

from flask import Flask, current_app, render_template, request, url_for
from flask_rest_jsonapi import Api
import sqlalchemy.exc
from werkzeug.utils import secure_filename

from .api import CSVList, CSVDetail, CSVPreview, CSVAnalysis
from .models import CSVFile, db


def home():
    return render_template('index.html')


def upload():
    if 'csv' not in request.files.keys():
        return {'message': 'Error: No usable form data was found'}, 422
    file = request.files['csv']
    csvfile = CSVFile(file, secure_filename(file.filename))
    try:
        csvfile.reader()  # Make sure we can read the file
    except csv.Error:
        return {'message': 'Error: This file could not be parsed as a .csv.'}, 422
    try:
        db.session.add(csvfile)
        db.session.commit()
    except sqlalchemy.exc.SQLAlchemyError as error:
        if error.args[0] == '(sqlite3.IntegrityError) UNIQUE constraint failed: csv_file.filename':
            error_msg = 'Error: An uploaded file with that name already exists.'
        else:
            error_msg = 'There was an error uploading the file.'
        return {'message': error_msg}, 422
    else:
        client = current_app.test_client()
        response = client.get(url_for('csv_detail', id=csvfile.id))
        response.status_code = 201
        return response


def create_app(db_path='./benford.db'):
    app = Flask(__name__)

    # Setup db
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    db.app = app
    db.init_app(app)
    db.create_all(app=app)

    # Add routes
    api = Api(app)
    app.add_url_rule('/', view_func=home)
    app.add_url_rule('/upload', view_func=upload, methods=['POST'])
    api.route(CSVList, 'csv_list', '/csv')
    api.route(CSVDetail, 'csv_detail', '/csv/<int:id>')
    api.route(CSVPreview, 'preview', '/csv/<int:id>/preview')
    api.route(CSVAnalysis, 'analysis', '/csv/<int:id>/analysis')

    return app
