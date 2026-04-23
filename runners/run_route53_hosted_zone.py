#!/usr/bin/env python3
"""
Playground runner — create or delete a Route53 hosted zone.

Usage:
    python run_route53_hosted_zone.py --action create --domain playground.example.com
    python run_route53_hosted_zone.py --action delete --domain playground.example.com
"""
import argparse
import sys

sys.path.insert(0, '..')

from route53_manager import Route53Manager  # noqa: E402

SAMPLE_DOMAIN = 'playground.example.com'


def run_create(domain_name: str) -> str:
    hosted_zone_id = Route53Manager().create_hosted_zone(domain_name)
    print(f"[run_route53_hosted_zone] hosted zone ID: {hosted_zone_id}")
    return hosted_zone_id


def run_delete(domain_name: str) -> None:
    Route53Manager().remove_hosted_zone_by_domain(domain_name)
    print(f"[run_route53_hosted_zone] deleted hosted zone for: {domain_name}")


def main():
    parser = argparse.ArgumentParser(description='Route53 hosted zone playground runner')
    parser.add_argument('--action', choices=['create', 'delete'], default='create',
                        help='create or delete the hosted zone')
    parser.add_argument('--domain', default=SAMPLE_DOMAIN,
                        help='domain name for the hosted zone')
    args = parser.parse_args()

    if args.action == 'create':
        run_create(args.domain)
    else:
        run_delete(args.domain)


if __name__ == '__main__':
    main()
