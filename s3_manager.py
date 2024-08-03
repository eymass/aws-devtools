import json
from botocore.exceptions import ClientError
import boto3
from exceptions.already_exists_exceptions import AlreadyExists


class S3Manager:
    def __init__(self):
        self.s3 = boto3.client('s3')

    def create_bucket(self, bucket_name):
        # check if bucket exists
        buckets = self.s3.list_buckets()
        for bucket in buckets['Buckets']:
            if bucket['Name'] == bucket_name:
                msg = f"Bucket with name {bucket_name} already exists"
                print(msg)
                raise AlreadyExists(msg)
        print(f"Creating bucket {bucket_name}")
        result = self.s3.create_bucket(Bucket=bucket_name, ACL='public-read')
        print(result)
        print(f"Enabling public access block for bucket {bucket_name}")
        response = self.s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
        print(response)
        self.add_public_policy(bucket_name)
        return {"bucket_name": bucket_name, "result": result, "url": result['Location']}

    def add_public_policy(self, bucket_name):
        bucket_policy = {
            'Version': '2012-10-17',
            'Statement': [{
                'Sid': 'AddPerm',
                'Effect': 'Allow',
                'Principal': '*',
                'Action': 's3:GetObject',
                'Resource': f'arn:aws:s3:::{bucket_name}/*'
            }]
        }
        bucket_policy_string = json.dumps(bucket_policy)

        try:
            self.s3.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy_string)
        except ClientError as e:
            print(f"Error applying bucket policy: {e}")
            return False

    def delete_bucket(self, bucket_name):
        try:
            print(f"Emptying bucket {bucket_name}")
            result = self.empty_bucket(bucket_name)
            print(result)
        except Exception as e:
            print(f"Failed to empty bucket {bucket_name}")
            raise e

        try:
            print(f"Deleting bucket {bucket_name}")
            result = self.s3.delete_bucket(Bucket=bucket_name)
            print(result)
        except Exception as e:
            print(f"Failed to delete bucket {bucket_name}")
            raise e

    def empty_bucket(self, bucket_name):
        response = self.s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for item in response['Contents']:
                self.s3.delete_object(Bucket=bucket_name, Key=item['Key'])
        return response

    def upload_file(self, bucket_name, file_path, key):
        self.s3.upload_file(file_path, bucket_name, key)

    def download_file(self, bucket_name, key, file_path):
        self.s3.download_file(bucket_name, key, file_path)

    def delete_file(self, bucket_name, key):
        self.s3.delete_object(Bucket=bucket_name, Key=key)
