import csv

import sqlalchemy.exc
from flask import render_template, url_for, request
from werkzeug.utils import secure_filename

# from benford import analysis as analysis
# from benford.models import CSVFile
from flask import current_app
# from . import api
# from . import resource, schema
from .database import db
from .models import CSVFile


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


# def preview(filename=None):
#     filename = request.args.get('filename', filename)
#     if not filename:
#         files = CSVFile.query.order_by(CSVFile.date_created).all()
#         return {'uploadedFiles': [file.filename for file in files]}, 200
#
#     try:
#         csvfile = CSVFile.query.filter_by(filename=filename).one()
#     except sqlalchemy.exc.NoResultFound:
#         return "File not found", 404
#     else:
#         data = list(csvfile.dump(end=7))
#         preview_rows = min(len(data), 6)
#         response = {
#             'filename': csvfile.filename,
#             'data': data[:preview_rows],
#             'numRows': len(csvfile),
#             'viableColumnIndices': [col[0] for col in csvfile.viable_columns],
#             'numDiscarded': len(csvfile.unusable())
#         }
#         return response, 200
#
#
# def analyze(filename=None):
#     filename = request.args.get('filename', filename)
#     column_index = int(request.args['columnIndex'])
#     if not filename:
#         return "No file was specified", 400
#
#     try:
#         csvfile = CSVFile.query.filter_by(filename=filename).one()
#     except sqlalchemy.exc.NoResultFound:
#         return "File not found", 404
#     else:
#         column = csvfile.column(column_index)
#         data = analysis.clean_data(column)
#         expected = analysis.expected_distribution(len(data))
#         observed = analysis.observed_distribution(data)
#         response = {
#             'n': len(data),
#             'expectedDistribution': expected,
#             'observedDistribution': observed,
#             'testStatistic': analysis.sum_chi_squares(expected, observed),
#             'goodnessOfFit': {
#                 'criticalValues': analysis.CRITICAL_VALUES,
#                 'results': analysis.goodness_of_fit(expected, observed)
#             }
#         }
#         return response, 200
