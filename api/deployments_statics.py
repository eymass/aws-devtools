from urllib.parse import urlparse


class DeploymentStatics:
    # AWS managed cache/origin-request policy IDs
    CACHE_POLICY_CACHING_DISABLED = '4135ea2d-6df8-44a3-9df3-4b5a84be39ad'
    CACHE_POLICY_CACHING_OPTIMIZED = '658327ea-f89d-4fab-a63d-7e88639e58f6'
    ORIGIN_REQUEST_POLICY_ALL_VIEWER = '216adef6-5c7f-47e4-b989-5492eafa07d3'

    @staticmethod
    def normalize_s3_website_domain(s3_website_url: str) -> str:
        """Extract a bare DNS hostname from an S3 static-website URL.

        CloudFront's ``Origins.Items[].DomainName`` rejects anything that is
        not a pure hostname — schemes, ports, paths, trailing slashes, and
        whitespace all trigger ``InvalidArgument: origin name must be a domain
        name``. Callers may legitimately pass any of these (the API schema
        example even includes ``http://``), so normalize here.
        """
        if not s3_website_url or not s3_website_url.strip():
            raise ValueError("s3_website_url is required")
        candidate = s3_website_url.strip()
        if "://" not in candidate:
            candidate = "http://" + candidate
        host = urlparse(candidate).hostname
        if not host:
            raise ValueError(f"Could not parse domain from s3_website_url: {s3_website_url!r}")
        return host

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
        domain = DeploymentStatics.normalize_s3_website_domain(s3_website_url)
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
    def get_viewer_request_function_associations(function_arn: str) -> dict:
        """Return a FunctionAssociations dict that attaches a viewer-request CloudFront Function."""
        return {
            'Quantity': 1,
            'Items': [
                {
                    'FunctionARN': function_arn,
                    'EventType': 'viewer-request',
                }
            ],
        }

    @staticmethod
    def get_s3_optimized_default_cache_behavior(
        s3_website_url: str,
        viewer_request_arn: str | None = None,
    ):
        """Default cache behavior optimised for purely static S3-website content.

        Pass viewer_request_arn to attach a CloudFront Function for logical routing
        (geo, A/B, UTM, IP, device, path, composite).
        """
        domain = DeploymentStatics.normalize_s3_website_domain(s3_website_url)
        function_associations = (
            DeploymentStatics.get_viewer_request_function_associations(viewer_request_arn)
            if viewer_request_arn
            else {'Quantity': 0}
        )
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
            'FunctionAssociations': function_associations,
            'FieldLevelEncryptionId': '',
            'CachePolicyId': DeploymentStatics.CACHE_POLICY_CACHING_OPTIMIZED,
        }

    @staticmethod
    def get_empty_cache_behaviors():
        """No path-specific cache behaviors — all traffic served by the default behavior."""
        return {'Quantity': 0, 'Items': []}
