from time import sleep

import boto3
from botocore.exceptions import ClientError


class CertificateManager:
    def __init__(self):
        self.client = boto3.client('acm')

    def remove_certificate_by_domain(self, domain_name):
        try:
            certificates = self.client.list_certificates()
            for cert in certificates['CertificateSummaryList']:
                cert_detail = self.client.describe_certificate(CertificateArn=cert['CertificateArn'])
                if cert_detail['Certificate']['DomainName'] == domain_name:
                    self.client.delete_certificate(CertificateArn=cert['CertificateArn'])
                    print(f"Certificate for {domain_name} has been deleted.")
                    return
            print(f"No certificate found for domain: {domain_name}")
        except ClientError as e:
            print(f"An error occurred: {e}")

    def get_certificate(self, certificate_arn):
        try:
            response = self.client.describe_certificate(CertificateArn=certificate_arn)
            return response['Certificate']
        except ClientError as e:
            print(f"An error occurred while getting the certificate: {e}")
            return None

    def create_certificate(self, domain_name):
        try:
            response = self.client.request_certificate(
                DomainName=domain_name,
                ValidationMethod='DNS'
            )
            certificate_arn = response['CertificateArn']
            print(f"Certificate request initiated for {domain_name}. Certificate ARN: {certificate_arn}")
            return certificate_arn
        except ClientError as e:
            print(f"An error occurred while creating the certificate: {e}")

    def request_certificate_with_validation(self, domain_name):
        try:
            response = self.client.request_certificate(
                DomainName=domain_name,
                ValidationMethod='DNS',
                SubjectAlternativeNames=["www."+domain_name]
            )
            certificate_arn = response['CertificateArn']
            validation_options = []
            found = False
            retries = 0
            while found is False and retries < 5:
                cert_details = self.client.describe_certificate(CertificateArn=certificate_arn)
                validation_options = cert_details['Certificate']['DomainValidationOptions']
                if len(validation_options) > 0 and 'ResourceRecord' in validation_options[0]:
                    print(f"Found DomainValidationOptions after {retries+1} retries.")
                    found = True
                retries += 1
                sleep(3)
            return certificate_arn, validation_options
        except ClientError as e:
            print(f"An error occurred while creating the certificate: {e}")
            return None, None

    def describe_certificate(self, arn):
        try:
            cert_details = self.client.describe_certificate(CertificateArn=arn)
            validation_options = cert_details['Certificate']['DomainValidationOptions']
            return arn, validation_options
        except ClientError as e:
            print(f"An error occurred while creating the certificate: {e}")
            return None, None
