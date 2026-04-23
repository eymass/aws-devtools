import json

from flask_smorest import Blueprint, abort
from flask import jsonify, request
from marshmallow import ValidationError
from celery_app import celery_app
from api.deployments_statics import DeploymentStatics
from api.schemas.create_environment_schema import (
    CreateEnvironmentSchema,
    GetEnvironmentStatusSchema,
    DeployEnvironmentSchema,
    DeployStaticSchema,
    CreateConfigurationTemplateSchema,
    RestartSchema,
    RemoveConfigurationTemplateSchema,
)
from api.schemas.response_schemas import (
    AsyncJobResponseSchema,
    JobStatusResponseSchema,
    EnvironmentResponseSchema,
    DataListResponseSchema,
    DomainAvailabilityResponseSchema,
    EnvironmentStatusResponseSchema,
    EnvironmentHealthResponseSchema,
    ValidationResponseSchema,
    ErrorResponseSchema,
)
import traceback
from cloudfront_manager import CloudFrontManager
from deployment_manager import DeploymentManager
from elasticbeanstalk_manager import ElasticBeanstalkManager
from route53_manager import Route53Manager

deployments_bp = Blueprint(
    'deployments',
    __name__,
    description=(
        "Manage AWS deployments: register domains via Route 53, provision CloudFront distributions, "
        "create and operate ElasticBeanstalk environments, and orchestrate full-stack deployments "
        "asynchronously via Celery background jobs."
    ),
)


# ---------------------------------------------------------------------------
# Async deployment endpoints
# ---------------------------------------------------------------------------

@deployments_bp.route('/environments/deploy', methods=['POST'])
@deployments_bp.arguments(DeployEnvironmentSchema)
@deployments_bp.response(202, AsyncJobResponseSchema, description=(
    "Deployment job accepted. Use the returned jobId with GET /jobs/{jobId} to poll for completion."
))
def deploy_environment(args):
    """Deploy CloudFront + domain in front of an ElasticBeanstalk environment.

    Registers (or reuses) the domain in Route 53, requests an ACM certificate,
    builds a multi-origin CloudFront distribution (static assets from S3,
    dynamic traffic to ElasticBeanstalk), and wires up DNS alias records.

    This is a **long-running operation** — the job is queued and the endpoint
    returns immediately with a `jobId`. Poll `GET /jobs/{jobId}` to track progress.
    """
    try:
        domain_name = args.get("domain_name", None)
        contact_info = args.get("contact_info", None)
        static_files_bucket = args.get("static_files_bucket", None)
        environment_url = args.get("environment_url", None)
        purchase_domain = args.get("purchase_domain", True)

        print(f"deploying environment {environment_url} with domain {domain_name} "
              f"and static files bucket {static_files_bucket}")
        origins = DeploymentStatics.get_origins(static_files_bucket=static_files_bucket,
                                                environment_url=environment_url)
        print(f"origins: {origins}")
        default_cache_behavior = DeploymentStatics.get_default_cache_behavior(environment_url=environment_url)
        cache_behavior = DeploymentStatics.get_cache_behaviors(static_files_bucket=static_files_bucket)
        print(f"cache_behavior: {cache_behavior}")
        task = deploy_domain_task_wrapped.apply_async(
            args=[domain_name, contact_info, origins, default_cache_behavior, cache_behavior, purchase_domain]
        )
        print("Deployment successful")
        return jsonify({"message": "Deployment scheduled", "jobId": task.id}), 202
    except Exception as e:
        print(f"error deploying environment {e}")
        traceback.print_exc()
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


