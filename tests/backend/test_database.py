import csv
import io
import itertools
from time import sleep

import chardet
from sqlalchemy.exc import IntegrityError

from benford import analysis
from benford.database import db
from benford.models import CSVFile
from backend.test_base import CSV_FILES, DatabaseTestCase


class TestDatabase(DatabaseTestCase):
    def test_sqlalchemy_registers_csvfile_model(self):
        """The create_app function creates a SQLAlchemy instance with the registered model"""
        models = [mapper.class_ for mapper in db.Model.registry.mappers]
        self.assertEqual([CSVFile], models)

    def test_create_and_retrieve_row(self):
        """A new row can be added to the table and queried/retrieved"""
        with open(CSV_FILES[0], 'rb') as f:
            csvfile = CSVFile(f, CSV_FILES[0].name)
            db.session.add(csvfile)
        db.session.commit()
        rows = CSVFile.query.all()
        self.assertEqual(1, len(rows))
        self.assertEqual([CSVFile], [type(row) for row in rows])

    def test_remove_row(self):
        """A row can be removed from the table"""
        for path in CSV_FILES:
            with open(path, 'rb') as f:
                csvfile = CSVFile(f, path.name)
                db.session.add(csvfile)
        db.session.commit()
        self.assertEqual(3, len(CSVFile.query.all()))
        CSVFile.query.filter_by(id=1).delete()
        db.session.commit()
        self.assertEqual(2, len(CSVFile.query.all()))


