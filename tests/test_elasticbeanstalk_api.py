import json

from app import DEPLOYMENTS_ROUTE
from elasticbeanstalk_manager import EBEnvironmentStatus


def test_get_environment_health_success(app):
    env_name = "apprca"
    request = {
        "environment_name": env_name
    }
    response = app.test_client().get(DEPLOYMENTS_ROUTE+"environments/health",
                                    query_string=request)
    assert response.status_code == 200
    assert 'errors' not in response.json
    assert 'Health' in response.json


def test_restart_environment_success(app):
    env_name = "apprca"
    request = {
        "environment_name": env_name
    }
    response = app.test_client().post(DEPLOYMENTS_ROUTE+"environments/restart",
                                     data=json.dumps(request), content_type='application/json')
    assert response.status_code == 201
    assert 'errors' not in response.json
    assert 'Status' in response.json


def test_list_environments_success(app):
    response = app.test_client().get(DEPLOYMENTS_ROUTE+"environments/list"+"?region=us-east-1")
    assert response.status_code == 201
    assert 'errors' not in response.json


def test_list_cloudfronts_success(app):
    response = app.test_client().get(DEPLOYMENTS_ROUTE+"cloudfronts/list"+"?region=us-east-1")
    assert response.status_code == 201
    assert 'errors' not in response.json


def test_check_domain_availability_success(app):
    domain_name = "test.com"
    request = {
        "domain": domain_name
    }
    response = app.test_client().get(DEPLOYMENTS_ROUTE+"domains/availability",
                                    query_string=request)
    assert response.status_code == 201
    assert 'errors' not in response.json
    assert 'Availability' in response.json
    assert response.json['Availability'] == 'UNAVAILABLE'


def test_get_environment_status_success(app):
    env_name = "global-web3-sa-pens1"
    request = {
        "environment_name": env_name
    }
    response = app.test_client().get(DEPLOYMENTS_ROUTE+"environments/status",
                                    query_string=request)
    assert response.status_code == 200
    assert 'errors' not in response.json
    assert 'Status' in response.json
    assert response.json['Status'] == EBEnvironmentStatus.Terminated

def test_create_environments_success(app):
    env_name = "global-dynamic-pens1"
    request = {
        "environment_name": env_name,
        "description": "global dynamic pens",
        "application_name": "global-dynamic",
        #"template_name": "template-global-web3",
        "environment_variables": {
            "PLATFORM_ENV": "production",
            "NAMESPACE": "global-web3-sa-pens1",
            "BUCKET_URL": "https://global-web3-sa-pens1.s3.us-east-1.amazonaws.com",
            "MONGO_URI": "mongodb+srv://sa-pens1admin:Ms+9v+k7vYz9Z<Ps@blog.7efvgcb.mongodb.net/global-web3-sa-pens1?retryWrites=true&w=majority",
            "MONGO_DB": "global-web3-sa-pens1",
            "GENERATOR_URL": "https://post-generator-ai-cfea6fc9daab.herokuapp.com",
        }
    }
    response = app.test_client().post(DEPLOYMENTS_ROUTE+"environments",
                                      data=json.dumps(request), content_type='application/json')
    assert response.status_code == 201
    assert 'EnvironmentId' in response.json
    assert 'Status' in response.json
    assert response.json['Status'] == EBEnvironmentStatus.Launching
    assert 'EnvironmentName' in response.json
    assert response.json['EnvironmentName'] == env_name
    assert 'errors' not in response.json

    response = app.test_client().delete(DEPLOYMENTS_ROUTE+"environments?name="+env_name)
    assert response.status_code == 201
    assert 'Status' in response.json
    assert response.json["Status"] == EBEnvironmentStatus.Terminating

def test_create_configuration_template_success(app):
    app_name = "global-dynamic"
    env_name = "global-dynamic2"
    request = {
        "application_name": app_name,
        "environment_name": env_name,
    }
    response = app.test_client().post(DEPLOYMENTS_ROUTE+"environments/configuration_template",
                                      data=json.dumps(request), content_type='application/json')
    assert response.status_code == 201
    assert 'errors' not in response.json
    assert 'TemplateName' in response.json
    assert 'TemplateName' == "template-" + app_name
