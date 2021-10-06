import json
import os
from io import BytesIO
from unittest import TestCase

import database as db
from app import app

TEST_DB_PATH = os.getcwd() + '/test.db'

if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

db.init(app, TEST_DB_PATH)


class FlaskTestCase(TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.assertEqual([], db.CSVFile.query.all())

        # I load a csv in
        self.filename = os.path.basename('test_csv_1.csv')
        with open(f'{os.curdir}/{self.filename}', 'rb') as data:
            db.CSVFile.load(data, self.filename)

    def tearDown(self):
        del self.client
        db.CSVFile.query.delete()


class TestCSVFile(FlaskTestCase):
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

    def test_viable_columns(self):
        csvfile = db.CSVFile.query.one()

        # This csv's columns:
        # seq, name/first, name/last, age, street, city, state, zip, dollar, pick, date

        # Of these, we can expect the following to be viable:
        # seq (though not useful), age, dollar, date

        viable_cols = csvfile.viable_columns
        self.assertEqual([0, 3, 7, 8], [col[0] for col in viable_cols])
        self.assertEqual(['seq', 'age', 'zip', 'dollar'], [col[1] for col in viable_cols])


class TestFlask(FlaskTestCase):
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
        self.assertEqual([self.filename], response_json['uploadedFiles'])

    def test_upload(self):
        # I upload a second csv
        filename = 'test_csv_2.csv'
        with open(f'{os.curdir}/{filename}', 'rb') as data:
            response = self.client.post('/upload', data={
                "csv": (data, filename)
            })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.get_data())
        # The API returns the csv's filename
        self.assertEqual(filename, response_json['filename'])

        # As well as a preview of the csv
        csvfile = db.CSVFile.query.all()[1]
        self.assertEqual(list(csvfile.dump(end=6)), response_json['data'])

        # And the number of usable and discarded rows
        self.assertEqual(len(csvfile), response_json['numRows'])
        self.assertEqual(1, response_json['numDiscarded'])

        # Along with indices for viable columns
        self.assertEqual([0, 3, 4, 5, 6], response_json['viableColumnIndices'])
