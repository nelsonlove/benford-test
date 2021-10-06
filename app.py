import sqlalchemy.exc
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

import analysis
import database as db

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/preview', methods=['GET'])
def preview(filename=None):
    filename = request.args.get('filename', filename)
    if not filename:
        files = db.CSVFile.query.order_by(db.CSVFile.date_created).all()
        return {'uploadedFiles': [file.filename for file in files]}, 200

    try:
        csvfile = db.CSVFile.query.filter_by(filename=filename).one()
    except sqlalchemy.exc.NoResultFound:
        return "File not found", 404
    else:
        data = list(csvfile.dump(end=7))
        preview_rows = min(len(data), 6)
        response = {
            'filename': csvfile.filename,
            'data': data[:preview_rows],
            'numRows': len(csvfile),
            'viableColumnIndices': [col[0] for col in csvfile.viable_columns],
            'numDiscarded': len(csvfile.unusable())
        }
        return response, 200


@app.route('/upload', methods=['POST'])
def upload():
    if 'csv' not in request.files:
        return 'No usable parameters found', 422
    file = request.files['csv']
    try:
        csvfile = db.CSVFile.load(file, secure_filename(file.filename))
    except sqlalchemy.exc.IntegrityError:
        return 'There was an error uploading the file.', 422
    return preview(csvfile.filename)


@app.route('/analyze', methods=['GET'])
def analyze(filename=None):
    filename = request.args.get('filename', filename)
    column_index = int(request.args['columnIndex'])
    if not filename:
        return "No file was specified", 400

    try:
        csvfile = db.CSVFile.query.filter_by(filename=filename).one()
    except sqlalchemy.exc.NoResultFound:
        return "File not found", 404
    else:
        column = csvfile.column(column_index)
        data = analysis.clean_data(column)
        expected = analysis.expected_distribution(len(data))
        observed = analysis.observed_distribution(data)
        response = {
            'n': len(data),
            'expectedDistribution': expected,
            'observedDistribution': observed,
            'testStatistic': analysis.sum_chi_squares(expected, observed),
            'goodnessOfFit': {
                'criticalValues': analysis.CRITICAL_VALUES,
                'results': analysis.goodness_of_fit(expected, observed)
            }
        }
        return response, 200


def main():
    db.init(app, 'benford.db')
    app.run()


if __name__ == '__main__':
    main()
