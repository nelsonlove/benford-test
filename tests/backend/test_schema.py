from datetime import datetime

from benford.database import db
from benford.models import CSVFile
from benford.schema import CSVSchema, PreviewSchema, AnalysisSchema
from backend.test_base import CSV_FILES, DATETIME_FSTRING, AppTestCase


def supports_collection_only(func):
    def wrapped(self, *args, **kwargs):
        if not self.many:
            msg = 'Skipping'
        else:
            msg = 'Running'
        print(f'{msg} {func.__name__} for {self.schema.__class__.__name__}')
        if not self.many:
            return
        return func(self, *args, **kwargs)

    return wrapped


class SchemaTestCase(AppTestCase):
    cls = None
    object_type = None
    endpoint = None
    many = None
    collection_endpoint = None

    def setUp(self):
        super().setUp()
        for attr in ['cls', 'endpoint', 'object_type', 'many']:
            if getattr(self, attr) is None:
                self.fail(f"Class attribute '{attr}' must be set")

        self.schema = self.cls()
        if self.many and not self.collection_endpoint:
            self.fail("Class attribute 'collection_endpoint' must be set")

        for path in CSV_FILES:
            with open(path, 'rb') as f:
                csvfile = CSVFile(f, path.name)
                db.session.add(csvfile)
        db.session.commit()

    def test_schema_returns_single_object(self):
        """Schema returns data field containing a dict given a single object"""
        with self.app.app_context():
            csvfile = CSVFile.query.first()
            single_object = self.schema.dump(csvfile)
            self.assertTrue(isinstance(single_object['data'], dict))

    def test_single_object_top_level_fields(self):
        """Single objects contain 'data' and 'links' as top-level fields"""
        with self.app.app_context():
            csvfile = CSVFile.query.first()
            single_object = self.schema.dump(csvfile)
            self.assertEqual(['data', 'links'], list(single_object.keys()))

    @supports_collection_only
    def test_collection_top_level_fields(self):
        """Collections contain 'data' and 'links' as top-level fields"""
        with self.app.app_context():
            csvfiles = CSVFile.query.all()
            collection = self.schema.dump(csvfiles, many=True)
            self.assertEqual(['data', 'links'], list(collection.keys()))

    @supports_collection_only
    def test_schema_returns_collection_of_objects(self):
        """Schema returns data field containing a list of dicts given a collection"""
        with self.app.app_context():
            csvfiles = CSVFile.query.all()
            collection = self.schema.dump(csvfiles, many=True)
            self.assertTrue(isinstance(collection['data'], list))
            self.assertTrue(all(
                [isinstance(record, dict) for record in collection['data']]
            ))

    @supports_collection_only
    def test_single_objects_match_records_in_collection(self):
        """Data for single objects matches data returned for collection"""
        with self.app.app_context():
            csvfiles = CSVFile.query.all()
            collection = self.schema.dump(csvfiles, many=True)
            for i, csvfile in enumerate(csvfiles):
                single_object = self.schema.dump(csvfile)
                self.assertEqual(single_object['data'], collection['data'][i])

    def test_id_field(self):
        """A schema object's id field matches its corresponding database record"""
        with self.app.app_context():
            for i, csvfile in enumerate(CSVFile.query.all()):
                single_object = self.schema.dump(csvfile)
            self.assertEqual(str(csvfile.id), single_object['data']['id'])

    def test_single_object_self_link(self):
        """Schema object's links field generates self link"""
        with self.app.app_context():
            csvfile = CSVFile.query.first()
            single_object = self.schema.dump(csvfile)
        self.assertEqual(self.endpoint.format(id=csvfile.id), single_object['links']['self'])

    @supports_collection_only
    def test_collection_self_link(self):
        """Schema object's links field generates self link"""
        with self.app.app_context():
            csvfiles = CSVFile.query.all()
            collection = self.schema.dump(csvfiles, many=True)
        self.assertEqual(self.collection_endpoint, collection['links']['self'])

    def test_type_field(self):
        """Objects have a properly set type field"""
        with self.app.app_context():
            csvfile = CSVFile.query.first()
            single_object = self.schema.dump(csvfile)
        self.assertEqual(self.object_type, single_object['data']['type'])


