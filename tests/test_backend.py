import json
import os
from unittest import TestCase

import analysis
import database as db
from app import app
from tests import setup_once

setup_once(app)


class TestCSVFile(TestCase):
    def setUp(self):
        self.assertEqual([], db.CSVFile.query.all())

        # I load a csv in
        self.filename = os.path.basename('test_csv_1.csv')
        with open(f'{os.curdir}/{self.filename}', 'rb') as data:
            db.CSVFile.load(data, self.filename)

    def tearDown(self):
        db.CSVFile.query.delete()

    def test_load(self):
        csvfile = db.CSVFile.query.one()

        # The csv's filename and encoding is stored with the file
        self.assertEqual(self.filename, csvfile.filename)
        self.assertEqual('ascii', csvfile.encoding)

        # The csv has 102 rows
        self.assertEqual(102, len(csvfile))

        # But one row is missing columns
        self.assertEqual(1, len(csvfile.unusable()))

        # So I have 101 rows of potentially usable data
        # though there might be a header row as in this case
        self.assertEqual(101, len(csvfile.data()))

        # We can also get specific columns
        self.assertEqual(101, len(csvfile.column(0)))

    def test_viable_columns(self):
        csvfile = db.CSVFile.query.one()

        # This csv's columns:
        # seq, name/first, name/last, age, street, city, state, zip, dollar, pick, date

        # Of these, we can expect the following to be viable:
        # seq (though not useful), age, dollar, date

        viable_cols = csvfile.viable_columns
        self.assertEqual([0, 3, 7, 8], [col[0] for col in viable_cols])
        self.assertEqual(['seq', 'age', 'zip', 'dollar'], [col[1] for col in viable_cols])


class TestFlask(TestCase):
    def setUp(self):
        self.client = app.test_client()

    def tearDown(self):
        del self.client

    def test_index(self):
        # Flask is working!
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_preview(self):
        # I want info on the csv I uploaded
        response = self.client.get('/preview')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.get_data())

        # The API confirms that I've uploaded a csv called test_csv_1.csv
        self.assertEqual(['test_csv_1.csv'], response_json['uploadedFiles'])

    def test_upload(self):
        # I upload a csv
        filename = 'test_csv_2.csv'
        with open(f'{os.curdir}/{filename}', 'rb') as data:
            response = self.client.post('/upload', data={
                "csv": (data, filename)
            })
        self.assertEqual(response.status_code, 200)

        # The API returns the csv's filename
        response_json = json.loads(response.get_data())
        self.assertEqual(filename, response_json['filename'])

        # As well as a preview of the csv
        csvfile = db.CSVFile.query.all()[1]
        self.assertEqual(list(csvfile.dump(end=6)), response_json['data'])

        # And the number of usable and discarded rows
        self.assertEqual(len(csvfile), response_json['numRows'])
        self.assertEqual(1, response_json['numDiscarded'])

        # This csv has no headers but the columns look like this:
        #
        # 1,"Eldon Base for stackable storage shelf, platinum",
        # Muhammed MacIntyre,3,-213.25,38.94,35,Nunavut,Storage & Organization,0.8

        # So we might surmise that columns 0, 3, 4, 5, 6, and 9 are viable
        self.assertEqual([0, 3, 4, 5, 6, 9], response_json['viableColumnIndices'])

    def test_analyze(self):
        # I want to analyze a csv someone previously added to the database
        self.filename = os.path.basename('test_csv_1.csv')
        with open(f'{os.curdir}/{self.filename}', 'rb') as data:
            csvfile = db.CSVFile.load(data, self.filename)

        # Specifically I'm interested in the column with index of 3
        column_index = 3
        column = csvfile.column(column_index)

        # The API returns the data for the analysis
        response = self.client.get(f'/analyze?filename={csvfile.filename}&columnIndex={column_index}')
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.get_data())

        # This includes the sample size,
        data = analysis.clean_data(column)
        n = len(data)
        self.assertEqual(n, response_json['n'])

        # the expected distribution,
        expected = analysis.expected_distribution(n)
        self.assertEqual(expected, response_json['expectedDistribution'])

        # the observed distribution,
        observed = analysis.observed_distribution(data)
        self.assertEqual(observed, response_json['observedDistribution'])

        # the test statistic at various values of p,
        sum_chi_squares = analysis.sum_chi_squares(expected, observed)
        self.assertEqual(sum_chi_squares, response_json['testStatistic'])

        # and the test result
        goodness_of_fit = analysis.goodness_of_fit(expected, observed)
        self.assertEqual(goodness_of_fit, response_json['goodnessOfFit']['results'])
