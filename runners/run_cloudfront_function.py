#!/usr/bin/env python3
"""
Playground runner — create, inspect, or delete a CloudFront viewer-request Function.

Usage:
    python run_cloudfront_function.py --action create --name my-fn --routing-type geo
    python run_cloudfront_function.py --action create --name my-fn --routing-type ab
    python run_cloudfront_function.py --action delete --name my-fn
"""
import argparse
import sys

sys.path.insert(0, '..')

from cloudfront_function_manager import CloudFrontFunctionManager  # noqa: E402
from viewer_request_templates import ROUTING_TYPES, build_function_code  # noqa: E402

SAMPLE_NAME = 'playground-viewer-request'


def run_create(name: str, routing_type: str, routing_config: dict | None = None) -> str:
    code = build_function_code(routing_type, routing_config)
    print(f"[run_cloudfront_function] generated code ({routing_type}):\n{code}\n")
    arn = CloudFrontFunctionManager().get_or_create_function(name, code)
    print(f"[run_cloudfront_function] CloudFront Function ARN: {arn}")
    return arn


def run_delete(name: str) -> None:
    CloudFrontFunctionManager().delete_function(name)
    print(f"[run_cloudfront_function] deleted function: {name}")


def main():
    parser = argparse.ArgumentParser(description='CloudFront Function playground runner')
    parser.add_argument('--action', choices=['create', 'delete'], default='create',
                        help='create or delete the CloudFront Function')
    parser.add_argument('--name', default=SAMPLE_NAME,
                        help='CloudFront Function name')
    parser.add_argument('--routing-type', default='geo', choices=list(ROUTING_TYPES),
                        help='routing template to use when creating')
    args = parser.parse_args()

    if args.action == 'create':
        run_create(args.name, args.routing_type)
    else:
        run_delete(args.name)


if __name__ == '__main__':
    main()
