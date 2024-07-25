import time
import unittest
from unittest.mock import patch
from moto import mock_aws
import boto3
from domain_manager import DomainManager
from cloudfront_manager import CloudFrontManager
from route53_manager import Route53Manager
from deployment_manager import DeploymentManager
from certificate_manager import CertificateManager


class TestDeploymentManager(unittest.TestCase):

    @mock_aws
    def setUp(self):
        # Patching sleep to speed up tests
        patcher = patch('time.sleep', return_value=None)
        self.addCleanup(patcher.stop)
        patcher.start()

        # Create necessary AWS resources for tests
        self.route53_client = boto3.client('route53')
        self.acm_client = boto3.client('acm')
        self.cloudfront_client = boto3.client('cloudfront')
        self.route53domains_client = boto3.client('route53domains')

        # Create a dummy hosted zone
        self.hosted_zone = self.route53_client.create_hosted_zone(
            Name='example.com',
            CallerReference=str(time.time())
        )

        # Create a dummy certificate
        self.certificate = self.acm_client.request_certificate(
            DomainName='example.com',
            ValidationMethod='DNS'
        )

        # Create a dummy CloudFront distribution
        self.cloudfront_distribution = self.cloudfront_client.create_distribution(
            DistributionConfig={
                'CallerReference': str(time.time()),
                'Aliases': {'Quantity': 1, 'Items': ['example.com']},
                'DefaultRootObject': '',
                'Origins': {
                    'Quantity': 1,
                    'Items': [{
                        'Id': 'origin1',
                        'DomainName': 'example.com',
                        'CustomOriginConfig': {
                            'HTTPPort': 80,
                            'HTTPSPort': 443,
                            'OriginProtocolPolicy': 'https-only',
                            'OriginSslProtocols': {'Quantity': 1, 'Items': ['TLSv1.2']}
                        }
                    }]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': 'origin1',
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'TrustedSigners': {'Enabled': False, 'Quantity': 0},
                    'ForwardedValues': {'QueryString': False, 'Cookies': {'Forward': 'none'}},
                    'MinTTL': 0
                },
                'Comment': 'Test distribution',
                'Enabled': True,
                'ViewerCertificate': {
                    'CloudFrontDefaultCertificate': True,
                    'MinimumProtocolVersion': 'TLSv1.2_2021'
                }
            }
        )

    @patch.object(DomainManager, 'purchase_domain', return_value='mock-operation-id')
    @patch.object(DomainManager, 'get_operation_detail', return_value={'Status': 'SUCCESSFUL'})
    @patch.object(DomainManager, 'create_certificate_for_domain', return_value='mock-certificate-arn')
    @patch.object(CertificateManager, 'get_certificate', return_value={'Status': 'ISSUED'})
    @patch.object(CloudFrontManager, 'create_distribution',
                  return_value=('mock-distribution-id', 'mock.cloudfront.net'))
    @patch.object(Route53Manager, 'create_hosted_zone', return_value='mock-hosted-zone-id')
    @patch.object(Route53Manager, 'add_record_to_hosted_zone')
    def test_deploy_domain(self, mock_add_record_to_hosted_zone, mock_create_hosted_zone, mock_create_distribution,
                           mock_get_certificate, mock_create_certificate_for_domain, mock_get_operation_detail,
                           mock_purchase_domain):
        deployment_manager = DeploymentManager()

        contact_info = {
            'FirstName': 'John',
            'LastName': 'Doe',
            'ContactType': 'PERSON',
            'OrganizationName': 'Example Org',
            'AddressLine1': 'TLV',
            'City': 'TLV',
            'CountryCode': 'IL',
            'ZipCode': '3522222',
            'PhoneNumber': '+972508777733',
            'Email': 'myemail@gmail.com',
        }

        domain_name = "example.com"
        origin = {
            'Id': 'myElasticBeanstalkApp',
            'DomainName': 'myapp.elasticbeanstalk.com',
            'CustomOriginConfig': {
                'HTTPPort': 80,
                'HTTPSPort': 443,
                'OriginProtocolPolicy': 'https-only',
                'OriginSslProtocols': ['TLSv1.2']
            }
        }

        deployment_manager.deploy_domain(domain_name, contact_info, origin)

        mock_purchase_domain.assert_called_once_with(domain_name, contact_info)
        mock_create_certificate_for_domain.assert_called_once_with(domain_name)
        mock_get_certificate.assert_called_once_with('mock-certificate-arn')
        mock_create_distribution.assert_called_once_with(domain_name, 'mock-certificate-arn', origin)
        mock_create_hosted_zone.assert_called_once_with(domain_name)
        mock_add_record_to_hosted_zone.assert_called_once_with('mock-hosted-zone-id', domain_name, 'mock.cloudfront.net')


if __name__ == '__main__':
    unittest.main()
