"""
Example: deploy an S3 static-website bucket behind CloudFront via the deploy_static API.

POST /api/deployments/statics/deploy  →  202 {"message": "...", "jobId": "<uuid>"}
GET  /api/deployments/jobs/<jobId>    →  200 {"state": "SUCCESS", "result": {...}}

Run the Flask app and Celery worker first:
    gunicorn run:app
    celery -A celery_app.celery_app worker --loglevel=info
"""

import time
import requests

BASE_URL = "http://localhost:5200/api/deployments"

CONTACT_INFO = {
    "FirstName": "Jane",
    "LastName": "Doe",
    "ContactType": "PERSON",
    "OrganizationName": "Acme Corp",
    "AddressLine1": "123 Main St",
    "City": "New York",
    "CountryCode": "US",
    "ZipCode": "10001",
    "PhoneNumber": "+1.2125551234",
    "Email": "jane.doe@example.com",
}

payload = {
    "domain_name": "static.example.com",
    # S3 static-website endpoint (bucket must have website hosting enabled)
    "s3_website_url": "my-static-site.s3-website-us-east-1.amazonaws.com",
    "contact_info": CONTACT_INFO,
    "purchase_domain": False,  # set True to register the domain via Route53 if not owned
}

# ── 1. Kick off the background job ───────────────────────────────────────────
response = requests.post(f"{BASE_URL}/statics/deploy", json=payload)
response.raise_for_status()

data = response.json()
job_id = data["jobId"]
print(f"Deployment scheduled — jobId: {job_id}")

# ── 2. Poll until the job finishes ────────────────────────────────────────────
MAX_POLLS = 20
POLL_INTERVAL_SECONDS = 30

for attempt in range(1, MAX_POLLS + 1):
    poll = requests.get(f"{BASE_URL}/jobs/{job_id}")
    poll.raise_for_status()
    status = poll.json()
    print(f"[{attempt}/{MAX_POLLS}] state={status['state']}")

    if status["state"] == "SUCCESS":
        print("Deployment complete!")
        print(f"  distribution_id       : {status['result']['distribution_id']}")
        print(f"  distribution_domain   : {status['result']['distribution_domain_name']}")
        print(f"  domain_name           : {status['result']['domain_name']}")
        break

    if status["state"] == "FAILURE":
        print(f"Deployment failed: {status.get('error')}")
        break

    time.sleep(POLL_INTERVAL_SECONDS)
else:
    print("Timed out waiting for deployment to complete.")
