from pathlib import Path
from unittest import TestCase

import benford
from benford.app import create_app
from benford.database import db
from benford.models import CSVFile

TEST_DIR = Path().absolute() / 'tests'
FIXTURES_PATH = TEST_DIR / 'cypress/cypress/fixtures'
DB_PATH = TEST_DIR / 'test.db'
CSV_FILES = [
    FIXTURES_PATH / 'test_csv_1.csv',
    FIXTURES_PATH / 'test_csv_2.csv',
    FIXTURES_PATH / 'test_csv_3.csv',
]
DATETIME_FSTRING = '%Y-%m-%dT%H:%M:%S'


def clear():
    CSVFile.query.delete()
    db.session.commit()
    return 'OK', 200


def create_test_app(path):
    app_ = create_app(path)
    app_.add_url_rule('/clear', view_func=clear)
    return app_


class AppTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_test_app(DB_PATH)
        cls.app.config['SERVER_NAME'] = 'localhost'

    def tearDown(self):
        CSVFile.query.delete()
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        del cls.app
        try:
            DB_PATH.unlink()
            Path(str(DB_PATH) + '-journal').unlink()
        except FileNotFoundError:
            pass


class DatabaseTestCase(AppTestCase):
    def setUp(self):
        super().setUp()
        # Make sure the table is empty
        self.assertEqual([], CSVFile.query.all())


if __name__ == '__main__':
    # Run server for Cypress tests
    app = create_test_app(DB_PATH)
    app.run(host='0.0.0.0', port=8000, debug=True)
