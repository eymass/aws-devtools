import json

from app import DEPLOYMENTS_ROUTE
from elasticbeanstalk_manager import EBEnvironmentStatus


def test_list_environments_success(app):
    response = app.test_client().get(DEPLOYMENTS_ROUTE+"environments/list"+"?region=us-east-1")
    assert response.status_code == 201
    assert 'errors' not in response.json


def test_create_environments_success(app):
    env_name = "global-web3-test2"
    request = {
        "environment_name": env_name,
        "description": "test description",
        "application_name": "global-web3",
        "template_name": "template-global-web3",
        "environment_variables": {"test": "test"}
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
    app_name = "global-web3"
    request = {
        "application_name": "app_name",
    }
    response = app.test_client().post(DEPLOYMENTS_ROUTE+"environments/configuration_template",
                                      data=json.dumps(request), content_type='application/json')
    assert response.status_code == 201
    assert 'errors' not in response.json
    assert 'TemplateName' in response.json
    assert 'TemplateName' == "template-" + app_name