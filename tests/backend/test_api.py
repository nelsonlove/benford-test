from datetime import datetime

from flask import url_for

from benford.database import db
from benford.models import CSVFile
from backend.test_base import CSV_FILES, AppTestCase, DATETIME_FSTRING


class APITestCase(AppTestCase):
    endpoint = ''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.app.test_client()
        cls.base_url = 'http://localhost'

    def setUp(self):
        super().setUp()

        # Flask should be working
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # Table starts empty
        self.assertEqual(0, len(CSVFile.query.all()))

        for attr in ['endpoint']:
            if not getattr(self, attr):
                self.fail(f"Class attribute '{attr}' must be set")

    def get_response(self, **kwargs):
        endpoint = self.endpoint.format(**kwargs)
        return self.client.get(endpoint)


class TestCSVListEndpoint(APITestCase):
    endpoint = '/csv'

    def setUp(self):
        super().setUp()

        for path in CSV_FILES:
            with open(path, 'rb') as f:
                csvfile = CSVFile(f, path.name)
                db.session.add(csvfile)
        db.session.commit()

        self.response = self.get_response()
        self.data = self.response.get_json()

    def test_response_code(self):
        self.assertEqual(self.get_response().status_code, 200)

    def test_top_level_keys(self):
        self.assertEqual(['data', 'links', 'meta', 'jsonapi'], list(self.data.keys()))

    def test_meta_and_jsonapi_fields(self):
        self.assertEqual({'version': '1.0'}, self.data['jsonapi'])
        self.assertEqual({'count': len(CSVFile.query.all())}, self.data['meta'])

    def test_id_field(self):
        self.assertEqual(
            [str(csvfile.id) for csvfile in CSVFile.query.all()],
            [record['id'] for record in self.data['data']]
        )

    def test_type_field(self):
        for record in self.data['data']:
            self.assertEqual('csv', record['type'])

    def test_filename_attribute(self):
        self.assertEqual(
            [csvfile.filename for csvfile in CSVFile.query.all()],
            [record['attributes']['filename'] for record in self.data['data']]
        )

    def test_date_created_attribute(self):
        self.assertEqual(
            [csvfile.date_created for csvfile in CSVFile.query.all()],
            [datetime.strptime(record['attributes']['dateCreated'],
                               DATETIME_FSTRING) for record in self.data['data']]
        )

    def test_self_link(self):
        with self.app.app_context():
            link = url_for('csv_list')
        self.assertEqual({'self': link}, self.data['links'])

    def test_preview_relationship(self):
        with self.app.app_context():
            self.assertEqual(
                [{'links': {'self': url_for('preview', id=csvfile.id, _external=False)}}
                 for csvfile in CSVFile.query.all()],
                [record['relationships']['preview'] for record in self.data['data']]
            )

    def test_analysis_relationship(self):
        with self.app.app_context():
            self.assertEqual(
                [{'links': {'self': url_for('analysis', id=csvfile.id, _external=False)}}
                 for csvfile in CSVFile.query.all()],
                [record['relationships']['analysis'] for record in self.data['data']]
            )


