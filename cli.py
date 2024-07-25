import argparse
from certificate_manager import CertificateManager
from route53_manager import Route53Manager
from cloudfront_manager import CloudFrontManager


def main():
    parser = argparse.ArgumentParser(description="AWS Certificate Manager and Route 53 Management Tool")
    parser.add_argument("domain", help="Domain name to remove certificate and hosted zone")
    parser.add_argument("--remove-certificate", action="store_true", help="Remove certificate for the domain")
    parser.add_argument("--clean-deployment", action="store_true", help="Remove domains' all deployed resources")
    parser.add_argument("--remove-hosted-zone", action="store_true", help="Remove hosted zone for the domain")

    args = parser.parse_args()

    if args.clean_deployment:
        cf_manager = CloudFrontManager()
        cf_manager.remove_distribution_by_domain(args.domain)
        cert_manager = CertificateManager()
        cert_manager.remove_certificate_by_domain(args.domain)
        route53_manager = Route53Manager()
        route53_manager.remove_hosted_zone_by_domain(args.domain)

    if args.remove_cloudfront_distribution:
        cf_manager = CloudFrontManager()
        cf_manager.remove_distribution_by_domain(args.domain)

    if args.remove_certificate:
        cert_manager = CertificateManager()
        cert_manager.remove_certificate_by_domain(args.domain)

    if args.remove_hosted_zone:
        route53_manager = Route53Manager()
        route53_manager.remove_hosted_zone_by_domain(args.domain)

    if not (args.remove_certificate or args.remove_hosted_zone):
        print("Please specify at least one operation: --remove-certificate or --remove-hosted-zone")


if __name__ == "__main__":
    main()
