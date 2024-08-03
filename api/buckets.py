from flask import request
from flask_smorest import Blueprint, abort
from flask import jsonify
from marshmallow import ValidationError
from .schemas.create_bucket_schema import CreateBucketSchema
from s3_manager import S3Manager

buckets_bp = Blueprint('buckets', __name__)


@buckets_bp.route('/', methods=['POST'])
@buckets_bp.arguments(CreateBucketSchema)
def create_bucket():
    """Endpoint to create a new bucket"""
    try:
        result = S3Manager().create_bucket(bucket_name=request.json['name'])
        print(result)
        return jsonify(result), 201
    except Exception as e:
        return abort(500, message=str(e))


@buckets_bp.route('/:name', methods=['DELETE'])
def delete_bucket():
    """Endpoint to delete a bucket"""
    try:
        name = request.args.get('name')
        if not name or name == "":
            return jsonify({'error': 'name is required'}), 400
        result = S3Manager().delete_bucket(bucket_name=name)
        print(result)
        return jsonify(result), 201
    except Exception as e:
        return abort(500, message=str(e))



@buckets_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": e.messages}), 422

