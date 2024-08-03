from flask import Flask, request, jsonify, g
from api.deployments import deployments_bp
from api.buckets import buckets_bp
from marshmallow import ValidationError

DEPLOYMENTS_ROUTE = '/api/deployments/'
BUCKETS_ROUTE = '/api/buckets/'


def create_app():
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



