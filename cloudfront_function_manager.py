import boto3
from botocore.exceptions import ClientError


class CloudFrontFunctionManager:
    def __init__(self):
        self.client = boto3.client('cloudfront')

    def get_function(self, name: str) -> tuple[str | None, str | None]:
        """Return (arn, etag) of the LIVE function, or (None, None) if absent."""
        try:
            response = self.client.describe_function(Name=name, Stage='LIVE')
            arn = response['FunctionSummary']['FunctionMetadata']['FunctionARN']
            return arn, response['ETag']
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchFunctionExists':
                return None, None
            raise

    def get_or_create_function(self, name: str, code: str) -> str:
        """Return the LIVE ARN — reuse existing function or create and publish a new one."""
        arn, _ = self.get_function(name)
        if arn:
            print(f"[CloudFrontFunctionManager] reusing {name} arn={arn}")
            return arn
        return self._create_and_publish(name, code)

    def _create_and_publish(self, name: str, code: str) -> str:
        create_resp = self.client.create_function(
            Name=name,
            FunctionConfig={
                'Comment': f'Viewer-request routing for {name}',
                'Runtime': 'cloudfront-js-2.0',
            },
            FunctionCode=code.encode('utf-8'),
        )
        etag = create_resp['ETag']
        print(f"[CloudFrontFunctionManager] created {name}")
        self.client.publish_function(Name=name, IfMatch=etag)
        print(f"[CloudFrontFunctionManager] published {name}")
        arn, _ = self.get_function(name)
        return arn

    def delete_function(self, name: str) -> None:
        """Delete the function. Must not be attached to any live distribution when called."""
        try:
            dev_resp = self.client.describe_function(Name=name, Stage='DEVELOPMENT')
            etag = dev_resp['ETag']
            self.client.delete_function(Name=name, IfMatch=etag)
            print(f"[CloudFrontFunctionManager] deleted {name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchFunctionExists':
                return
            print(f"[CloudFrontFunctionManager] error deleting {name}: {e}")
            raise
