from deployment_manager import DeploymentManager


def try_me():
    deployment_manager = DeploymentManager()

    # This information is required for domain registration and SSL certificate generation.
    # If you are not purchasing a new domain, ensure the domain is registered in AWS Route53.
    contact_info = {
        'FirstName': 'John',
        'LastName': 'Doe',
        'ContactType': 'PERSON',
        'OrganizationName': 'Example Org',
        'AddressLine1': '123 Main St',
        'City': 'Anytown',
        'CountryCode': 'IL',
        'ZipCode': '3342501',
        'PhoneNumber': '+1.1234567890',
        'Email': 'eymaslive@gmail.com'
    }

    # Replace with your domain name. This domain must be managed in Amazon Route 53
    # for the deployment script to work, as it needs to add records for certificate validation
    # and to point to the CloudFront distribution.
    domain_name = "publab8.com"

    # S3 bucket configuration
    s3_bucket_name = 'mrkt-ui-eymas'
    s3_origin_id = f's3-{s3_bucket_name}'
    s3_domain_name = f'{s3_bucket_name}.s3.amazonaws.com'

    # CloudFront origins
    origins = [
        {
            'Id': s3_origin_id,
            'DomainName': s3_domain_name,
            'OriginPath': '',
            'CustomHeaders': {
                'Quantity': 0
            },
            'S3OriginConfig': {
                # For restricting access to the S3 bucket from CloudFront,
                # it is recommended to use Origin Access Control (OAC).
                # The OriginAccessControlId would be set here.
                # For simplicity, this example uses a public S3 bucket.
                'OriginAccessIdentity': ''
            },
            'ConnectionAttempts': 3,
            'ConnectionTimeout': 10,
            'OriginShield': {
                'Enabled': False
            },
            'OriginAccessControlId': ''
        }
    ]

    # CloudFront default cache behavior
    default_cache_behavior = {
        'TargetOriginId': s3_origin_id,
        'TrustedSigners': {
            'Enabled': False,
            'Quantity': 0
        },
        'TrustedKeyGroups': {
            'Enabled': False,
            'Quantity': 0
        },
        'ViewerProtocolPolicy': 'redirect-to-https',
        'AllowedMethods': {
            'Quantity': 2,  # GET, HEAD
            'Items': ['GET', 'HEAD'],
            'CachedMethods': {
                'Quantity': 2,
                'Items': ['GET', 'HEAD']
            }
        },
        'Compress': True,
        # Using a managed cache policy for caching optimized for S3 origins.
        # 'CachePolicyId': '658327ea-f89d-4fab-a63d-7e88639e58f6' # CachingOptimized
    }

    # No specific cache behaviors needed for a simple static site, so this is empty.
    cache_behaviors = {
        'Quantity': 0,
        'Items': []
    }

    # Call the deployment manager
    # `purchase_domain` is set to False, assuming you already own the domain
    # and it is managed in AWS Route 53.
    deployment_manager.deploy_domain(domain_name=domain_name,
                                     contact_info=contact_info,
                                     origins=origins,
                                     default_cache_behavior=default_cache_behavior,
                                     cache_behaviors=cache_behaviors,
                                     purchase_domain=False)


try_me()
