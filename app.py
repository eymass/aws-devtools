import os
import sys

from flask import Flask, jsonify
from api.deployments import deployments_bp
from api.buckets import buckets_bp
from marshmallow import ValidationError

DEPLOYMENTS_ROUTE = '/api/deployments/'
BUCKETS_ROUTE = '/api/buckets/'

REQUIRED_AWS_ENV_VARS = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']


def validate_aws_env_vars():
    """Validate that required AWS environment variables are set."""
    missing_vars = [var for var in REQUIRED_AWS_ENV_VARS if not os.environ.get(var)]
    if missing_vars:
        print("ERROR: Missing required AWS environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these environment variables before starting the application:")
        print('  export AWS_ACCESS_KEY_ID="your_access_key"')
        print('  export AWS_SECRET_ACCESS_KEY="your_secret_key"')
        print('  export AWS_DEFAULT_REGION="us-east-1"')
        sys.exit(1)


def create_app():
    validate_aws_env_vars()
    _app = Flask(__name__)
    _app.register_blueprint(deployments_bp, url_prefix=DEPLOYMENTS_ROUTE)
    _app.register_blueprint(buckets_bp, url_prefix=BUCKETS_ROUTE)

    @_app.errorhandler(422)
    def handle_422_error(e):
        response = jsonify({"errors": e.data.get("messages", None)})
        response.status_code = 422
        return response

    @_app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({"error": e.messages}), 400

    return _app


app = create_app()
