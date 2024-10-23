
class DeploymentStatics:

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
    def get_cache_behaviors(static_files_bucket: str, path_pattern: str = '/assets/img/*'):
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
                'CachePolicyId': '658327ea-f89d-4fab-a63d-7e88639e58f6' # TODO predefine cache policy ids
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
        'CachePolicyId': '4135ea2d-6df8-44a3-9df3-4b5a84be39ad', # TODO predefine cache policy ids
        'OriginRequestPolicyId': '216adef6-5c7f-47e4-b989-5492eafa07d3' # TODO predefine cache policy ids
    }