@deployments_bp.route('/statics/deploy', methods=['POST'])
@deployments_bp.arguments(DeployStaticSchema)
@deployments_bp.response(202, AsyncJobResponseSchema, description=(
    "Deployment job accepted. Use the returned jobId with GET /jobs/{jobId} to poll for completion."
))
def deploy_static(args):
    """Deploy CloudFront + domain in front of an S3 static-website bucket.

    Registers (or reuses) the domain in Route 53, requests an ACM certificate,
    creates a CloudFront distribution pointing to the S3 website endpoint,
    and creates DNS alias records.

    Optionally attaches a **CloudFront Function** (viewer-request) for
    edge routing logic:

    - Set `enable_viewer_request=true` to activate edge routing.
    - Use `routing_type` to select a built-in template:
      `geo`, `ab`, `utm`, `ip`, `device`, `path`, or `composite`.
    - Or supply raw JavaScript in `viewer_request_function_code` for a
      fully custom function.
    - Pass `routing_config` to parameterise built-in templates
      (e.g. country → variant mappings for `geo` routing).

    This is a **long-running operation** — the job is queued and the endpoint
    returns immediately with a `jobId`. Poll `GET /jobs/{jobId}` to track progress.
    """
    try:
        domain_name = args.get("domain_name")
        contact_info = args.get("contact_info")
        s3_website_url = args.get("s3_website_url")
        purchase_domain = args.get("purchase_domain", True)
        enable_viewer_request = args.get("enable_viewer_request", False)
        routing_type = args.get("routing_type")
        viewer_request_function_code = args.get("viewer_request_function_code")
        routing_config = args.get("routing_config")
        viewer_request_function_name = args.get("viewer_request_function_name")

        print(f"[deploy_static] deploying domain={domain_name} "
              f"s3_website_url={s3_website_url} purchase_domain={purchase_domain} "
              f"enable_viewer_request={enable_viewer_request} routing_type={routing_type}")

        task = deploy_static_task_wrapped.apply_async(
            args=[
                domain_name, contact_info, s3_website_url, purchase_domain,
                enable_viewer_request, routing_type, viewer_request_function_code,
                routing_config, viewer_request_function_name,
            ]
        )
        print(f"[deploy_static] task queued jobId={task.id}")
        return jsonify({"message": "Static deployment scheduled", "jobId": task.id}), 202
    except Exception as e:
        print(f"[deploy_static] error: {e}")
        traceback.print_exc()
        return abort(500, message={"error": str(e)})


@celery_app.task
def deploy_static_task_wrapped(
    domain_name, contact_info, s3_website_url, purchase_domain,
    enable_viewer_request=False, routing_type=None,
    viewer_request_function_code=None, routing_config=None,
    viewer_request_function_name=None,
):
    try:
        print(f"[deploy_static_task_wrapped] start "
              f"domain={domain_name} s3_website_url={s3_website_url} "
              f"enable_viewer_request={enable_viewer_request} routing_type={routing_type}")
        result = DeploymentManager().deploy_static_domain(
            domain_name=domain_name,
            contact_info=contact_info,
            s3_website_url=s3_website_url,
            purchase_domain=purchase_domain,
            enable_viewer_request=enable_viewer_request,
            routing_type=routing_type,
            viewer_request_function_code=viewer_request_function_code,
            routing_config=routing_config,
            viewer_request_function_name=viewer_request_function_name,
        )
        print(f"[deploy_static_task_wrapped] done result={result}")
        return result
    except Exception as e:
        print(f"[deploy_static_task_wrapped] error: {e}")
        raise e


# ---------------------------------------------------------------------------
# Job status
# ---------------------------------------------------------------------------

@deployments_bp.route('/jobs/<job_id>', methods=['GET'])
@deployments_bp.response(200, JobStatusResponseSchema, description="Current task state and payload.")
def get_job_status(job_id):
    """Poll the status of an async deployment job.

    Pass the `jobId` returned by `POST /statics/deploy` or
    `POST /environments/deploy` to retrieve the current state.

    **State machine:**

    | state    | description                                      |
    |----------|--------------------------------------------------|
    | PENDING  | Job is queued but not yet picked up by a worker. |
    | PROGRESS | Worker is actively executing the job.            |
    | SUCCESS  | Job completed successfully — see `result`.       |
    | FAILURE  | Job failed — see `error` for the exception.      |
    """
    task = deploy_domain_task_wrapped.AsyncResult(job_id)
    if task.state == 'PENDING':
        response = {"state": task.state, "message": "Task is pending"}
    elif task.state == 'SUCCESS':
        response = {"state": task.state, "result": task.result}
    elif task.state == 'FAILURE':
        response = {"state": task.state, "error": str(task.info)}
    else:
        response = {"state": task.state, "message": "Task is processing"}
    print(f"[get_job_status] {response}")
    return jsonify(response)


# ---------------------------------------------------------------------------
# ElasticBeanstalk environment management
# ---------------------------------------------------------------------------

@deployments_bp.route('/environments', methods=['POST'])
@deployments_bp.arguments(CreateEnvironmentSchema)
@deployments_bp.response(201, EnvironmentResponseSchema, description="Environment created successfully.")
def create_environment(args):
    """Create a new ElasticBeanstalk environment.

    Creates an environment within the specified application using either a
    solution stack (`stack_name`) or a saved configuration template (`template_name`).
    Environment variables are injected as `PARAM_*` option settings.
    """
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
@deployments_bp.response(201, EnvironmentResponseSchema, description="Environment termination initiated.")
def terminate_environment():
    """Terminate an ElasticBeanstalk environment.

    Initiates graceful termination of the environment. The operation is
    asynchronous on the AWS side — the environment transitions to `Terminating`
    and then `Terminated`.

    **Query parameters:**

    | Parameter | Type   | Required | Description                        |
    |-----------|--------|----------|------------------------------------|
    | name      | string | Yes      | Name of the environment to delete. |
    """
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


