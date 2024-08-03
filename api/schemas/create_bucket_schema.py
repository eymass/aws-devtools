from marshmallow import Schema, fields, validate


class CreateBucketSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=5), error_messages={"required": "name is required"})

