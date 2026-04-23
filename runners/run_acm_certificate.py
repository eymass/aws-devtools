#!/usr/bin/env python3
"""
Playground runner — request or delete an ACM certificate (DNS validation).

Usage:
    python run_acm_certificate.py --action create --domain playground.example.com
    python run_acm_certificate.py --action delete --domain playground.example.com

Note: ACM certificates must be in us-east-1 for CloudFront use.
"""
import argparse
import sys

sys.path.insert(0, '..')

from certificate_manager import CertificateManager  # noqa: E402

SAMPLE_DOMAIN = 'playground.example.com'


def run_create(domain_name: str) -> tuple[str, list]:
    arn, validation_options = CertificateManager().request_certificate_with_validation(domain_name)
    print(f"[run_acm_certificate] Certificate ARN  : {arn}")
    print(f"[run_acm_certificate] Validation options: {validation_options}")
    return arn, validation_options


def run_delete(domain_name: str) -> None:
    CertificateManager().remove_certificate_by_domain(domain_name)
    print(f"[run_acm_certificate] deleted certificate for: {domain_name}")


def main():
    parser = argparse.ArgumentParser(description='ACM certificate playground runner')
    parser.add_argument('--action', choices=['create', 'delete'], default='create',
                        help='create or delete the certificate')
    parser.add_argument('--domain', default=SAMPLE_DOMAIN,
                        help='domain name for the certificate')
    args = parser.parse_args()

    if args.action == 'create':
        run_create(args.domain)
    else:
        run_delete(args.domain)


if __name__ == '__main__':
    main()