@deployments_bp.route('/environments/status', methods=['GET'])
@deployments_bp.response(200, EnvironmentStatusResponseSchema,
                         description="Current environment configuration and status.")
def get_environment_status():
    """Get the current status and configuration of an ElasticBeanstalk environment.

    **Query parameters:**

    | Parameter        | Type   | Required | Description                   |
    |------------------|--------|----------|-------------------------------|
    | environment_name | string | Yes      | Name of the environment.      |
    """
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
@deployments_bp.response(200, EnvironmentHealthResponseSchema, description="Environment health data and recent logs.")
def get_environment_health(args):
    """Get health status and recent logs for an ElasticBeanstalk environment.

    Returns the output of `describe_environment_health` (overall health color,
    causes, metrics) plus the most recent log bundle from `retrieve_environment_logs`.
    """
    try:
        req = GetEnvironmentStatusSchema().load(args)
        health = ElasticBeanstalkManager().describe_environment_health(
            environment_name=req['environment_name']
        )
        logs = ElasticBeanstalkManager().retrieve_environment_logs(
            environment_name=req['environment_name']
        )
        return jsonify({"health": health, "logs": logs}), 200
    except Exception as e:
        return abort(500, description=str(e))


@deployments_bp.route('/environments/list', methods=['GET'])
@deployments_bp.response(200, DataListResponseSchema,
                         description="List of all ElasticBeanstalk environments in the region.")
def list_environment():
    """List all ElasticBeanstalk environments in the configured AWS region."""
    try:
        response = ElasticBeanstalkManager().list_environments()
        json.dump(response["Environments"], open('data.json', 'w'), default=str)
        return jsonify({"data": response}), 200
    except Exception as e:
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/environments/validate', methods=['GET'])
@deployments_bp.response(200, ValidationResponseSchema, description="End-to-end validation result.")
def validate_domain_e2e():
    """Validate that an ElasticBeanstalk environment and its domain are wired up correctly.

    Performs an end-to-end check: verifies that the environment is healthy,
    the CloudFront distribution exists, and the domain resolves to the
    distribution endpoint.

    **Query parameters:**

    | Parameter        | Type   | Required | Description                                  |
    |------------------|--------|----------|----------------------------------------------|
    | environment_name | string | Yes      | Name of the ElasticBeanstalk environment.    |
    | domain_name      | string | Yes      | Apex domain to validate (e.g. myapp.com).    |
    """
    try:
        environment_name = request.args.get('environment_name')
        domain_name = request.args.get('domain_name')
        if not environment_name or environment_name == "":
            return jsonify({"error": "environment_name is missing"}), 400
        if not domain_name or domain_name == "":
            return jsonify({"error": "domain_name is missing"}), 400
        print("handling validate env and domain")
        response = ElasticBeanstalkManager().validate_e2e_environment(
            environment_name=environment_name,
            domain_name=domain_name,
        )
        return jsonify(response), 200
    except Exception as e:
        print(f"error validating environment {e}")
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/environments/restart', methods=['POST'])
@deployments_bp.arguments(RestartSchema)
@deployments_bp.response(201, EnvironmentResponseSchema, description="Environment restart initiated.")
def restart_environment(args):
    """Restart all EC2 instances in an ElasticBeanstalk environment.

    Performs a rolling restart without re-deploying the application version.
    Useful for picking up new environment variables or clearing stale state.
    """
    try:
        print("handling restart environment")
        response = ElasticBeanstalkManager().restart_environment(
            environment_name=args["environment_name"],
        )
        return jsonify(response), 201
    except Exception as e:
        print(f"error restarting environment {e}")
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/environments/rebuild', methods=['POST'])
@deployments_bp.arguments(RestartSchema)
@deployments_bp.response(201, EnvironmentResponseSchema, description="Environment rebuild initiated.")
def rebuild_environment(args):
    """Rebuild an ElasticBeanstalk environment.

    Terminates and re-provisions all infrastructure (EC2, load balancer, Auto Scaling)
    while preserving the application version and environment configuration.
    This is more disruptive than a restart — use it to recover a broken environment.
    """
    try:
        print("handling rebuild env")
        response = ElasticBeanstalkManager().rebuild_environment(
            environment_name=args["environment_name"],
        )
        return jsonify(response), 201
    except Exception as e:
        print(f"error rebuilding env {e}")
        return abort(500, message={"error": str(e)})


