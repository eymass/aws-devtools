from flask import Flask, request, jsonify, g
from api.deployments import deployments_bp
from api.buckets import buckets_bp
from marshmallow import ValidationError
from celery import Celery

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


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    return celery


app.config.update(
    CELERY_BROKER_URL='mongodb://localhost:27017/celery_broker',
    CELERY_RESULT_BACKEND='mongodb://localhost:27017/celery_backend'
)
# environment_deployer H2U41WXrCJi1AXbz
celery = make_celery(app)


@celery.task
def deploy_domain_task(domain_name, contact_info, origins, default_cache_behavior, cache_behaviors, purchase_domain):
    deployment_manager = DeploymentManager()
    return deployment_manager.deploy_domain(
        domain_name=domain_name,
        contact_info=contact_info,
        origins=origins,
        default_cache_behavior=default_cache_behavior,
        cache_behaviors=cache_behaviors,
        purchase_domain=purchase_domain
    )


@deployments_bp.route('/environments/deploy', methods=['POST'])
@deployments_bp.arguments(DeployEnvironmentSchema)
def deploy_environment(args):
    try:
        domain_name = args.get("domain_name", None)
        contact_info = args.get("contact_info", None)
        static_files_bucket = args.get("static_files_bucket", None)
        environment_url = args.get("environment_url", None)
        purchase_domain = args.get("purchase_domain", True)

        origins = DeploymentStatics.get_origins(static_files_bucket=static_files_bucket,
                                                environment_url=environment_url)
        default_cache_behavior = DeploymentStatics.get_default_cache_behavior(environment_url=environment_url)
        cache_behavior = DeploymentStatics.get_cache_behaviors(static_files_bucket=static_files_bucket)

        # Schedule the task
        task = deploy_domain_task.apply_async(
            args=[domain_name, contact_info, origins, default_cache_behavior, cache_behavior, purchase_domain]
        )
        return jsonify({"message": "Deployment scheduled", "jobId": task.id}), 202
    except Exception as e:
        return abort(500, message={"error": str(e)})


@deployments_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    task = deploy_domain_task.AsyncResult(job_id)
    if task.state == 'PENDING':
        response = {"state": task.state, "message": "Task is pending"}
    elif task.state == 'SUCCESS':
        response = {"state": task.state, "result": task.result}
    elif task.state == 'FAILURE':
        response = {"state": task.state, "error": str(task.info)}
    else:
        response = {"state": task.state, "message": "Task is processing"}
    return jsonify(response)