class TestCSVFile(DatabaseTestCase):
    def setUp(self):
        for path in CSV_FILES:
            with open(path, 'rb') as f:
                csvfile = CSVFile(f, path.name)
                db.session.add(csvfile)
                sleep(0.01)  # To test date_created column we need a delay
        db.session.commit()

    def test_id_column(self):
        """ID column autoincrements when new records are added"""
        self.assertEqual([1, 2, 3], [row.id for row in CSVFile.query.all()])

    def test_filename_column(self):
        """filename column populates with name of file"""
        self.assertEqual([
            'test_csv_1.csv',
            'test_csv_2.csv',
            'test_csv_3.csv',
        ], [row.filename for row in CSVFile.query.all()])

    def test_unique_filename_constraint(self):
        """Rows are required to have unique filenames"""
        with open(CSV_FILES[2], 'rb') as f:
            csvfile = CSVFile(f, CSV_FILES[2].name)
            db.session.add(csvfile)
            self.assertRaises(IntegrityError, db.session.commit)
        db.session.rollback()

    def test_date_created_column(self):
        """date_created column is populated with DateTime on row creation"""

        # Make sure that we can sort
        dates_created = [row.date_created for row in CSVFile.query.all()]
        self.assertGreaterEqual(dates_created[0], dates_created[1])
        self.assertGreaterEqual(dates_created[1], dates_created[2])

        # We choose a file and delete the corresponding row from the table
        file_to_delete = CSV_FILES[1]
        row_to_delete = CSVFile.query.filter_by(id=2).one()
        self.assertEqual(file_to_delete.name, row_to_delete.filename)
        CSVFile.query.filter_by(id=row_to_delete.id).delete()
        db.session.commit()

        # We should have two rows now
        self.assertEqual(2, len(CSVFile.query.all()))

        # And add the file back
        with open(file_to_delete, 'rb') as f:
            csvfile = CSVFile(f, file_to_delete.name)
            db.session.add(csvfile)
        db.session.commit()

        # We should have all three files back now, but if we sort
        # by date_created the order should be different than our CSV_FILES list
        rows_sorted_by_date_created = CSVFile.query.order_by(CSVFile.date_created).all()
        self.assertEqual([
            CSV_FILES[0].name,
            CSV_FILES[2].name,
            CSV_FILES[1].name,
        ], [row.filename for row in rows_sorted_by_date_created])

    def test_read_bytes(self):
        """Can read a byte stream from the file column that matches the file"""
        for path in CSV_FILES:
            row = CSVFile.query.filter_by(filename=path.name).one()
            with open(path, 'rb') as f:
                self.assertEqual(f.read(), row.file)

    def test_detect_encoding(self):
        """Column populates with detected encoding of .csv file"""
        expected_encodings = [
            'ascii',
            'utf-8',
            'ascii',
        ]
        for i, path in enumerate(CSV_FILES):
            with open(path, 'rb') as fixture:
                fixture_sample = fixture.read(10000)
                fixture_encoding = chardet.detect(fixture_sample)['encoding']
            self.assertEqual(fixture_encoding, expected_encodings[i])

            db_row = CSVFile.query.filter_by(filename=path.name).one()
            db_row_encoding = CSVFile.get_encoding(io.BytesIO(db_row.file))
            self.assertEqual(fixture_encoding, db_row_encoding)

    def test_reader(self):
        """CSVFile.reader() method returns a csv reader from file data"""
        for path in CSV_FILES:
            row = CSVFile.query.filter_by(filename=path.name).one()
            with open(path) as f:
                db_row_reader = row.reader()
                for row in csv.reader(f):
                    self.assertEqual(row, next(db_row_reader))

    def test_dump(self):
        """CSVFile.dump() method accepts an optional start and stop,
        returning a list of rows from file data"""
        for path in CSV_FILES:
            row = CSVFile.query.filter_by(filename=path.name).one()
            with open(path) as f:
                first_5_csv_rows = itertools.islice(csv.reader(f), 0, 5)
                self.assertEqual(
                    [row for row in first_5_csv_rows],
                    [row for row in row.dump(0, 5)]
                )
                f.seek(0)
                all_rows = itertools.islice(csv.reader(f), 0, None)
                self.assertEqual(
                    [row for row in all_rows],
                    [row for row in row.dump()]
                )

    def test_viable_rows(self):
        expected_viable_rows = [101, 100, 101]
        for i, csvfile in enumerate(CSVFile.query.all()):
            data = list(csvfile.dump())
            viable_rows = csvfile.viable_rows()
            self.assertTrue(all(len(row) == len(data[0]) for row in viable_rows))
            self.assertEqual(expected_viable_rows[i], len(csvfile.viable_rows()))

    def test_viable_columns(self):
        csvfile = CSVFile.query.all()[1]

        # This csv has no headers but the columns look like this:
        #
        # 1,"Eldon Base for stackable storage shelf, platinum",
        # Muhammed MacIntyre,3,-213.25,38.94,35,Nunavut,Storage & Organization,0.8

        # So we might surmise that columns 0, 3, 4, 5, 6, and 9 are viable
        self.assertEqual([0, 3, 4, 5, 6, 9], csvfile.viable_columns())

        # Let's try it on all of them
        expected_viable_columns = [
            [0, 3, 7, 8],
            [0, 3, 4, 5, 6, 9],
            [0, 3, 7, 8]
        ]
        for i, csvfile in enumerate(CSVFile.query.all()):
            self.assertEqual(expected_viable_columns[i], csvfile.viable_columns())

    def test_row_counts(self):
        expected_num_rows = [103, 101, 102]
        expected_num_discarded = [2, 1, 1]
        for i, csvfile in enumerate(CSVFile.query.all()):
            self.assertEqual(
                expected_num_rows[i],
                csvfile.preview()['numRows']
            )
            self.assertEqual(
                expected_num_discarded[i],
                csvfile.preview()['numDiscarded']
            )

    def test_preview_data(self):
        for i, csvfile in enumerate(CSVFile.query.all()):
            with open(CSV_FILES[i]) as f:
                reader = csv.reader(f)
                rows = list(reader)[:6]
            self.assertEqual(
                rows,
                csvfile.preview()['previewData']
            )

    def test_n(self):
        for i, csvfile in enumerate(CSVFile.query.all()):
            for j, col in enumerate(csvfile.viable_columns()):
                data = analysis.clean_data([row[col] for row in csvfile.viable_rows()])
                self.assertEqual(
                    len(data),
                    csvfile.analysis(col)['n']
                )

    def test_expected_distribution(self):
        for i, csvfile in enumerate(CSVFile.query.all()):
            for j, col in enumerate(csvfile.viable_columns()):
                data = analysis.clean_data([row[col] for row in csvfile.viable_rows()])
                expected_distribution = analysis.expected_distribution(len(data))

                self.assertEqual(
                    expected_distribution,
                    csvfile.analysis(col)['expectedDistribution']
                )

    def test_observed_distribution(self):
        for i, csvfile in enumerate(CSVFile.query.all()):
            for j, col in enumerate(csvfile.viable_columns()):
                data = analysis.clean_data([row[col] for row in csvfile.viable_rows()])
                observed_distribution = analysis.observed_distribution(data)

                self.assertEqual(
                    observed_distribution,
                    csvfile.analysis(col)['observedDistribution']
                )

    def test_sum_chi_square(self):
        for i, csvfile in enumerate(CSVFile.query.all()):
            for j, col in enumerate(csvfile.viable_columns()):
                data = analysis.clean_data([row[col] for row in csvfile.viable_rows()])
                expected_distribution = analysis.expected_distribution(len(data))
                observed_distribution = analysis.observed_distribution(data)
                test_statistic = analysis.sum_chi_squares(expected_distribution, observed_distribution)

                self.assertEqual(
                    test_statistic,
                    csvfile.analysis(col)['testStatistic']
                )

    def test_goodness_of_fit(self):
        for i, csvfile in enumerate(CSVFile.query.all()):
            for j, col in enumerate(csvfile.viable_columns()):
                data = analysis.clean_data([row[col] for row in csvfile.viable_rows()])
                expected_distribution = analysis.expected_distribution(len(data))
                observed_distribution = analysis.observed_distribution(data)
                goodness_of_fit = analysis.goodness_of_fit(expected_distribution, observed_distribution)

                self.assertEqual(
                    goodness_of_fit,
                    csvfile.analysis(col)['goodnessOfFit']
                )