import os
import sys

from flask import Flask, jsonify
from flask_smorest import Api
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

    # ------------------------------------------------------------------
    # OpenAPI / Swagger UI configuration
    # ------------------------------------------------------------------
    _app.config["API_TITLE"] = "Deployment Manager API"
    _app.config["API_VERSION"] = "v1"
    _app.config["OPENAPI_VERSION"] = "3.0.3"
    _app.config["OPENAPI_URL_PREFIX"] = "/"
    _app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
    # Serve Swagger UI assets from jsDelivr CDN (no extra package needed)
    _app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    _app.config["API_SPEC_OPTIONS"] = {
        "info": {
            "description": (
                "API for provisioning AWS infrastructure for web deployments. "
                "Supports registering domains via Route 53, creating CloudFront distributions "
                "(with optional edge routing via CloudFront Functions), managing ElasticBeanstalk "
                "environments, and orchestrating S3 bucket creation. "
                "\n\n"
                "Long-running operations (domain purchase, CloudFront provisioning) are handled "
                "asynchronously — endpoints return a `jobId` immediately and you poll "
                "`GET /api/deployments/jobs/{jobId}` to track progress."
            ),
        },
        "servers": [
            {"url": "/", "description": "Current host"},
        ],
    }

    api = Api(_app)
    api.register_blueprint(deployments_bp, url_prefix=DEPLOYMENTS_ROUTE)
    api.register_blueprint(buckets_bp, url_prefix=BUCKETS_ROUTE)

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