class TestCSVSchema(SchemaTestCase):
    cls = CSVSchema
    endpoint = 'http://localhost/csv/{id}'
    object_type = 'csv'
    many = True
    collection_endpoint = 'http://localhost/csv'

    def test_filename_attribute(self):
        """A CSVSchema object's filename attribute matches its corresponding database record"""
        with self.app.app_context():
            for i, csvfile in enumerate(CSVFile.query.all()):
                single_object = self.schema.dump(csvfile)
                self.assertEqual(csvfile.filename, single_object['data']['attributes']['filename'])

    def test_date_created_attribute(self):
        """A CSVSchema object's dateCreated attribute matches its corresponding database record"""

        with self.app.app_context():
            for i, csvfile in enumerate(CSVFile.query.all()):
                single_object = self.schema.dump(csvfile)
                date_created_attribute = single_object['data']['attributes']['dateCreated']
                date_created = datetime.strptime(date_created_attribute, DATETIME_FSTRING)
                self.assertEqual(csvfile.date_created, date_created)


class TestPreviewSchema(SchemaTestCase):
    cls = PreviewSchema
    endpoint = 'http://localhost/csv/{id}/preview'
    object_type = 'preview'
    many = False

    def test_num_rows_and_num_discarded(self):
        """Objects contain fields for the total number of
       rows and the number of discarded rows"""
        with self.app.app_context():
            for csvfile in CSVFile.query.all():
                single_object = PreviewSchema().dump(csvfile)
                num_rows = len(csvfile)
                viable_rows = csvfile.viable_rows()
                num_discarded = num_rows - len(viable_rows)
                self.assertEqual(
                    num_rows,
                    single_object['data']['attributes']['numRows']
                )
                self.assertEqual(
                    num_discarded,
                    single_object['data']['attributes']['numDiscarded']
                )

    def test_preview_data(self):
        """Schema objects include preview data"""
        with self.app.app_context():
            for csvfile in CSVFile.query.all():
                single_object = self.schema.dump(csvfile)
                usable_data = csvfile.viable_rows()
                self.assertEqual(
                    usable_data[:6],
                    single_object['data']['attributes']['previewData']
                )

    def test_viable_column_indices(self):
        with self.app.app_context():
            for csvfile in CSVFile.query.all():
                single_object = PreviewSchema().dump(csvfile)
                self.assertEqual(
                    csvfile.viable_columns(),
                    single_object['data']['attributes']['viableColumnIndices']
                )


class TestAnalysisSchema(SchemaTestCase):
    cls = AnalysisSchema
    endpoint = 'http://localhost/csv/{id}/analysis'
    object_type = 'analysis'
    many = False

    def setUp(self):
        super().setUp()
        self.analyses = []
        self.schema_output = []
        with self.app.app_context():
            for csvfile in CSVFile.query.all():
                self.analyses.append(
                    [csvfile.analysis(col) for col in csvfile.viable_columns()]
                )
                self.schema_output.append(self.schema.dump(csvfile))

    def test_name(self):
        for i, analysis_ in enumerate(self.analyses):
            columns = self.schema_output[i]['data']['attributes']['columns']
            for j, col in enumerate(analysis_):
                self.assertEqual(col['name'], columns[j]['name'])

    def test_index(self):
        for i, analysis_ in enumerate(self.analyses):
            columns = self.schema_output[i]['data']['attributes']['columns']
            for j, col in enumerate(analysis_):
                self.assertEqual(col['index'], columns[j]['index'])

    def test_n(self):
        for i, analysis_ in enumerate(self.analyses):
            columns = self.schema_output[i]['data']['attributes']['columns']
            for j, col in enumerate(analysis_):
                self.assertEqual(col['n'], columns[j]['n'])

    def test_expected_distribution(self):
        for i, analysis_ in enumerate(self.analyses):
            columns = self.schema_output[i]['data']['attributes']['columns']
            for j, col in enumerate(analysis_):
                self.assertEqual(col['expectedDistribution'], columns[j]['expectedDistribution'])

    def observed_distribution(self):
        for i, analysis_ in enumerate(self.analyses):
            columns = self.schema_output[i]['data']['attributes']['columns']
            for j, col in enumerate(analysis_):
                self.assertEqual(col['observedDistribution'], columns[j]['observedDistribution'])

    def test_statistic(self):
        for i, analysis_ in enumerate(self.analyses):
            columns = self.schema_output[i]['data']['attributes']['columns']
            for j, col in enumerate(analysis_):
                self.assertEqual(col['testStatistic'], columns[j]['testStatistic'])

    def test_critical_values(self):
        for i, analysis_ in enumerate(self.analyses):
            columns = self.schema_output[i]['data']['attributes']['columns']
            for j, col in enumerate(analysis_):
                self.assertEqual(col['criticalValues'], columns[j]['criticalValues'])

    def test_goodness_of_fit(self):
        for i, analysis_ in enumerate(self.analyses):
            columns = self.schema_output[i]['data']['attributes']['columns']
            for j, col in enumerate(analysis_):
                self.assertEqual(col['goodnessOfFit'], columns[j]['goodnessOfFit'])


del SchemaTestCase
