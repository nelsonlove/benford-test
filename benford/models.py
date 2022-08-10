import codecs
import csv
import io
import itertools

import chardet
from flask_sqlalchemy import SQLAlchemy

from benford import util

db = SQLAlchemy()


class CSVFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.now())
    filename = db.Column(db.String(120), unique=True, nullable=False)
    file = db.Column(db.LargeBinary, nullable=False)
    encoding = db.Column(db.String(32), nullable=False)

    @classmethod
    def get_encoding(cls, data):
        # Detect encoding from sample
        sample = data.read(10000)
        data.seek(0)
        return chardet.detect(sample)['encoding']

    def __init__(self, data, filename):
        file = data.read()
        data.seek(0)
        super().__init__(
            filename=filename,
            file=file,
            encoding=self.get_encoding(data)
        )

    def reader(self):
        # Get dialect first
        file = io.BytesIO(self.file)
        sample = file.read(1024).decode(self.encoding)
        file.seek(0)
        dialect = csv.Sniffer().sniff(sample)

        data_iterator = codecs.iterdecode(file, self.encoding)
        return csv.reader(data_iterator, dialect)

    def dump(self, start=0, end=None):
        return itertools.islice(self.reader(), start, end)

    def viable_rows(self):
        data = list(self.dump())
        return [row for row in data if len(row) == len(data[0])]

    def __len__(self):
        return len(list(self.dump()))

    def viable_columns(self):
        def is_numeric_or_blank(x):
            # We can skip blanks later, for now we just want to see if the parser breaks for other reasons
            if not x:
                return True
            try:
                util.parse_numeric(x)
            except ValueError:
                return False
            return True

        data = self.viable_rows()
        num_columns = len(data[0])
        viable_columns = []

        for i in range(num_columns):
            column = [row[i] for row in data]
            # Start at col[1:] because we don't want to count possible headers
            if all(is_numeric_or_blank(x) for x in column[1:]):
                viable_columns.append(i)

        return viable_columns

    def preview(self):
        viable_rows = self.viable_rows()
        num_rows = len(self)
        num_preview_rows = min(len(viable_rows), 6)

        return {
            'numRows': num_rows,
            'numDiscarded': num_rows - len(viable_rows),
            'previewData': viable_rows[:num_preview_rows],
            'viableColumnIndices': self.viable_columns()
        }

    def analysis(self, column_index):
        viable_rows = self.viable_rows()
        column = [row[column_index] for row in viable_rows]
        data = util.clean_data(column)
        expected = util.expected_distribution(len(data))
        observed = util.observed_distribution(data)

        return {
            'name': viable_rows[0][column_index],
            'index': column_index,
            'n': len(data),
            'expectedDistribution': expected,
            'observedDistribution': observed,
            'testStatistic': util.sum_chi_squares(expected, observed),
            'criticalValues': util.CRITICAL_VALUES,
            'goodnessOfFit': util.goodness_of_fit(expected, observed)
        }
