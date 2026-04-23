from flask import request
from flask_smorest import Blueprint, abort
from flask import jsonify
from marshmallow import ValidationError

from exceptions.already_exists_exceptions import AlreadyExists
from .schemas.create_bucket_schema import CreateBucketSchema
from .schemas.response_schemas import BucketResponseSchema, ErrorResponseSchema
from s3_manager import S3Manager

buckets_bp = Blueprint(
    'buckets',
    __name__,
    description="Manage S3 buckets used to host static assets for deployments.",
)


@buckets_bp.route('/', methods=['POST'])
@buckets_bp.arguments(CreateBucketSchema)
@buckets_bp.response(201, BucketResponseSchema, description="Bucket created successfully.")
def handle_create_bucket(args):
    """Create a new S3 bucket.

    Creates an S3 bucket in the configured AWS region. The bucket name must be
    globally unique across all AWS accounts. Bucket names must follow
    [S3 naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html):
    lowercase letters, numbers, and hyphens only; 3–63 characters.
    """
    try:
        result = S3Manager().create_bucket(bucket_name=args['name'])
        print(result)
        return jsonify(result), 201
    except AlreadyExists as e:
        print(e)
        return abort(409, message={"error": str(e)})
    except Exception as e:
        print(e)
        return abort(500, message={"error": str(e)})


@buckets_bp.route('/', methods=['DELETE'])
@buckets_bp.response(204, description="Bucket deleted successfully.")
def delete_bucket():
    """Delete an S3 bucket.

    Permanently deletes the specified bucket. The bucket must be empty before
    it can be deleted.

    **Query parameters:**

    | Parameter | Type   | Required | Description                      |
    |-----------|--------|----------|----------------------------------|
    | name      | string | Yes      | Name of the bucket to delete.    |
    """
    try:
        name = request.args.get('name')
        if not name or name == "":
            return jsonify({'error': 'name is required'}), 400
        result = S3Manager().delete_bucket(bucket_name=name)
        print(result)
        return jsonify(result), 204
    except Exception as e:
        return abort(500, message={"error": str(e)})


@buckets_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": e.messages}), 422