class TestUploadEndpoint(APITestCase):
    endpoint = '/upload'

    def test_upload_with_no_file(self):
        # 422 indicates unsuccessful upload
        response = self.client.post('/upload')
        self.assertEqual(response.status_code, 422)

    def test_upload_one(self):
        # Table has no rows yet
        self.assertEqual(0, len(CSVFile.query.all()))

        # I upload a csv
        with open(CSV_FILES[-1], 'rb') as data:
            response = self.client.post('/upload', data={
                "csv": (data, CSV_FILES[-1].name)
            })

        # 201 indicates successful upload
        self.assertEqual(response.status_code, 201)

        # Table now has a single row
        self.assertEqual(1, len(CSVFile.query.all()))

        csvfile = CSVFile.query.one()
        data = response.get_json()

        # Our response should be the csv_detail view for our uploaded file
        with self.app.app_context():
            self.assertEqual(
                url_for('csv_detail', id=csvfile.id, _external=False),
                response.get_json()['links']['self']
            )
        self.assertEqual(CSV_FILES[-1].name, data['data']['attributes']['filename'])

    def test_upload_fails_on_existing_filename(self):
        # I upload a csv
        with open(CSV_FILES[-1], 'rb') as data:
            response = self.client.post('/upload', data={
                "csv": (data, CSV_FILES[-1].name)
            })

        # 201 indicates successful upload
        self.assertEqual(response.status_code, 201)

        # Table now has a single row
        self.assertEqual(1, len(CSVFile.query.all()))

        # I upload the same csv again
        with open(CSV_FILES[-1], 'rb') as data:
            response = self.client.post('/upload', data={
                "csv": (data, CSV_FILES[-1].name)
            })

        # 422 indicates unsuccessful upload
        self.assertEqual(response.status_code, 422)

        # Table still has a single row
        self.assertEqual(1, len(CSVFile.query.all()))

    def test_upload_multiple(self):
        for path in CSV_FILES[:2]:
            with open(path, 'rb') as data:
                response = self.client.post('/upload', data={
                    "csv": (data, path.name)
                })

        # Table now has two rows
        self.assertEqual(2, len(CSVFile.query.all()))


class TestCSVDetailEndpoint(APITestCase):
    endpoint = '/csv/{id}'

    def setUp(self):
        super().setUp()

        path = CSV_FILES[0]
        with open(path, 'rb') as f:
            csvfile = CSVFile(f, path.name)
            db.session.add(csvfile)
        db.session.commit()

        self.csvfile = CSVFile.query.all()[0]
        self.response = self.get_response(id=self.csvfile.id)
        self.data = self.response.get_json()

    def test_response_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_top_level_keys(self):
        self.assertEqual(['data', 'links', 'jsonapi'], list(self.data.keys()))

    def test_jsonapi_field(self):
        self.assertEqual({'version': '1.0'}, self.data['jsonapi'])

    def test_id_field(self):
        self.assertEqual(str(self.csvfile.id), self.data['data']['id'])

    def test_type_field(self):
        self.assertEqual('csv', self.data['data']['type'])

    def test_filename_attribute(self):
        self.assertEqual(self.csvfile.filename, self.data['data']['attributes']['filename'])

    def test_date_created_attribute(self):
        self.assertEqual(self.csvfile.date_created,
                         datetime.strptime(self.data['data']['attributes']['dateCreated'],
                                           DATETIME_FSTRING))

    def test_self_link(self):
        with self.app.app_context():
            link = url_for('csv_detail', id=self.csvfile.id, _external=False)
        self.assertEqual({'self': link}, self.data['links'])

    def test_preview_relationship(self):
        with self.app.app_context():
            self.assertEqual(
                {'links': {'self': url_for('preview', id=self.csvfile.id, _external=False)}},
                self.data['data']['relationships']['preview']
            )

    def test_analysis_relationship(self):
        with self.app.app_context():
            self.assertEqual(
                {'links': {'self': url_for('analysis', id=self.csvfile.id, _external=False)}},
                self.data['data']['relationships']['analysis']
            )


