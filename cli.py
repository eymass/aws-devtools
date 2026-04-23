import argparse
from certificate_manager import CertificateManager
from cloudfront_function_manager import CloudFrontFunctionManager
from cloudfront_manager import CloudFrontManager
from route53_manager import Route53Manager


def main():
    parser = argparse.ArgumentParser(description="AWS deployment resource management tool")
    parser.add_argument("domain", help="Domain name to operate on")
    parser.add_argument("--remove-certificate", action="store_true",
                        help="Remove ACM certificate for the domain")
    parser.add_argument("--remove-cloudfront-distribution", action="store_true",
                        help="Disable and delete the CloudFront distribution for the domain")
    parser.add_argument("--remove-hosted-zone", action="store_true",
                        help="Remove Route53 hosted zone for the domain")
    parser.add_argument("--remove-viewer-function", metavar="FUNCTION_NAME",
                        default=None,
                        help="Delete a CloudFront viewer-request Function by name")
    parser.add_argument("--clean-deployment", action="store_true",
                        help="Remove all deployed resources for the domain "
                             "(distribution + cert + hosted zone)")

    args = parser.parse_args()

    acted = False

    if args.clean_deployment:
        CloudFrontManager().remove_distribution_by_domain(args.domain)
        CertificateManager().remove_certificate_by_domain(args.domain)
        Route53Manager().remove_hosted_zone_by_domain(args.domain)
        acted = True

    if args.remove_cloudfront_distribution:
        CloudFrontManager().remove_distribution_by_domain(args.domain)
        acted = True

    if args.remove_certificate:
        CertificateManager().remove_certificate_by_domain(args.domain)
        acted = True

    if args.remove_hosted_zone:
        Route53Manager().remove_hosted_zone_by_domain(args.domain)
        acted = True

    if args.remove_viewer_function:
        CloudFrontFunctionManager().delete_function(args.remove_viewer_function)
        acted = True

    if not acted:
        parser.print_help()


if __name__ == "__main__":
    main()
