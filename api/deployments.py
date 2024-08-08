import json

from flask_smorest import Blueprint, abort
from flask import jsonify, request
from marshmallow import ValidationError

from api.deployments_statics import DeploymentStatics
from api.schemas.create_environment_schema import CreateEnvironmentSchema, GetEnvironmentStatusSchema, \
    DeployEnvironmentSchema, CreateConfigurationTemplateSchema
from marshmallow import Schema, fields, validate
from deployment_manager import DeploymentManager
from elasticbeanstalk_manager import ElasticBeanstalkManager

deployments_bp = Blueprint('deployments', __name__)


@deployments_bp.route('/environments/deploy', methods=['POST'])
@deployments_bp.arguments(DeployEnvironmentSchema)
def deploy_environment(args):
    """Endpoint to deploy an environment"""
    try:
        req = DeployEnvironmentSchema(**args)
        deployment_manager = DeploymentManager()
        origins = DeploymentStatics.get_origins(static_files_bucket=req.static_files_bucket,
                                                environment_url=req.environment_url)
        default_cache_behavior = DeploymentStatics.get_default_cache_behavior(environment_url=req.environment_url)
        cache_behavior = DeploymentStatics.get_cache_behaviors(static_files_bucket=req.static_files_bucket)

        deployment_manager.deploy_domain(domain_name=req.domain_name,
                                         contact_info=req.contact_info,
                                         origins=origins,
                                         default_cache_behavior=default_cache_behavior,
                                         cache_behaviors=cache_behavior,
                                         purchase_domain=True)
        return jsonify({"message": "Deployment successful"}), 201
    except Exception as e:
        return abort(500, message=str(e))


@deployments_bp.route('/environments', methods=['POST'])
@deployments_bp.arguments(CreateEnvironmentSchema)
def create_environment(args):
    """Endpoint to create an environment"""
    try:
        response = ElasticBeanstalkManager().create_environment(
            environment_name=args.get("environment_name", None),
            description=args.get("description", None),
            stack_name=args.get("stack_name", None),
            template_name=args.get("template_name", None),
            application_name=args.get("application_name", None),
            environment_variables=args.get("environment_variables", None),
            tags=[],
        )
        return jsonify(response), 201
    except Exception as e:
        return abort(500, message=str(e))


@deployments_bp.route('/environments', methods=['DELETE'])
def terminate_environment():
    """Endpoint to terminate an environment"""
    try:
        env_name = request.args.get('name')
        print(f"terminating environment {env_name}")
        if not env_name or env_name == "":
            print("environment name is required")
            return abort(400, message="Environment name is required")
        response = ElasticBeanstalkManager().terminate_environment(
            environment_name=env_name,
        )
        print(f"response: {response}")
        return jsonify(response), 201
    except Exception as e:
        print(f"error terminating environment {e}")
        return abort(500, message=str(e))


@deployments_bp.route('/environments/configuration_template', methods=['POST'])
@deployments_bp.arguments(CreateConfigurationTemplateSchema)
def create_environment(args):
    """Endpoint to create configuration template"""
    try:
        print("handling create configuration template")
        response = ElasticBeanstalkManager().create_configuration_template(
            application_name=args["application_name"],
        )
        return jsonify(response), 201
    except Exception as e:
        print(f"error creating configuration template {e}")
        return abort(500, message=str(e))


@deployments_bp.route('/environments/status', methods=['GET'])
@deployments_bp.arguments(GetEnvironmentStatusSchema, location="query")
def get_environment_status(args):
    """Endpoint to get environment status"""
    try:
        req = GetEnvironmentStatusSchema().load(args)
        config = ElasticBeanstalkManager().get_environment_status(
            environment_name=req['environment_name']
        )
        if config is None:
            return abort(404, description="Environment not found")
        return jsonify(config), 200
    except Exception as e:
        return abort(500, description=str(e))


@deployments_bp.route('/environments/list', methods=['GET'])
def list_environment():
    """Endpoint to list environments in a region"""
    try:
        response = ElasticBeanstalkManager().list_environments()
        json.dump(response["Environments"], open('data.json', 'w'), default=str)
        jsonify({"data": response}), 200
    except Exception as e:
        return abort(500, message=str(e))


@deployments_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": e.messages}), 422