class TestPreviewEndpoint(APITestCase):
    endpoint = '/csv/{id}/preview'

    def setUp(self):
        super().setUp()

        path = CSV_FILES[0]
        with open(path, 'rb') as f:
            csvfile = CSVFile(f, path.name)
            db.session.add(csvfile)
        db.session.commit()

        self.csvfile = CSVFile.query.all()[0]
        self.response = self.get_response(id=self.csvfile.id)
        self.data = self.response.get_json()

    def test_response_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_top_level_keys(self):
        self.assertEqual(['data', 'links', 'jsonapi'], list(self.data.keys()))

    def test_jsonapi_field(self):
        self.assertEqual({'version': '1.0'}, self.data['jsonapi'])

    def test_id_field(self):
        self.assertEqual(str(self.csvfile.id), self.data['data']['id'])

    def test_type_field(self):
        self.assertEqual('preview', self.data['data']['type'])

    def test_filename_attribute(self):
        self.assertEqual(self.csvfile.filename,
                         self.data['data']['attributes']['filename'])

    def test_num_rows(self):
        self.assertEqual(self.csvfile.preview()['numRows'],
                         self.data['data']['attributes']['numRows'])

    def test_num_discarded(self):
        self.assertEqual(self.csvfile.preview()['numDiscarded'],
                         self.data['data']['attributes']['numDiscarded'])

    def test_preview_data(self):
        self.assertEqual(self.csvfile.preview()['previewData'],
                         self.data['data']['attributes']['previewData'])

    def test_viable_column_indices(self):
        self.assertEqual(self.csvfile.preview()['viableColumnIndices'],
                         self.data['data']['attributes']['viableColumnIndices'])

    def test_csv_relationship(self):
        with self.app.app_context():
            self.assertEqual(
                {'links': {'self': url_for('csv_detail', id=self.csvfile.id, _external=False)}},
                self.data['data']['relationships']['csv']
            )


class TestAnalysisEndpoint(APITestCase):
    endpoint = '/csv/{id}/analysis'

    def setUp(self):
        super().setUp()

        path = CSV_FILES[0]
        with open(path, 'rb') as f:
            csvfile = CSVFile(f, path.name)
            db.session.add(csvfile)
        db.session.commit()

        self.csvfile = CSVFile.query.all()[0]
        self.response = self.get_response(id=self.csvfile.id)
        self.data = self.response.get_json()

    def test_response_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_top_level_keys(self):
        self.assertEqual(['data', 'links', 'jsonapi'], list(self.data.keys()))

    def test_jsonapi_field(self):
        self.assertEqual({'version': '1.0'}, self.data['jsonapi'])

    def test_id_field(self):
        self.assertEqual(str(self.csvfile.id), self.data['data']['id'])

    def test_type_field(self):
        self.assertEqual('analysis', self.data['data']['type'])

    def test_name(self):
        for i, col in enumerate(self.csvfile.viable_columns()):
            self.assertEqual(
                self.csvfile.analysis(col)['name'],
                self.data['data']['attributes']['columns'][i]['name']
            )

    def test_index(self):
        for i, col in enumerate(self.csvfile.viable_columns()):
            self.assertEqual(
                self.csvfile.analysis(col)['index'],
                self.data['data']['attributes']['columns'][i]['index']
            )

    def test_n(self):
        for i, col in enumerate(self.csvfile.viable_columns()):
            self.assertEqual(
                self.csvfile.analysis(col)['n'],
                self.data['data']['attributes']['columns'][i]['n']
            )

    def test_expected_distribution(self):
        for i, col in enumerate(self.csvfile.viable_columns()):
            self.assertEqual(
                self.csvfile.analysis(col)['expectedDistribution'],
                self.data['data']['attributes']['columns'][i]['expectedDistribution']
            )

    def observed_distribution(self):
        for i, col in enumerate(self.csvfile.viable_columns()):
            self.assertEqual(
                self.csvfile.analysis(col)['observedDistribution'],
                self.data['data']['attributes']['columns'][i]['observedDistribution']
            )

    def test_statistic(self):
        for i, col in enumerate(self.csvfile.viable_columns()):
            self.assertEqual(
                self.csvfile.analysis(col)['testStatistic'],
                self.data['data']['attributes']['columns'][i]['testStatistic']
            )

    def test_critical_values(self):
        for i, col in enumerate(self.csvfile.viable_columns()):
            self.assertEqual(
                self.csvfile.analysis(col)['criticalValues'],
                self.data['data']['attributes']['columns'][i]['criticalValues']
            )

    def test_goodness_of_fit(self):
        for i, col in enumerate(self.csvfile.viable_columns()):
            self.assertEqual(
                self.csvfile.analysis(col)['goodnessOfFit'],
                self.data['data']['attributes']['columns'][i]['goodnessOfFit']
            )


del APITestCase
