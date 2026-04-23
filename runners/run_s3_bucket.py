#!/usr/bin/env python3
"""
Playground runner — create or delete an S3 public-website bucket.

Usage:
    python run_s3_bucket.py --action create --bucket-name my-bucket-test
    python run_s3_bucket.py --action delete --bucket-name my-bucket-test
"""
import argparse
import sys
import time

sys.path.insert(0, '..')

from s3_manager import S3Manager  # noqa: E402


def run_create(bucket_name: str) -> dict:
    result = S3Manager().create_bucket(bucket_name)
    print(f"[run_s3_bucket] created bucket={bucket_name}")
    print(f"[run_s3_bucket] result={result}")
    return result


def run_delete(bucket_name: str) -> None:
    S3Manager().delete_bucket(bucket_name)
    print(f"[run_s3_bucket] deleted bucket={bucket_name}")


def main():
    parser = argparse.ArgumentParser(description='S3 public bucket playground runner')
    parser.add_argument('--action', choices=['create', 'delete'], default='create',
                        help='create or delete the bucket')
    parser.add_argument('--bucket-name', default=f'playground-bucket-{int(time.time())}',
                        help='S3 bucket name')
    args = parser.parse_args()

    if args.action == 'create':
        run_create(args.bucket_name)
    else:
        run_delete(args.bucket_name)


if __name__ == '__main__':
    main()
