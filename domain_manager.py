import boto3
from botocore.exceptions import ClientError
from certificate_manager import CertificateManager


class DomainManager:
    def __init__(self):
        self.route53domains_client = boto3.client('route53domains')
        self.cert_manager = CertificateManager()

    def purchase_domain(self, domain_name: str, contact_info: dict):
        try:
            response = self.route53domains_client.register_domain(
                DomainName=domain_name,
                DurationInYears=1,
                AdminContact=contact_info,
                RegistrantContact=contact_info,
                BillingContact=contact_info,
                TechContact=contact_info,
                AutoRenew=False,
                PrivacyProtectAdminContact=True,
                PrivacyProtectRegistrantContact=True,
                PrivacyProtectTechContact=True,
                PrivacyProtectBillingContact=True
            )
            print(f"Domain {domain_name} registration initiated. Status: {response['OperationId']}")
            return response['OperationId']
        except ClientError as e:
            print(f"{e}")
            raise e

    def get_operation_detail(self, operation_id):
        try:
            response = self.route53domains_client.get_operation_detail(OperationId=operation_id)
            print(f"Operation details for {operation_id}: {response}")
            return response
        except ClientError as e:
            print(f"An error occurred while retrieving operation details: {e}")
            return None

    def create_certificate_for_domain(self, domain_name):
        return self.cert_manager.request_certificate_with_validation(domain_name)


if __name__ == "__main__":
    domain_manager = DomainManager()

    contact = {
        'FirstName': 'John',
        'LastName': 'Doe',
        'ContactType': 'PERSON',
        'OrganizationName': 'Example Org',
        'AddressLine1': 'TLV',
        'City': 'TLV',
        'CountryCode': 'IL',
        'ZipCode': '3522222',
        'PhoneNumber': '+972505554444',
        'Email': 'myemail@gmail.com'
    }

    domain = "example.com"

    # Purchase domain
    operation_id = domain_manager.purchase_domain(domain, contact)

    # Create certificate for the purchased domain
    certificate_arn = domain_manager.create_certificate_for_domain(domain)
