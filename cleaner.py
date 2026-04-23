"""
DeploymentCleaner — removes all AWS resources created by deploy_static_domain.

Deletion order (safe for dependencies):
  1. CloudFront distribution  (disable → delete; removes CF Function associations)
  2. CloudFront viewer-request Function  (safe once distribution is gone)
  3. ACM certificate
  4. Route53 hosted zone  (deletes all DNS records inside it)
"""
import argparse

from certificate_manager import CertificateManager
from cloudfront_function_manager import CloudFrontFunctionManager
from cloudfront_manager import CloudFrontManager
from route53_manager import Route53Manager


class DeploymentCleaner:
    def __init__(self):
        self.cf_manager = CloudFrontManager()
        self.cf_fn_manager = CloudFrontFunctionManager()
        self.cert_manager = CertificateManager()
        self.route53_manager = Route53Manager()

    def clean_static_deployment(
        self,
        domain_name: str,
        viewer_request_function_name: str | None = None,
    ) -> dict:
        """Remove every AWS resource tied to a static deployment for domain_name.

        Args:
            domain_name: The custom domain (e.g. 'static.example.com').
            viewer_request_function_name: CloudFront Function name to delete after the
                distribution is gone.  When omitted, function cleanup is skipped.

        Returns:
            dict mapping each resource type to 'removed' or 'error: <message>'.
        """
        results = {}

        print(f"[DeploymentCleaner] === cleaning deployment for {domain_name} ===")

        # 1. CloudFront distribution
        print(f"[DeploymentCleaner] removing CloudFront distribution for {domain_name}")
        try:
            self.cf_manager.remove_distribution_by_domain(domain_name)
            results['cloudfront_distribution'] = 'removed'
        except Exception as e:
            results['cloudfront_distribution'] = f'error: {e}'
            print(f"[DeploymentCleaner] cloudfront error: {e}")

        # 2. CloudFront viewer-request Function (safe now that distribution is gone)
        if viewer_request_function_name:
            print(f"[DeploymentCleaner] deleting CF function {viewer_request_function_name}")
            try:
                self.cf_fn_manager.delete_function(viewer_request_function_name)
                results['viewer_request_function'] = 'removed'
            except Exception as e:
                results['viewer_request_function'] = f'error: {e}'
                print(f"[DeploymentCleaner] function error: {e}")

        # 3. ACM certificate
        print(f"[DeploymentCleaner] removing ACM certificate for {domain_name}")
        try:
            self.cert_manager.remove_certificate_by_domain(domain_name)
            results['acm_certificate'] = 'removed'
        except Exception as e:
            results['acm_certificate'] = f'error: {e}'
            print(f"[DeploymentCleaner] certificate error: {e}")

        # 4. Route53 hosted zone (removes all DNS records)
        print(f"[DeploymentCleaner] removing Route53 hosted zone for {domain_name}")
        try:
            self.route53_manager.remove_hosted_zone_by_domain(domain_name)
            results['route53_hosted_zone'] = 'removed'
        except Exception as e:
            results['route53_hosted_zone'] = f'error: {e}'
            print(f"[DeploymentCleaner] hosted zone error: {e}")

        print(f"[DeploymentCleaner] done: {results}")
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Remove all AWS resources for a static CloudFront deployment."
    )
    parser.add_argument("domain", help="Domain name to clean up (e.g. static.example.com)")
    parser.add_argument(
        "--function-name",
        default=None,
        help="CloudFront Function name to delete (optional)",
    )
    args = parser.parse_args()
    results = DeploymentCleaner().clean_static_deployment(
        domain_name=args.domain,
        viewer_request_function_name=args.function_name,
    )
    for resource, status in results.items():
        print(f"  {resource}: {status}")


if __name__ == "__main__":
    main()
