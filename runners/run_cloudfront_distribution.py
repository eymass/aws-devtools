#!/usr/bin/env python3
"""
Playground runner — create or delete a CloudFront distribution backed by S3 static website.

Prerequisites for create:
  - A valid ACM certificate ARN in us-east-1  (use run_acm_certificate.py)
  - An S3 static-website endpoint (use run_s3_bucket.py and enable website hosting)

Usage:
    python run_cloudfront_distribution.py --action create \\
        --domain playground.example.com \\
        --cert-arn arn:aws:acm:us-east-1:123456789012:certificate/abc \\
        --s3-url playground-bucket.s3-website-us-east-1.amazonaws.com

    python run_cloudfront_distribution.py --action delete --domain playground.example.com
"""
import argparse
import sys

sys.path.insert(0, '..')

from cloudfront_manager import CloudFrontManager  # noqa: E402
from api.deployments_statics import DeploymentStatics  # noqa: E402

SAMPLE_DOMAIN = 'playground.example.com'
SAMPLE_CERT_ARN = 'arn:aws:acm:us-east-1:123456789012:certificate/placeholder'
SAMPLE_S3_URL = 'playground-bucket.s3-website-us-east-1.amazonaws.com'


def run_create(
    domain_name: str,
    certificate_arn: str,
    s3_website_url: str,
    viewer_request_arn: str | None = None,
) -> tuple[str, str]:
    origins = DeploymentStatics.get_s3_website_origins(s3_website_url)
    default_cache_behavior = DeploymentStatics.get_s3_optimized_default_cache_behavior(
        s3_website_url,
        viewer_request_arn=viewer_request_arn,
    )
    cache_behaviors = DeploymentStatics.get_empty_cache_behaviors()

    dist_id, dist_domain = CloudFrontManager().create_distribution(
        domain_name, certificate_arn, origins, default_cache_behavior, cache_behaviors,
    )
    print(f"[run_cloudfront_distribution] Distribution ID    : {dist_id}")
    print(f"[run_cloudfront_distribution] Distribution domain: {dist_domain}")
    return dist_id, dist_domain


def run_delete(domain_name: str) -> None:
    CloudFrontManager().remove_distribution_by_domain(domain_name)
    print(f"[run_cloudfront_distribution] deleted distribution for: {domain_name}")


def main():
    parser = argparse.ArgumentParser(description='CloudFront distribution playground runner')
    parser.add_argument('--action', choices=['create', 'delete'], default='create',
                        help='create or delete the distribution')
    parser.add_argument('--domain', default=SAMPLE_DOMAIN,
                        help='custom domain name / CloudFront alias')
    parser.add_argument('--cert-arn', default=SAMPLE_CERT_ARN,
                        help='ACM certificate ARN (us-east-1, required for create)')
    parser.add_argument('--s3-url', default=SAMPLE_S3_URL,
                        help='S3 static-website endpoint (no http:// prefix)')
    parser.add_argument('--viewer-request-arn', default=None,
                        help='CloudFront Function ARN to attach as viewer-request (optional)')
    args = parser.parse_args()

    if args.action == 'create':
        run_create(args.domain, args.cert_arn, args.s3_url, args.viewer_request_arn)
    else:
        run_delete(args.domain)


if __name__ == '__main__':
    main()
