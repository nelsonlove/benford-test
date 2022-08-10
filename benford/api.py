from flask_rest_jsonapi import ResourceList, ResourceDetail
from marshmallow import post_dump
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Schema, Relationship

from .models import CSVFile, db
from .util import underscore_to_camel


class CSVSchema(Schema):
    class Meta:
        type_ = 'csv'
        self_view = 'csv_detail'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'csv_list'
        inflect = underscore_to_camel

    id = fields.Integer(as_string=True, dump_only=True)
    filename = fields.String(unique=True, nullable=False)
    date_created = fields.DateTime(dump_only=True)
    preview = Relationship(
        self_view='preview',
        self_view_kwargs={'id': '<id>'},
        schema='PreviewSchema',
        type_='preview',
    )
    analysis = Relationship(
        self_view='analysis',
        self_view_kwargs={'id': '<id>'},
        schema='AnalysisSchema',
        type_='analysis'
    )


class CSVDetail(ResourceDetail):
    schema = CSVSchema
    data_layer = {
        'session': db.session,
        'model': CSVFile
    }


class CSVList(ResourceList):
    schema = CSVSchema
    data_layer = {
        'session': db.session,
        'model': CSVFile,
    }


class PreviewSchema(Schema):
    class Meta:
        type_ = 'preview'
        self_view = 'preview'
        self_view_kwargs = {'id': '<id>'}
        inflect = underscore_to_camel

    id = fields.Integer(as_string=True, dump_only=True)
    filename = fields.String(unique=True, nullable=False)
    csv = Relationship(
        self_view='csv_detail',
        self_view_kwargs={'id': '<id>'},
        schema='CSVSchema',
        type_='csv'
    )
    num_rows = fields.Integer(as_string=True, dump_only=True)
    num_discarded = fields.Integer(as_string=True, dump_only=True)
    preview_data = fields.String(dump_only=True)
    viable_column_indices = fields.List(fields.Integer, dump_only=True)

    @post_dump(pass_many=False, pass_original=True)
    def add_preview_fields(self, data, csvfile, **kwargs):
        for key, value in csvfile.preview().items():
            data[key] = value
        return data


class CSVPreview(ResourceDetail):
    schema = PreviewSchema
    data_layer = {
        'session': db.session,
        'model': CSVFile
    }


class ColumnSchema(Schema):
    class Meta:
        type_ = 'column'
        self_view = 'column'
        self_view_kwargs = {'id': '<id>', 'col': '<col>'}
        many = True
        inflect = underscore_to_camel

    name = fields.String(dump_only=True)
    index = fields.Integer(as_string=True, dump_only=True)
    n = fields.Integer(as_string=True, dump_only=True)
    expected_distribution = fields.List(fields.Float, dump_only=True)
    observed_distribution = fields.List(fields.Integer, dump_only=True)
    test_statistic = fields.Float(dump_only=True)
    critical_values = fields.List(fields.Float, dump_only=True)
    goodness_of_fit = fields.List(fields.Boolean, dump_only=True)


class AnalysisSchema(Schema):
    class Meta:
        type_ = 'analysis'
        self_view = 'analysis'
        self_view_kwargs = {'id': '<id>'}
        inflect = underscore_to_camel

    id = fields.Integer(as_string=True, dump_only=True)
    filename = fields.String(unique=True, nullable=False)
    csv = Relationship(
        self_view='csv_detail',
        self_view_kwargs={'id': '<id>'},
        schema='CSVSchema',
        type_='csv'
    )
    columns = fields.Nested(ColumnSchema)

    @post_dump(pass_many=False, pass_original=True)
    def add_analysis_fields(self, data, csvfile, **kwargs):
        analyses = []

        for column_index in csvfile.viable_columns():
            analyses.append(csvfile.analysis(column_index))

        data['columns'] = analyses
        return data


class CSVAnalysis(ResourceDetail):
    schema = AnalysisSchema
    data_layer = {
        'session': db.session,
        'model': CSVFile,
    }
