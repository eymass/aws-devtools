from flask import request
from flask_smorest import Blueprint, abort
from flask import jsonify
from marshmallow import ValidationError

from exceptions.already_exists_exceptions import AlreadyExists
from .schemas.create_bucket_schema import CreateBucketSchema
from s3_manager import S3Manager

buckets_bp = Blueprint('buckets', __name__)


@buckets_bp.route('/', methods=['POST'])
@buckets_bp.arguments(CreateBucketSchema)
def handle_create_bucket(args):
    """Endpoint to create a new bucket"""
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
def delete_bucket():
    """Endpoint to delete a bucket"""
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

