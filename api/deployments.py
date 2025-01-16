import json

from flask_smorest import Blueprint, abort
from flask import jsonify, request
from marshmallow import ValidationError
from celery_app import celery_app
from api.deployments_statics import DeploymentStatics
from api.schemas.create_environment_schema import CreateEnvironmentSchema, GetEnvironmentStatusSchema, \
    DeployEnvironmentSchema, CreateConfigurationTemplateSchema, RestartSchema, RemoveConfigurationTemplateSchema
from marshmallow import Schema, fields, validate

from cloudfront_manager import CloudFrontManager
from deployment_manager import DeploymentManager
from elasticbeanstalk_manager import ElasticBeanstalkManager
from route53_manager import Route53Manager

deployments_bp = Blueprint('deployments', __name__)


@deployments_bp.route('/environments/deploy', methods=['POST'])
@deployments_bp.arguments(DeployEnvironmentSchema)
def deploy_environment(args):
    """Endpoint to deploy an environment"""
    try:
        domain_name = args.get("domain_name", None)
        contact_info = args.get("contact_info", None)
        static_files_bucket = args.get("static_files_bucket", None)
        environment_url = args.get("environment_url", None)
        purchase_domain = args.get("purchase_domain", True)

        print(f"deploying environment {environment_url} with domain {domain_name} and static files bucket {static_files_bucket}")
        origins = DeploymentStatics.get_origins(static_files_bucket=static_files_bucket,
                                                environment_url=environment_url)
        default_cache_behavior = DeploymentStatics.get_default_cache_behavior(environment_url=environment_url)
        cache_behavior = DeploymentStatics.get_cache_behaviors(static_files_bucket=static_files_bucket)

        task = deploy_domain_task_wrapped.apply_async(
            args=[domain_name, contact_info, origins, default_cache_behavior, cache_behavior, purchase_domain]
        )
        print("Deployment successful")
        return jsonify({"message": "Deployment scheduled", "jobId": task.id}), 202
    except Exception as e:
        print(f"error deploying environment {e}")
        return abort(500, message={"error": str(e)})


@celery_app.task
def deploy_domain_task_wrapped(domain_name, contact_info, origins, default_cache_behavior,
                               cache_behavior, purchase_domain):
    try:
        deployment_manager = DeploymentManager()
        print("starting deploy_domain_task_wrapped")
        result = deployment_manager.deploy_domain(domain_name=domain_name,
                                                  contact_info=contact_info,
                                                  origins=origins,
                                                  default_cache_behavior=default_cache_behavior,
                                                  cache_behaviors=cache_behavior,
                                                  purchase_domain=purchase_domain)
        return result
    except Exception as e:
        print(f"error deploying domain {e}")
        raise e


@deployments_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    task = deploy_domain_task_wrapped.AsyncResult(job_id)
    if task.state == 'PENDING':
        response = {"state": task.state, "message": "Task is pending"}
    elif task.state == 'SUCCESS':
        response = {"state": task.state, "result": task.result}
    elif task.state == 'FAILURE':
        response = {"state": task.state, "error": str(task.info)}
    else:
        response = {"state": task.state, "message": "Task is processing"}
    return jsonify(response)


@deployments_bp.route('/environments', methods=['POST'])
@deployments_bp.arguments(CreateEnvironmentSchema)
def create_environment(args):
    """Endpoint to create an environment"""
    try:
        print(f"[create_environment] start {args}")
        response = ElasticBeanstalkManager().create_environment(
            environment_name=args.get("environment_name", None),
            description=args.get("description", None),
            stack_name=args.get("stack_name", None),
            template_name=args.get("template_name", None),
            application_name=args.get("application_name", None),
            environment_variables=args.get("environment_variables", None),
            tags=[],
        )
        print(f"[create_environment] respond: {response}")
        return jsonify(response), 201
    except Exception as e:
        print(f"[create_environment] error creating environment {e}")
        return abort(500, message={"error": str(e)})


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
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/domains/availability', methods=['GET'])
def check_domain_availability():
    """Endpoint to terminate an environment"""
    try:
        domain_name = request.args.get('domain')
        print(f"checking domain availability domain_name=[{domain_name}]")
        if not domain_name or domain_name == "":
            msg = "domain_name name is required"
            print(msg)
            return abort(400, message=msg)
        response = Route53Manager().is_domain_available(
            domain_name=domain_name,
        )
        print(f"response: {response}")
        return jsonify(response), 201
    except Exception as e:
        print(f"error checking domain availability {e}")
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/domains/ownership', methods=['GET'])
def check_domain_ownership():
    """Endpoint to check domain ownership"""
    try:
        domain_name = request.args.get('domain')
        print(f"checking domain ownership domain_name=[{domain_name}]")
        if not domain_name or domain_name == "":
            msg = "domain_name name is required"
            print(msg)
            return abort(400, message=msg)
        response = Route53Manager().is_domain_owned(
            domain_name=domain_name,
        )
        print(f"response: {response}")
        return jsonify(response), 201
    except Exception as e:
        print(f"error checking domain ownership {e}")
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/environments/validate', methods=['GET'])
def validate_domain_e2e():
    """" using validate_e2e_environment """
    """Endpoint to remove configuration template"""
    try:
        environment_name = request.args.get('environment_name')
        domain_name = request.args.get('domain_name')
        if not environment_name or environment_name == "":
            return jsonify({"error": "environment_name or environment_name is missing"}), 400
        if not domain_name or domain_name == "":
            return jsonify({"error": "domain_name or domain_name is missing"}), 400
        print("handling validate env and domain")
        response = ElasticBeanstalkManager().validate_e2e_environment(
            environment_name=environment_name,
            domain_name=domain_name,
        )
        return jsonify(response), 200
    except Exception as e:
        print(f"error validating environment {e}")
        return abort(500, message={"error": str(e)})

