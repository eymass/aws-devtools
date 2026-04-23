from marshmallow import Schema, fields, validate

_CONTACT_INFO_EXAMPLE = {
    "FirstName": "Jane",
    "LastName": "Doe",
    "ContactType": "PERSON",
    "AddressLine1": "123 Main St",
    "City": "Seattle",
    "State": "WA",
    "CountryCode": "US",
    "ZipCode": "98101",
    "PhoneNumber": "+1.2065550100",
    "Email": "jane.doe@example.com",
}


class CreateEnvironmentSchema(Schema):
    """Request body for creating an ElasticBeanstalk environment."""

    application_name = fields.String(
        required=True,
        validate=validate.Length(min=3),
        metadata={
            "description": "Name of the ElasticBeanstalk application to attach the environment to.",
            "example": "my-web-app",
        },
    )
    environment_name = fields.String(
        required=True,
        validate=validate.Length(min=3),
        metadata={
            "description": "Unique name for the new environment within the application.",
            "example": "my-web-app-prod",
        },
    )
    description = fields.String(
        required=False,
        validate=validate.Length(min=5),
        metadata={
            "description": "Human-readable description of the environment (min 5 chars).",
            "example": "Production environment for the web app",
        },
    )
    environment_variables = fields.Dict(
        required=False,
        keys=fields.Str(),
        values=fields.Str(),
        metadata={
            "description": "Key-value pairs injected as environment variables into the application.",
            "example": {"NODE_ENV": "production", "LOG_LEVEL": "info"},
        },
    )
    stack_name = fields.String(
        required=False,
        validate=validate.Length(min=5),
        metadata={
            "description": "ElasticBeanstalk solution stack name (platform version). "
                           "Mutually exclusive with template_name.",
            "example": "64bit Amazon Linux 2023 v6.1.6 running Node.js 20",
        },
    )
    template_name = fields.String(
        required=False,
        validate=validate.Length(min=5),
        metadata={
            "description": "Saved configuration template to use instead of stack_name.",
            "example": "my-web-app-template-v2",
        },
    )


class GetEnvironmentStatusSchema(Schema):
    """Query parameters for environment health/status endpoints."""

    environment_name = fields.Str(
        required=False,
        metadata={
            "description": "Name of the ElasticBeanstalk environment to inspect.",
            "example": "my-web-app-prod",
        },
    )


class CreateConfigurationTemplateSchema(Schema):
    """Request body for creating an ElasticBeanstalk saved configuration template."""

    application_name = fields.Str(
        required=True,
        metadata={
            "description": "Application from which to snapshot the configuration.",
            "example": "my-web-app",
        },
    )
    environment_name = fields.Str(
        required=True,
        metadata={
            "description": "Environment whose current settings will be saved as a template.",
            "example": "my-web-app-prod",
        },
    )


class RemoveConfigurationTemplateSchema(Schema):
    """Request body for deleting a saved configuration template."""

    application_name = fields.Str(
        required=True,
        metadata={
            "description": "Application that owns the template.",
            "example": "my-web-app",
        },
    )
    template_name = fields.Str(
        required=True,
        metadata={
            "description": "Name of the configuration template to delete.",
            "example": "my-web-app-template-v2",
        },
    )


class RestartSchema(Schema):
    """Request body for restart or rebuild operations."""

    environment_name = fields.Str(
        required=True,
        metadata={
            "description": "Name of the ElasticBeanstalk environment to restart or rebuild.",
            "example": "my-web-app-prod",
        },
    )


class DeployEnvironmentSchema(Schema):
    """Request body for deploying a domain + CloudFront in front of an ElasticBeanstalk environment."""

    domain_name = fields.Str(
        required=True,
        metadata={
            "description": "Apex domain name to register and point to the CloudFront distribution.",
            "example": "myapp.example.com",
        },
    )
    contact_info = fields.Dict(
        required=True,
        metadata={
            "description": "AWS Route 53 Domains registrant contact object. "
                           "Required fields: FirstName, LastName, ContactType, AddressLine1, "
                           "City, State, CountryCode, ZipCode, PhoneNumber, Email.",
            "example": _CONTACT_INFO_EXAMPLE,
        },
    )
    static_files_bucket = fields.Str(
        required=True,
        metadata={
            "description": "Name of the S3 bucket that holds static assets (CSS, JS, images). "
                           "CloudFront will route /static/* requests here.",
            "example": "my-app-static-assets",
        },
    )
    environment_url = fields.Str(
        required=True,
        metadata={
            "description": "ElasticBeanstalk environment URL used as the CloudFront default origin.",
            "example": "http://my-web-app-prod.us-east-1.elasticbeanstalk.com",
        },
    )
    purchase_domain = fields.Bool(
        required=False,
        load_default=True,
        metadata={
            "description": "Set to false to skip Route 53 domain purchase "
                           "(use when the domain is already registered).",
            "example": True,
        },
    )


ROUTING_TYPES = ('geo', 'ab', 'utm', 'ip', 'device', 'path', 'composite')


class DeployStaticSchema(Schema):
    """Request body for deploying a domain + CloudFront in front of an S3 static-website URL."""

    domain_name = fields.Str(
        required=True,
        metadata={
            "description": "Apex domain to register and point at the CloudFront distribution.",
            "example": "landing.example.com",
        },
    )
    contact_info = fields.Dict(
        required=True,
        metadata={
            "description": "AWS Route 53 Domains registrant contact object. "
                           "Required fields: FirstName, LastName, ContactType, AddressLine1, "
                           "City, State, CountryCode, ZipCode, PhoneNumber, Email.",
            "example": _CONTACT_INFO_EXAMPLE,
        },
    )
    s3_website_url = fields.Str(
        required=True,
        metadata={
            "description": "S3 static-website endpoint URL (the bucket's website hosting URL, "
                           "not the S3 REST API endpoint).",
            "example": "http://my-landing-page.s3-website-us-east-1.amazonaws.com",
        },
    )
    purchase_domain = fields.Bool(
        load_default=True,
        metadata={
            "description": "Set to false to skip Route 53 domain purchase "
                           "(use when the domain is already registered).",
            "example": True,
        },
    )
    enable_viewer_request = fields.Bool(
        load_default=False,
        metadata={
            "description": "Attach a CloudFront Function for viewer-request routing logic. "
                           "Requires routing_type or viewer_request_function_code.",
            "example": True,
        },
    )
    routing_type = fields.Str(
        load_default=None,
        validate=validate.OneOf(ROUTING_TYPES),
        metadata={
            "description": "Built-in routing template to apply when enable_viewer_request=true. "
                           "One of: geo, ab, utm, ip, device, path, composite. "
                           "Mutually exclusive with viewer_request_function_code.",
            "example": "geo",
        },
    )
    viewer_request_function_code = fields.Str(
        load_default=None,
        metadata={
            "description": "Raw CloudFront Functions JavaScript source for a fully custom "
                           "viewer-request handler. Mutually exclusive with routing_type.",
            "example": None,
        },
    )
    routing_config = fields.Dict(
        load_default=None,
        metadata={
            "description": "Template-specific configuration passed to the built-in routing function "
                           "(e.g. country-to-variant mappings for geo routing).",
            "example": {"US": "/en/", "DE": "/de/", "default": "/en/"},
        },
    )
    viewer_request_function_name = fields.Str(
        load_default=None,
        metadata={
            "description": "Name to assign the CloudFront Function. "
                           "Auto-generated from domain_name if omitted.",
            "example": "landing-example-com-viewer-request",
        },
    )