# ---------------------------------------------------------------------------
# Configuration templates
# ---------------------------------------------------------------------------

@deployments_bp.route('/environments/configuration_template', methods=['POST'])
@deployments_bp.arguments(CreateConfigurationTemplateSchema)
@deployments_bp.response(201, EnvironmentResponseSchema, description="Configuration template created.")
def create_environment_template(args):
    """Snapshot an environment's configuration as a reusable template.

    Saves the current settings of the specified environment (instance type,
    environment variables, load balancer config, etc.) as a named template
    that can be referenced when creating future environments.
    """
    try:
        if not args.get("application_name", None):
            return jsonify({"error": "application_name is missing"}), 400
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
@deployments_bp.response(201, EnvironmentResponseSchema, description="Configuration template deleted.")
def remove_environment_template(args):
    """Delete a saved ElasticBeanstalk configuration template."""
    try:
        if not args.get("application_name", None):
            return jsonify({"error": "application_name is missing"}), 400
        print("handling remove configuration template")
        response = ElasticBeanstalkManager().delete_configuration_template(
            application_name=args["application_name"],
            template_name=args["template_name"],
        )
        return jsonify(response), 201
    except Exception as e:
        print(f"error removing configuration template {e}")
        return abort(500, message={"error": str(e)})


# ---------------------------------------------------------------------------
# Domain management
# ---------------------------------------------------------------------------

@deployments_bp.route('/domains/availability', methods=['GET'])
@deployments_bp.response(201, DomainAvailabilityResponseSchema, description="Domain availability check result.")
def check_domain_availability():
    """Check whether a domain name is available for registration.

    Uses the Route 53 Domains `checkDomainAvailability` API.

    **Query parameters:**

    | Parameter | Type   | Required | Description                              |
    |-----------|--------|----------|------------------------------------------|
    | domain    | string | Yes      | Domain name to check (e.g. myapp.com).   |
    """
    try:
        domain_name = request.args.get('domain')
        print(f"checking domain availability domain_name=[{domain_name}]")
        if not domain_name or domain_name == "":
            msg = "domain_name is required"
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
@deployments_bp.response(201, DomainAvailabilityResponseSchema, description="Domain ownership check result.")
def check_domain_ownership():
    """Check whether a domain is registered in the current AWS account.

    Uses Route 53 Domains `listDomains` to verify ownership.

    **Query parameters:**

    | Parameter | Type   | Required | Description                              |
    |-----------|--------|----------|------------------------------------------|
    | domain    | string | Yes      | Domain name to check (e.g. myapp.com).   |
    """
    try:
        domain_name = request.args.get('domain')
        print(f"checking domain ownership domain_name=[{domain_name}]")
        if not domain_name or domain_name == "":
            msg = "domain_name is required"
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


# ---------------------------------------------------------------------------
# CloudFront management
# ---------------------------------------------------------------------------

@deployments_bp.route('/cloudfronts/list', methods=['GET'])
@deployments_bp.response(200, DataListResponseSchema, description="List of CloudFront distributions in the account.")
def list_cloudfronts():
    """List all CloudFront distributions in the AWS account."""
    try:
        response = CloudFrontManager().list_cloudfronts()
        json.dump(response.get("Environments", []), open('data.json', 'w'), default=str)
        return jsonify({"data": response}), 200
    except Exception as e:
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/cloudfronts/dist_id', methods=['GET'])
@deployments_bp.response(200, DataListResponseSchema, description="CloudFront distribution configuration.")
def get_distribution_config():
    """Get the full configuration of a specific CloudFront distribution.

    **Query parameters:**

    | Parameter       | Type   | Required | Description                           |
    |-----------------|--------|----------|---------------------------------------|
    | distribution_id | string | Yes      | CloudFront distribution ID (e.g. E1234ABCDEF). |
    """
    try:
        dist_id = request.args.get('distribution_id')
        if not dist_id or dist_id == "":
            return abort(400, message="distribution_id is required")
        response = CloudFrontManager().get_distribution_config(distribution_id=dist_id)
        json.dump(response.get("Environments", []), open('data.json', 'w'), default=str)
        return jsonify({"data": response}), 200
    except Exception as e:
        return abort(500, message={"error": str(e)})


@deployments_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": e.messages}), 422