@deployments_bp.route('/environments/configuration_template', methods=['POST'])
@deployments_bp.arguments(CreateConfigurationTemplateSchema)
def create_environment_template(args):
    """Endpoint to create configuration template"""
    try:
        if not args.get("application_name", None) or args.get("application_name", None) == "":
            return jsonify({"error": "application_name or application_name is missing"}), 400
        print("handling create configuration template")
        response = ElasticBeanstalkManager().create_configuration_template(
            application_name=args["application_name"],
            environment_name=args["environment_name"],
        )
        return jsonify(response), 201
    except Exception as e:
        print(f"error creating configuration template {e}")
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/environments/configuration_template', methods=['DELETE'])
@deployments_bp.arguments(RemoveConfigurationTemplateSchema)
def remove_environment_template(args):
    """Endpoint to remove configuration template"""
    try:
        if not args.get("application_name", None) or args.get("application_name", None) == "":
            return jsonify({"error": "application_name or application_name is missing"}), 400
        print("handling remove configuration template")
        response = ElasticBeanstalkManager().delete_configuration_template(
            application_name=args["application_name"],
            template_name=args["template_name"],
        )
        return jsonify(response), 201
    except Exception as e:
        print(f"error removing configuration template {e}")
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/environments/restart', methods=['POST'])
@deployments_bp.arguments(RestartSchema)
def restart_environment(args):
    """Endpoint to create configuration template"""
    try:
        print("handling create configuration template")
        response = ElasticBeanstalkManager().restart_environment(
            environment_name=args["environment_name"],
        )
        return jsonify(response), 201
    except Exception as e:
        print(f"error creating configuration template {e}")
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/environments/status', methods=['GET'])
def get_environment_status():
    """Endpoint to get environment status"""
    try:
        environment_name = request.args.get('environment_name')
        config = ElasticBeanstalkManager().get_environment_status(
            environment_name=environment_name
        )
        if config is None:
            return abort(404, description="Environment not found")
        return jsonify(config), 200
    except Exception as e:
        return abort(502, description=str(e))


@deployments_bp.route('/environments/health', methods=['GET'])
@deployments_bp.arguments(GetEnvironmentStatusSchema, location="query")
def get_environment_health(args):
    """Endpoint to get environment health"""
    try:
        req = GetEnvironmentStatusSchema().load(args)
        health = ElasticBeanstalkManager().describe_environment_health(
            environment_name=req['environment_name']
        )
        logs = ElasticBeanstalkManager().retrieve_environment_logs(
            environment_name=req['environment_name']
        )
        return jsonify({health: health, logs: logs}), 200
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
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/cloudfronts/list', methods=['GET'])
def list_cloudfronts():
    """Endpoint to list cloudfronts in a region"""
    try:
        response = CloudFrontManager().list_cloudfronts()
        json.dump(response["Environments"], open('data.json', 'w'), default=str)
        jsonify({"data": response}), 200
    except Exception as e:
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/cloudfronts/dist_id', methods=['GET'])
def get_distribution_config():
    """Get dist config in a region"""
    try:
        dist_id = request.args.get('distribution_id')
        if not dist_id or dist_id == "":
            return abort(400, message="distribution_id is required")
        response = CloudFrontManager().get_distribution_config(distribution_id=dist_id)
        json.dump(response["Environments"], open('data.json', 'w'), default=str)
        jsonify({"data": response}), 200
    except Exception as e:
        return abort(500, message={"error": str(e)})


@deployments_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": e.messages}), 422
