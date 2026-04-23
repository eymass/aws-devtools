import json
import time

from app import DEPLOYMENTS_ROUTE

S3_WEBSITE_URL = "my-static-site.s3-website-us-east-1.amazonaws.com"
DOMAIN_NAME = "static.example.com"
CONTACT_INFO = {
    'FirstName': 'Jane',
    'LastName': 'Doe',
    'ContactType': 'PERSON',
    'OrganizationName': 'Example Org',
    'AddressLine1': 'TLV',
    'City': 'TLV',
    'CountryCode': 'IL',
    'ZipCode': '3522222',
    'PhoneNumber': '+972.508777733',
    'Email': 'test@example.com',
}


def test_deploy_static_returns_job_id(app):
    """POST /statics/deploy returns 202 with a jobId."""
    payload = {
        "domain_name": DOMAIN_NAME,
        "contact_info": CONTACT_INFO,
        "s3_website_url": S3_WEBSITE_URL,
        "purchase_domain": False,
    }
    response = app.test_client().post(
        DEPLOYMENTS_ROUTE + "statics/deploy",
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert response.status_code == 202
    assert response.json.get("jobId") is not None
    assert 'errors' not in response.json


def test_deploy_static_poll_job(app):
    """Deploy static job can be polled via GET /jobs/<jobId>."""
    payload = {
        "domain_name": DOMAIN_NAME,
        "contact_info": CONTACT_INFO,
        "s3_website_url": S3_WEBSITE_URL,
        "purchase_domain": False,
    }
    response = app.test_client().post(
        DEPLOYMENTS_ROUTE + "statics/deploy",
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert response.status_code == 202
    job_id = response.json.get("jobId")
    assert job_id is not None

    max_count = 10
    count = 1
    while True:
        poll = app.test_client().get(DEPLOYMENTS_ROUTE + f"jobs/{job_id}")
        assert poll.status_code == 200
        state = poll.json.get("state")
        if state in ("SUCCESS", "FAILURE"):
            # Domain not owned → deployed=False is the expected terminal state
            assert state == "SUCCESS"
            assert "result" in poll.json
            break
        if count >= max_count:
            break
        count += 1
        time.sleep(8)


def test_deploy_static_missing_s3_url_returns_422(app):
    """POST /statics/deploy without s3_website_url returns 422."""
    payload = {
        "domain_name": DOMAIN_NAME,
        "contact_info": CONTACT_INFO,
        # s3_website_url omitted intentionally
    }
    response = app.test_client().post(
        DEPLOYMENTS_ROUTE + "statics/deploy",
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert response.status_code == 422


def test_deploy_static_with_viewer_request_geo_routing(app):
    """POST /statics/deploy with enable_viewer_request=True and routing_type=geo returns 202."""
    payload = {
        "domain_name": DOMAIN_NAME,
        "contact_info": CONTACT_INFO,
        "s3_website_url": S3_WEBSITE_URL,
        "purchase_domain": False,
        "enable_viewer_request": True,
        "routing_type": "geo",
        "routing_config": {"country_to_variant": {"IL": "il", "DE": "de"}},
    }
    response = app.test_client().post(
        DEPLOYMENTS_ROUTE + "statics/deploy",
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert response.status_code == 202
    assert response.json.get("jobId") is not None
    assert 'errors' not in response.json


def test_deploy_static_with_viewer_request_custom_code(app):
    """POST /statics/deploy with enable_viewer_request=True and custom code returns 202."""
    custom_code = (
        "function handler(event) { return event.request; }"
    )
    payload = {
        "domain_name": DOMAIN_NAME,
        "contact_info": CONTACT_INFO,
        "s3_website_url": S3_WEBSITE_URL,
        "purchase_domain": False,
        "enable_viewer_request": True,
        "viewer_request_function_code": custom_code,
        "viewer_request_function_name": "my-custom-fn",
    }
    response = app.test_client().post(
        DEPLOYMENTS_ROUTE + "statics/deploy",
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert response.status_code == 202
    assert response.json.get("jobId") is not None


def test_deploy_static_invalid_routing_type_returns_422(app):
    """POST /statics/deploy with an unsupported routing_type returns 422."""
    payload = {
        "domain_name": DOMAIN_NAME,
        "contact_info": CONTACT_INFO,
        "s3_website_url": S3_WEBSITE_URL,
        "purchase_domain": False,
        "enable_viewer_request": True,
        "routing_type": "not-a-real-type",
    }
    response = app.test_client().post(
        DEPLOYMENTS_ROUTE + "statics/deploy",
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert response.status_code == 422
