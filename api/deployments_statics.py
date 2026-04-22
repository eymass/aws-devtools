
class DeploymentStatics:
    # AWS managed cache/origin-request policy IDs
    CACHE_POLICY_CACHING_DISABLED = '4135ea2d-6df8-44a3-9df3-4b5a84be39ad'
    CACHE_POLICY_CACHING_OPTIMIZED = '658327ea-f89d-4fab-a63d-7e88639e58f6'
    ORIGIN_REQUEST_POLICY_ALL_VIEWER = '216adef6-5c7f-47e4-b989-5492eafa07d3'

    @staticmethod
    def get_origins(static_files_bucket: str, environment_url: str):
        return [
        {
            'Id': static_files_bucket,
            'DomainName': static_files_bucket,
            'OriginPath': '',
            'CustomHeaders': {
                'Quantity': 0
            },
            'S3OriginConfig': {
                'OriginAccessIdentity': ''
            },
            'ConnectionAttempts': 3,
            'ConnectionTimeout': 10,
            'OriginShield': {
                'Enabled': False
            },
            'OriginAccessControlId': ''
        },
        {
        'Id': environment_url,
        'DomainName': environment_url,
        'CustomOriginConfig': {
            'HTTPPort': 80,
            'HTTPSPort': 443,
            'OriginProtocolPolicy': 'http-only',
            'OriginSslProtocols': {
                'Quantity': 4,
                'Items': [
                  'SSLv3',
                  'TLSv1',
                  'TLSv1.1',
                  'TLSv1.2'
                ]
          }
        }
    }]

    @staticmethod
    def get_cache_behaviors(static_files_bucket: str, path_pattern: str = '/assets/imgs/*'):
        return {
        'Quantity': 1,
        'Items': [
            {
                'PathPattern': path_pattern,
                'TargetOriginId': static_files_bucket,
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
                    'Quantity': 2,
                    'Items': [
                        'HEAD',
                        'GET'
                    ],
                    'CachedMethods': {
                        'Quantity': 2,
                        'Items': [
                            'HEAD',
                            'GET'
                        ]
                    }
                },
                'SmoothStreaming': False,
                'Compress': True,
                'LambdaFunctionAssociations': {
                    'Quantity': 0
                },
                'FunctionAssociations': {
                    'Quantity': 0
                },
                'FieldLevelEncryptionId': '',
                'CachePolicyId': DeploymentStatics.CACHE_POLICY_CACHING_OPTIMIZED
            }
        ]
    }

    @staticmethod
    def get_default_cache_behavior(environment_url: str):
        return {
        'TargetOriginId': environment_url,
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
            'Quantity': 3,
            'Items': [
                'HEAD',
                'GET',
                'OPTIONS'
            ],
            'CachedMethods': {
                'Quantity': 2,
                'Items': [
                    'HEAD',
                    'GET'
                ]
            }
        },
        'SmoothStreaming': False,
        'Compress': True,
        'LambdaFunctionAssociations': {
            'Quantity': 0
        },
        'FunctionAssociations': {
            'Quantity': 0
        },
        'FieldLevelEncryptionId': '',
        'CachePolicyId': DeploymentStatics.CACHE_POLICY_CACHING_DISABLED,
        'OriginRequestPolicyId': DeploymentStatics.ORIGIN_REQUEST_POLICY_ALL_VIEWER
    }

    @staticmethod
    def get_s3_website_origins(s3_website_url: str):
        """Single CustomOrigin pointing to an S3 static-website endpoint (HTTP only)."""
        # S3 website endpoints only support HTTP, so CloudFront must use http-only protocol
        domain = s3_website_url.removeprefix('http://').removeprefix('https://')
        return [
            {
                'Id': domain,
                'DomainName': domain,
                'OriginPath': '',
                'CustomHeaders': {'Quantity': 0},
                'CustomOriginConfig': {
                    'HTTPPort': 80,
                    'HTTPSPort': 443,
                    'OriginProtocolPolicy': 'http-only',
                    'OriginSslProtocols': {
                        'Quantity': 3,
                        'Items': ['TLSv1', 'TLSv1.1', 'TLSv1.2']
                    },
                    'OriginReadTimeout': 30,
                    'OriginKeepaliveTimeout': 5,
                },
                'ConnectionAttempts': 3,
                'ConnectionTimeout': 10,
                'OriginShield': {'Enabled': False},
            }
        ]

    @staticmethod
    def get_s3_optimized_default_cache_behavior(s3_website_url: str):
        """Default cache behavior optimised for purely static S3-website content."""
        domain = s3_website_url.removeprefix('http://').removeprefix('https://')
        return {
            'TargetOriginId': domain,
            'TrustedSigners': {'Enabled': False, 'Quantity': 0},
            'TrustedKeyGroups': {'Enabled': False, 'Quantity': 0},
            'ViewerProtocolPolicy': 'redirect-to-https',
            'AllowedMethods': {
                'Quantity': 2,
                'Items': ['HEAD', 'GET'],
                'CachedMethods': {
                    'Quantity': 2,
                    'Items': ['HEAD', 'GET'],
                },
            },
            'SmoothStreaming': False,
            'Compress': True,
            'LambdaFunctionAssociations': {'Quantity': 0},
            'FunctionAssociations': {'Quantity': 0},
            'FieldLevelEncryptionId': '',
            'CachePolicyId': DeploymentStatics.CACHE_POLICY_CACHING_OPTIMIZED,
        }

    @staticmethod
    def get_empty_cache_behaviors():
        """No path-specific cache behaviors — all traffic served by the default behavior."""
        return {'Quantity': 0, 'Items': []}
