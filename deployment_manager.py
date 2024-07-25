import time

import boto3
from botocore.exceptions import ClientError
from certificate_manager import CertificateManager
from route53_manager import Route53Manager
from cloudfront_manager import CloudFrontManager
from domain_manager import DomainManager


class DeploymentManager:
    def __init__(self):
        self.domain_manager = DomainManager()
        self.certificate_manager = CertificateManager()
        self.route53_manager = Route53Manager()
        self.cloudfront_manager = CloudFrontManager()

    def purchase_domain(self, domain_name, contact_info):
        # Step 1: Purchase domain
        operation_id = self.domain_manager.purchase_domain(domain_name, contact_info)
        print(f"Domain {domain_name} purchase initiated with operation ID: {operation_id}")

        # Wait for domain registration to complete (this can take some time)
        # Here we are just simulating a wait time. In practice, you might want to check the status of the operation.
        time.sleep(60)  # wait for domain registration to complete

        count = 0
        max_retries = 10
        # poll for the status of the domain registration operation
        while True:
            response = self.domain_manager.get_operation_detail(operation_id)
            if response['Status'] == 'SUCCESSFUL':
                break
            if response['Status'] == 'FAILED':
                raise Exception("Domain registration failed.")
            if count >= max_retries:
                raise Exception("Timed out waiting for domain registration.")
            print("Waiting for domain registration to complete...")
            time.sleep(30)
        return

    def deploy_domain(self, domain_name, contact_info, origins,
                      default_cache_behavior, cache_behaviors, purchase_domain):
        try:
            if purchase_domain:
                self.purchase_domain(domain_name, contact_info)

            # Step 2: Create certificate for the domain
            certificate_arn, validation_options = self.domain_manager.create_certificate_for_domain(domain_name)
            print(f"Certificate created for domain {domain_name} with ARN: {certificate_arn}")
            print(f"Options {validation_options}")

            if not validation_options:
                raise Exception("No validation options found for the certificate.")
            # Step 3: Create the CNAME record for DNS validation
            for option in validation_options:
                if 'ResourceRecord' in option:
                    self.route53_manager.add_cname_record(domain_name, option['ResourceRecord']['Name'], option['ResourceRecord']['Value'])
                    print(f"CNAME record created for DNS validation: {option['ResourceRecord']['Name']} -> {option['ResourceRecord']['Value']}")
                else:
                    print(f"No CNAME record found in validation option {option}.")

            # Wait for the certificate to be issued
            time.sleep(60)

            # check the status of the certificate
            count = 0
            max_retries = 10
            while True:
                response = self.certificate_manager.get_certificate(certificate_arn)
                if response['Status'] == 'ISSUED':
                    break
                if response['Status'] == 'FAILED':
                    raise Exception("Certificate issuance failed.")
                if count >= max_retries:
                    raise Exception("Timed out waiting for certificate issuance.")
                print("Waiting for certificate to be issued...")
                time.sleep(30)

            # Step 3: Create CloudFront distribution for the domain
            distribution_id, distribution_domain_name = self.cloudfront_manager.create_distribution(
                domain_name, certificate_arn, origins, default_cache_behavior, cache_behaviors)
            print(
                f"CloudFront distribution created with ID: {distribution_id} and domain name: {distribution_domain_name}")

            hosted_zone_id = self.route53_manager.get_hosted_zone_id_by_domain(domain_name)
            # Step 5: Add records to the hosted zone pointing to the CloudFront distribution
            self.route53_manager.add_record_to_hosted_zone(hosted_zone_id, domain_name, distribution_domain_name)
            print(
                f"Record added to hosted zone {hosted_zone_id} for domain {domain_name} "
                f"pointing to {distribution_domain_name}")

            print("Deployment successful!")
        except ClientError as e:
            print(f"An error occurred during deployment: {e}")
