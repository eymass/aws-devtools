from marshmallow import Schema, fields, validate


class CreateEnvironmentSchema(Schema):
    application_name = fields.String(required=True, validate=validate.Length(min=3), error_messages={"required": "application_name is required"})
    environment_name = fields.String(required=True, validate=validate.Length(min=3), error_messages={"required": "environment_name is required"})
    description = fields.String(required=True, validate=validate.Length(min=5), error_messages={"required": "description is required"})
    environment_variables = fields.String(required=True, validate=validate.Length(min=5), error_messages={"required": "environment_variables is required"})


class GetEnvironmentStatusSchema(Schema):
    environment_name = fields.Str(required=True)


class DeployEnvironmentSchema(Schema):
    domain_name = fields.Str(required=True)
    contact_info = fields.Str(required=True)
    static_files_bucket = fields.Str(required=True)
    environment_url = fields.Str(required=True)
