import time

import boto3
from botocore.exceptions import ClientError


class Route53Manager:
    def __init__(self):
        self.client = boto3.client('route53')

    def remove_hosted_zone_by_domain(self, domain_name):
        try:
            hosted_zones = self.client.list_hosted_zones()
            for zone in hosted_zones['HostedZones']:
                if domain_name in zone['Name']:
                    self.client.delete_hosted_zone(Id=zone['Id'])
                    print(f"Hosted zone for {domain_name} has been deleted.")
                    return
            print(f"No hosted zone found for domain: {domain_name}")
        except ClientError as e:
            print(f"An error occurred: {e}")

    def create_hosted_zone(self, domain_name):
        try:
            response = self.client.create_hosted_zone(
                Name=domain_name,
                CallerReference=str(time.time())
            )
            print(f"Hosted zone created for domain {domain_name} with ID: {response['HostedZone']['Id']}")
            return response['HostedZone']['Id']
        except ClientError as e:
            print(f"An error occurred: {e}")

    def add_record_to_hosted_zone(self, hosted_zone_id, domain_name,
                                  cloudfront_distribution_domain_name):
        try:
            response = self.client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    'Comment': 'Add record to point to CloudFront distribution',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': domain_name,
                                'Type': 'A',
                                'AliasTarget': {
                                    'HostedZoneId': 'Z2FDTNDATAQYW2',  # CloudFront hosted zone ID (constant)
                                    'DNSName': cloudfront_distribution_domain_name,
                                    'EvaluateTargetHealth': False
                                }
                            }
                        }
                    ]
                }
            )
            print(f"Record added to hosted zone {hosted_zone_id} for domain {domain_name} pointing to "
                  f"{cloudfront_distribution_domain_name}.")
        except ClientError as e:
            print(f"An error occurred: {e}")

    def add_cname_record(self, domain_name, cname_name, cname_value):
        try:
            hosted_zones = self.client.list_hosted_zones()
            for zone in hosted_zones['HostedZones']:
                if domain_name in zone['Name']:
                    hosted_zone_id = zone['Id']
                    response = self.client.change_resource_record_sets(
                        HostedZoneId=hosted_zone_id,
                        ChangeBatch={
                            'Comment': 'Add CNAME record for DNS validation',
                            'Changes': [
                                {
                                    'Action': 'UPSERT',
                                    'ResourceRecordSet': {
                                        'Name': cname_name,
                                        'Type': 'CNAME',
                                        'TTL': 300,
                                        'ResourceRecords': [{'Value': cname_value}]
                                    }
                                }
                            ]
                        }
                    )
                    print(
                        f"CNAME record added to hosted zone {hosted_zone_id} for DNS validation: {cname_name} -> {cname_value}.")
                    return
            print(f"No hosted zone found for domain: {domain_name}")
        except ClientError as e:
            print(f"An error occurred while adding the CNAME record: {e}")

    def get_hosted_zone_id_by_domain(self, domain_name):
        try:
            hosted_zones = self.client.list_hosted_zones()
            for zone in hosted_zones['HostedZones']:
                if domain_name in zone['Name']:
                    return zone['Id']
            print(f"No hosted zone found for domain: {domain_name}")
        except ClientError as e:
            print(f"An error occurred: {e}")
            return None
