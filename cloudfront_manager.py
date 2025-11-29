import boto3
from botocore.exceptions import ClientError
import time


class CloudFrontManager:
    def __init__(self):
        self.client = boto3.client('cloudfront')

    def list_cloudfronts(self) -> dict | None:
        try:
            distributions = self.client.list_distributions()
            return distributions
        except Exception as e:
            print(f"An error occurred: {e}")
            return

    def get_distribution_id_by_domain(self, domain_name):
        try:
            # List all distributions
            distributions = self.client.list_distributions()
            distribution_id = None

            # Find the distribution with the specified domain name
            for distribution in distributions['DistributionList']['Items']:
                if domain_name in distribution['Aliases']['Items']:
                    distribution_id = distribution['Id']
                    break

            if not distribution_id:
                print(f"No distribution found for domain: {domain_name}")
                return
            return distribution_id
        except Exception as e:
            print(f"An error occurred: {e}")
            return

    def get_distribution_config(self, distribution_id):
        try:
            dist_config = self.client.get_distribution_config(Id=distribution_id)
            return dist_config
        except Exception as e:
            print(f"An error occurred: {e}")
            return

    def disable_and_remove_distribution(self, distribution_id):
        try:
            # Get the distribution config
            dist_config = self.client.get_distribution_config(Id=distribution_id)
            etag = dist_config['ETag']
            config = dist_config['DistributionConfig']

            # Set the distribution status to Disabled
            config['Enabled'] = False

            # Update the distribution
            self.client.update_distribution(DistributionConfig=config, Id=distribution_id, IfMatch=etag)
            print(f"Distribution {distribution_id} has been disabled.")

            # Wait for the distribution to be disabled
            while True:
                dist = self.client.get_distribution(Id=distribution_id)
                if dist['Distribution']['Status'] == 'Deployed' and not dist['Distribution']['DistributionConfig'][
                    'Enabled']:
                    break
                print("Waiting for distribution to be disabled...")
                time.sleep(30)

            # Delete the distribution
            self.client.delete_distribution(Id=distribution_id, IfMatch=etag)
            print(f"Distribution {distribution_id} has been deleted.")
        except ClientError as e:
            print(f"An error occurred: {e}")

    def remove_distribution_by_domain(self, domain_name):
        print(f"Removing CloudFront distribution for domain: {domain_name}")
        try:
            distribution_id = self.get_distribution_id_by_domain(domain_name)
            if distribution_id:
                self.disable_and_remove_distribution(distribution_id)
        except Exception as e:
            print(f"An error occurred: {e}")

    def create_distribution(self, domain_name, certificate_arn, origins, default_cache_behavior, cache_behaviors):
        try:
            # Determine if the default origin is an S3 bucket
            target_origin_id = default_cache_behavior.get('TargetOriginId')
            is_s3_origin = False
            if target_origin_id:
                for origin in origins:
                    if origin.get('Id') == target_origin_id and 'S3OriginConfig' in origin:
                        is_s3_origin = True
                        break

            distribution_config = {
                'CallerReference': str(time.time()),
                'Aliases': {
                    'Quantity': 2,
                    'Items': [domain_name, "www." + domain_name]
                },
                'Origins': {
                    'Quantity': len(origins),
                    'Items': origins
                },
                'DefaultCacheBehavior': default_cache_behavior,
                'CacheBehaviors': cache_behaviors,
                'Comment': f'Distribution for {domain_name}',
                'Enabled': True,
                'ViewerCertificate': {
                    'ACMCertificateArn': certificate_arn,
                    'SSLSupportMethod': 'sni-only',
                    'MinimumProtocolVersion': 'TLSv1.2_2021'
                }
            }
            
            if is_s3_origin:
                distribution_config['DefaultRootObject'] = 'index.html'

            response = self.client.create_distribution(DistributionConfig=distribution_config)
            distribution_id = response['Distribution']['Id']
            distribution_domain_name = response['Distribution']['DomainName']
            print(f"Distribution {distribution_id} for domain {domain_name} has been created.")
            return distribution_id, distribution_domain_name
        except ClientError as e:
            print(f"An error occurred: {e}")
