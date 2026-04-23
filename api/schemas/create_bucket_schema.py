from marshmallow import Schema, fields, validate


class CreateBucketSchema(Schema):
    """Request body for creating an S3 bucket."""

    name = fields.String(
        required=True,
        validate=validate.Length(min=5),
        metadata={
            "description": "Globally unique S3 bucket name (min 5 chars). "
                           "Must follow S3 naming rules: lowercase, no underscores, 3-63 chars.",
            "example": "my-landing-page-assets",
        },
    )
