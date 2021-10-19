import codecs
import csv
import io
import itertools

import chardet
from flask_sqlalchemy import SQLAlchemy

from benford.analysis import parse_numeric

db = SQLAlchemy()


class CSVFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.now())
    filename = db.Column(db.String(120), unique=True, nullable=False)
    file = db.Column(db.LargeBinary, nullable=False)
    encoding = db.Column(db.String(32), nullable=False)

    @classmethod
    def load(cls, data, filename):
        # Detect encoding from sample
        sample = data.read(10000)
        encoding = chardet.detect(sample)['encoding']
        data.seek(0)

        csvfile = cls(
            filename=filename,
            file=data.read(),
            encoding=encoding
        )
        db.session.add(csvfile)
        db.session.commit()

        return csvfile

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

    def num_columns(self):
        first_row = next(self.dump(end=1))
        return len(first_row)

    def data(self):
        num_cols = self.num_columns()
        return [row for row in self.dump() if len(row) == num_cols]

    def unusable(self):
        num_cols = self.num_columns()
        return [row for row in self.dump() if len(row) != num_cols]

    @property
    def viable_columns(self):
        def is_numeric_or_blank(x):
            # We can skip blanks later, for now we just want to see if the parser breaks for other reasons
            if not x:
                return True
            try:
                parse_numeric(x)
            except ValueError:
                return False
            return True

        viable_columns = []

        for i in range(self.num_columns()):
            column = self.column(i)
            # Start at col[1:] because we don't want to count possible headers
            if all(is_numeric_or_blank(x) for x in column[1:]):
                viable_columns.append((i, column[0]))

        return viable_columns

    def column(self, i):
        if i >= self.num_columns():
            raise IndexError
        return [row[i] for row in self.data()]

    def __len__(self):
        return len([_ for _ in self.reader()])
