from marshmallow import Schema, fields, validate


class CreateEnvironmentSchema(Schema):
    application_name = fields.String(required=True, validate=validate.Length(min=3), error_messages={"required": "application_name is required"})
    environment_name = fields.String(required=True, validate=validate.Length(min=3), error_messages={"required": "environment_name is required"})
    description = fields.String(required=False, validate=validate.Length(min=5), error_messages={"required": "description is required"})
    environment_variables = fields.Dict(required=False)
    stack_name = fields.String(required=False, validate=validate.Length(min=5), error_messages={"required": "stack_name is required"})
    template_name = fields.String(required=False, validate=validate.Length(min=5), error_messages={"required": "template_name is required"})


class GetEnvironmentStatusSchema(Schema):
    environment_name = fields.Str(required=True)


class CreateConfigurationTemplateSchema(Schema):
    application_name = fields.Str(required=True)


class DeployEnvironmentSchema(Schema):
    domain_name = fields.Str(required=True)
    contact_info = fields.Str(required=True)
    static_files_bucket = fields.Str(required=True)
    environment_url = fields.Str(required=True)
