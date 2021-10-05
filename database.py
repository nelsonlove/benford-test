import codecs
import csv
import io

import os

import chardet
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init(app, db_path):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join("./", db_path)}'

    db.app = app
    db.init_app(app)
    db.create_all(app=app)


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

    def column(self, i):
        if i >= self.num_cols():
            raise IndexError
        return [row[i] for row in self.dump()]

    def __len__(self):
        return len(self.data)
