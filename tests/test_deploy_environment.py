
import json
from app import DEPLOYMENTS_ROUTE
from tests.utils import create_bucket_tests

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
    #create_bucket_tests(app, TEST_BUCKET_NAME)
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
    assert response.status_code == 201
    assert response.json.get("message") == "Deployment successful"
    assert 'errors' not in response.json
