from deployment_manager import DeploymentManager


def try_me():
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
        'PhoneNumber': '+972.508777733',
        'Email': 'myemail@gmail.com'
    }

    domain_name = "domain.com"
    origins = [
        {
            'Id': 's3',
            'DomainName': 's3',
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
        'Id': 'ebUrl',
        'DomainName': 'ebUrl',
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

    cache_behaviors = {
        'Quantity': 1,
        'Items': [
            {
                'PathPattern': 'path',
                'TargetOriginId': 's3',
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
                'CachePolicyId': 'CachePolicyId'
            }
        ]
    }

    default_cache_behavior = {
    'TargetOriginId': 'TargetOriginId',
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
    'CachePolicyId': 'CachePolicyId',
    'OriginRequestPolicyId': 'OriginRequestPolicyId'
  }

    deployment_manager.deploy_domain(domain_name=domain_name,
                                     contact_info=contact_info,
                                     origins=origins,
                                     default_cache_behavior=default_cache_behavior,
                                     cache_behaviors=cache_behaviors,
                                     purchase_domain=False)


try_me()
