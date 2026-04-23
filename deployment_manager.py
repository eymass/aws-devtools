import re
import time

from botocore.exceptions import ClientError
from certificate_manager import CertificateManager
from route53_manager import Route53Manager
from cloudfront_manager import CloudFrontManager
from cloudfront_function_manager import CloudFrontFunctionManager
from domain_manager import DomainManager
from api.deployments_statics import DeploymentStatics
from viewer_request_templates import build_function_code


class DeploymentManager:
    def __init__(self):
        self.domain_manager = DomainManager()
        self.certificate_manager = CertificateManager()
        self.route53_manager = Route53Manager()
        self.cloudfront_manager = CloudFrontManager()

    def purchase_domain(self, domain_name: str, contact_info: dict):
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

    def deploy_domain(self, domain_name: str, contact_info: dict, origins,
                      default_cache_behavior, cache_behaviors, purchase_domain):
        try:
            if purchase_domain:
                # blocking call
                # TODO switch to job
                ownership = Route53Manager().is_domain_owned(
                    domain_name=domain_name,
                )
                if "Owned" in ownership and ownership["Owned"] is True:
                    pass
                else:
                    self.purchase_domain(domain_name, contact_info)
            else:
                ownership = self.route53_manager.is_domain_owned(domain_name)
                print("Domain ownership check result:", ownership)
                if "Owned" in ownership and ownership["Owned"] is False:
                    return {"message": "Domain is not owned by the account.", "deployed": False}

            domain_name = domain_name.lower()
            # Step 2: Create certificate for the domain
            certificate_arn, validation_options = self.domain_manager.create_certificate_for_domain(domain_name)
            print(f"Certificate created for domain {domain_name} with ARN: {certificate_arn}")
            print(f"Options {validation_options}")

            if not validation_options:
                raise Exception("No validation options found for the certificate.")
            # Step 3: Create the CNAME record for DNS validation
            for option in validation_options:
                if 'ResourceRecord' in option:
                    self.route53_manager.add_cname_record(domain_name.lower(), option['ResourceRecord']['Name'], option['ResourceRecord']['Value'])
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
                print(f"Certificate result: {response}")
                if response['Status'].upper() == 'ISSUED':
                    break
                if response['Status'].upper() == 'FAILED':
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
            return {"hosted_zone_id": hosted_zone_id, "distribution_id": distribution_id, "domain_name": domain_name,
                    "distribution_domain_name": distribution_domain_name, "state": "SUCCESS"}
        except ClientError as e:
            print(f"An error occurred during deployment: {e}")

    @staticmethod
    def _viewer_request_function_name(domain_name: str) -> str:
        """Derive a valid CloudFront Function name from a domain (1-64 chars, [a-zA-Z0-9-_])."""
        slug = re.sub(r'[^a-zA-Z0-9\-_]', '-', domain_name)[:50]
        return f"{slug}-viewer-request"

    def deploy_static_domain(
        self,
        domain_name: str,
        contact_info: dict,
        s3_website_url: str,
        purchase_domain: bool,
        enable_viewer_request: bool = False,
        routing_type: str | None = None,
        viewer_request_function_code: str | None = None,
        routing_config: dict | None = None,
        viewer_request_function_name: str | None = None,
    ):
        """Deploy CloudFront in front of an S3 static-website bucket.

        Optionally attaches a CloudFront viewer-request Function for logical routing
        (geo, A/B, UTM, IP, device, path, composite). When enable_viewer_request is True
        and no viewer_request_function_code is supplied, a template is generated from
        routing_type (defaults to 'geo').
        """
        print(f"[DeploymentManager] deploy_static_domain: domain={domain_name} "
              f"s3_website_url={s3_website_url} purchase_domain={purchase_domain} "
              f"enable_viewer_request={enable_viewer_request} routing_type={routing_type}")

        viewer_request_arn = None
        if enable_viewer_request:
            fn_name = viewer_request_function_name or self._viewer_request_function_name(domain_name)
            fn_code = viewer_request_function_code or build_function_code(
                routing_type or 'geo', routing_config
            )
            print(f"[DeploymentManager] deploy_static_domain: "
                  f"creating/reusing CF function name={fn_name}")
            viewer_request_arn = CloudFrontFunctionManager().get_or_create_function(fn_name, fn_code)
            print(f"[DeploymentManager] deploy_static_domain: viewer_request_arn={viewer_request_arn}")

        origins = DeploymentStatics.get_s3_website_origins(s3_website_url)
        print(f"[DeploymentManager] deploy_static_domain: origins={origins}")

        default_cache_behavior = DeploymentStatics.get_s3_optimized_default_cache_behavior(
            s3_website_url,
            viewer_request_arn=viewer_request_arn,
        )
        print(f"[DeploymentManager] deploy_static_domain: "
              f"default_cache_behavior={default_cache_behavior}")

        cache_behaviors = DeploymentStatics.get_empty_cache_behaviors()

        result = self.deploy_domain(
            domain_name=domain_name,
            contact_info=contact_info,
            origins=origins,
            default_cache_behavior=default_cache_behavior,
            cache_behaviors=cache_behaviors,
            purchase_domain=purchase_domain,
        )
        if result and viewer_request_arn:
            result['viewer_request_function_arn'] = viewer_request_arn
        return result
