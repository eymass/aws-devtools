
import json
import time

from app import DEPLOYMENTS_ROUTE

TEST_BUCKET_NAME = "global-web3-sa-pens1"
DOMAIN_NAME = "betterfuture2025.com"
ENVIRONMENT_URL = "global-web3-sa-pens1.eba-p4cwtpiw.us-east-1.elasticbeanstalk.com"
CONTACT_INFO = {
    'FirstName': 'John',
    'LastName': 'Doe',
    'ContactType': 'PERSON',
    'OrganizationName': 'Example Org',
    'AddressLine1': 'TLV',
    'City': 'TLV',
    'CountryCode': 'IL',
    'ZipCode': '3522222',
    'PhoneNumber': '+972.508777733',
    'Email': 'redcommang@gmail.com'
}


def test_e2e_deploy_environment_success(app):
    deployment_data = {
        "domain_name": DOMAIN_NAME,
        "contact_info": CONTACT_INFO,
        "static_files_bucket": TEST_BUCKET_NAME+".s3.amazonaws.com",
        "environment_url": ENVIRONMENT_URL,
        "purchase_domain": False
    }
    response = app.test_client().post(DEPLOYMENTS_ROUTE + "environments/deploy",
                                      data=json.dumps(deployment_data),
                                      content_type='application/json')
    assert response.status_code == 202
    assert response.json.get("jobId") is not None
    assert 'errors' not in response.json

    max_count = 10
    count = 1
    while True:
        response = app.test_client().get(DEPLOYMENTS_ROUTE + f"jobs/{response.json.get("jobId")}")
        assert response.status_code == 200
        if response.json.get("state") == "SUCCESS" or response.json.get("state") == "FAILURE":
            assert response.json.get("state") == "FAILURE"
            break
        if count >= max_count:
            break
        count += 1
        time.sleep(8)


def test_e2e_domain_ownership(app):
    response = app.test_client().get(DEPLOYMENTS_ROUTE + f"domains/ownership?domain=blabla.com")
    assert response.status_code == 200
    assert response.json.get("Owned") is True
