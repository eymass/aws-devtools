#!/usr/bin/env python3
"""
Playground runner — deploy an S3 static-website bucket behind CloudFront.

Mirrors the `POST /statics/deploy` endpoint (api/deployments.py) but invokes
DeploymentManager.deploy_static_domain() directly so it can be driven from the
command line without running Flask + Celery. Makes real AWS calls.

Viewer-request is enabled by default. When --viewer-request-function-code is
not supplied, a CloudFront Function is generated from --routing-type using
viewer_request_templates.build_function_code (geo/ab/utm/ip/device/path/composite).

Prerequisites:
  - AWS credentials in the environment (boto3 default chain)
  - An S3 bucket with static-website hosting enabled (see run_s3_bucket.py)
  - Route 53 hosted zone for the domain if --no-purchase-domain is used and
    the domain is already owned by the account; otherwise domain registration
    will be initiated (can take minutes to complete)

Usage:
    python run_static_deploy.py \\
        --domain static.example.com \\
        --s3-url my-static-site.s3-website-us-east-1.amazonaws.com \\
        --routing-type geo

    # Disable viewer-request entirely:
    python run_static_deploy.py --domain x.example.com \\
        --s3-url x.s3-website-us-east-1.amazonaws.com --no-viewer-request

    # Supply a fully custom CloudFront Function body:
    python run_static_deploy.py --domain x.example.com \\
        --s3-url x.s3-website-us-east-1.amazonaws.com \\
        --viewer-request-function-code ./my_fn.js
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, '..')

from deployment_manager import DeploymentManager  # noqa: E402

SAMPLE_DOMAIN = 'evestmena.com'
SAMPLE_S3_URL = 'mrkt-ui-eymas-test.s3-website-us-east-1.amazonaws.com'

DEFAULT_CONTACT_INFO = {
    'FirstName': 'Jane',
    'LastName': 'Doe',
    'ContactType': 'PERSON',
    'OrganizationName': 'Acme Corp',
    'AddressLine1': '123 Main St',
    'City': 'New York',
    'CountryCode': 'US',
    'ZipCode': '10001',
    'PhoneNumber': '+1.2125551234',
    'Email': 'jane.doe@example.com',
}


def _load_file_if_path(value: str | None) -> str | None:
    """If value is a path to an existing file, return its contents; else return value as-is."""
    if not value:
        return None
    p = Path(value)
    if p.is_file():
        return p.read_text()
    return value


def _load_json_if_path(value: str | None) -> dict | None:
    if not value:
        return None
    p = Path(value)
    raw = p.read_text() if p.is_file() else value
    return json.loads(raw)


def run_deploy(
    domain_name: str,
    s3_website_url: str,
    enable_viewer_request: bool,
    routing_type: str | None,
    viewer_request_function_code: str | None,
    routing_config: dict | None,
    viewer_request_function_name: str | None,
    purchase_domain: bool,
    contact_info: dict,
) -> dict | None:
    print(f"[run_static_deploy] domain={domain_name} s3_url={s3_website_url} "
          f"enable_viewer_request={enable_viewer_request} routing_type={routing_type} "
          f"purchase_domain={purchase_domain}")

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

    print(f"[run_static_deploy] result: {result}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Static S3+CloudFront deployment runner (mirrors POST /statics/deploy)'
    )
    parser.add_argument('--domain', default=SAMPLE_DOMAIN,
                        help='custom domain name / CloudFront alias')
    parser.add_argument('--s3-url', default=SAMPLE_S3_URL,
                        help='S3 static-website endpoint (no http:// prefix)')

    # viewer-request: on by default per task spec; allow explicit opt-out.
    vr_group = parser.add_mutually_exclusive_group()
    vr_group.add_argument('--viewer-request', dest='enable_viewer_request',
                          action='store_true', default=True,
                          help='attach a CloudFront viewer-request Function (default)')
    vr_group.add_argument('--no-viewer-request', dest='enable_viewer_request',
                          action='store_false',
                          help='disable viewer-request function attachment')

    parser.add_argument('--routing-type', default='geo',
                        choices=['geo', 'ab', 'utm', 'ip', 'device', 'path', 'composite'],
                        help='template used to generate the viewer-request function body')
    parser.add_argument('--routing-config',
                        help='inline JSON or path to a JSON file consumed by build_function_code')
    parser.add_argument('--viewer-request-function-code',
                        help='inline JS or path to a .js file; overrides --routing-type')
    parser.add_argument('--viewer-request-function-name',
                        help='explicit CF Function name; defaults to <slug>-viewer-request')

    # domain ownership: default to no purchase for runner safety.
    dom_group = parser.add_mutually_exclusive_group()
    dom_group.add_argument('--purchase-domain', dest='purchase_domain',
                           action='store_true',
                           help='register the domain via Route53 if not owned')
    dom_group.add_argument('--no-purchase-domain', dest='purchase_domain',
                           action='store_false', default=False,
                           help='assume the domain is already owned (default)')

    parser.add_argument('--contact-info',
                        help='inline JSON or path to a JSON file with Route53 contact info')

    args = parser.parse_args()

    contact_info = _load_json_if_path(args.contact_info) or DEFAULT_CONTACT_INFO
    routing_config = _load_json_if_path(args.routing_config)
    viewer_request_function_code = _load_file_if_path(args.viewer_request_function_code)

    run_deploy(
        domain_name=args.domain,
        s3_website_url=args.s3_url,
        enable_viewer_request=args.enable_viewer_request,
        routing_type=args.routing_type,
        viewer_request_function_code=viewer_request_function_code,
        routing_config=routing_config,
        viewer_request_function_name=args.viewer_request_function_name,
        purchase_domain=args.purchase_domain,
        contact_info=contact_info,
    )


if __name__ == '__main__':
    main()
