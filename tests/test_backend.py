import os
from unittest import TestCase

import database as db
from app import app

TEST_DB_PATH = os.getcwd() + '/test.db'
TEST_CSV_PATH = os.getcwd() + '/csv100rows.csv'


class FlaskTestCase(TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

        db.init(app, TEST_DB_PATH)
        self.client = app.test_client()


class TestFlask(FlaskTestCase):
    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class TestCSVFile(FlaskTestCase):
    def test_load(self):
        # I load a csv in
        with open(TEST_CSV_PATH, 'rb') as data:
            filename = os.path.basename(TEST_CSV_PATH)
            db.CSVFile.load(data, filename)

        csvfile = db.CSVFile.query.one()

        # The csv's filename and encoding is stored with the file
        self.assertEqual(csvfile.filename, filename)
        self.assertEqual(csvfile.encoding, 'utf-8')

        # The csv has 101 rows
        self.assertEqual(len(csvfile), 101)

        # But one of them is missing columns
        self.assertEqual(len(csvfile.unusable()), 1)

        # So I have 100 rows of usable data
        self.assertEqual(len(csvfile.data()), 100)
