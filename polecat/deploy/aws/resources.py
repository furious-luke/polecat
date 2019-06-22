from ...utils import capitalize
from .constants import MEDIA_PREFIX, SERVER_CODE


def create_api_resources(project, deployment, api_name, bucket, environment):
    project_deployment = f'{capitalize(project)}{capitalize(deployment)}'
    code_version = environment['code']['version']
    bundle_version = environment['bundle']['version']
    secrets = environment.get('secrets', {})
    return {
        f'{project_deployment}ServerLambda': {
            'Type': 'AWS::Lambda::Function',
            'Properties': {
                'Code': {
                    'S3Bucket': bucket,
                    'S3Key': SERVER_CODE.format(project, code_version)
                },
                'Description': f'Polecat API resolver for {project}/{deployment}',
                'FunctionName': f'{project_deployment}Server',
                'Handler': f'main.handler',
                'Timeout': 30,
                'Role': {
                    'Fn::GetAtt': [
                        f'{project_deployment}ExecutionRole',
                        'Arn'
                    ]
                },
                'Runtime': 'python3.7',
                'Environment': {
                    'Variables': {
                        'PROJECT': project,
                        'DEPLOYMENT': deployment,
                        'BUCKET': bucket,
                        'MEDIA_PREFIX': MEDIA_PREFIX.format(
                            project,
                            deployment
                        ),
                        'CODE_VERSION': code_version,
                        'BUNDLE_VERSION': bundle_version,
                        **secrets
                    }
                },
                'Tags': [
                    {
                        'Key': 'Builder',
                        'Value': 'Polecat'
                    },
                    {
                        'Key': 'PolecatProject',
                        'Value': project
                    },
                    {
                        'Key': 'PolecatDeployment',
                        'Value': deployment
                    }
                ]
            }
        },
        f'{project_deployment}ExecutionRole': {
            'Type': 'AWS::IAM::Role',
            'Properties': {
                'AssumeRolePolicyDocument': {
                    'Version': '2012-10-17',
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Principal': {
                                'Service': [
                                    'lambda.amazonaws.com'
                                ]
                            },
                            'Action': [
                                'sts:AssumeRole'
                            ]
                        }
                    ]
                },
                'ManagedPolicyArns': [
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
                ],
                'Policies': [
                    {
                        'PolicyName': f'{project_deployment}MediaAccess',
                        'PolicyDocument': {
                            'Version': '2012-10-17',
                            'Statement': [
                                {
                                    'Effect': 'Allow',
                                    'Action': [
                                        's3:DeleteObject',
                                        's3:DeleteObjectVersion',
                                        's3:GetObject',
                                        's3:PutObject'
                                    ],
                                    'Resource': {
                                        'Fn::Join': [
                                            '',
                                            [
                                                # TODO: Use a constant.
                                                f'arn:aws:s3:::{bucket}/' + MEDIA_PREFIX.format(project, deployment) + '*'
                                            ]
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        f'{api_name}Api': {
            'Type': 'AWS::ApiGateway::RestApi',
            'Properties': {
                'Name': api_name,
                'Description': f'Polecat API Gateway',
                'FailOnWarnings': True,
                'EndpointConfiguration': {
                    'Types': [
                        # TODO: This was regional before... problem?
                        'EDGE'
                    ]
                }
            }
        },
        f'{project_deployment}ServerLambdaPermission': {
            'Type': 'AWS::Lambda::Permission',
            'Properties': {
                'Action': 'lambda:invokeFunction',
                'FunctionName': {
                    'Fn::GetAtt': [
                        f'{project_deployment}ServerLambda',
                        'Arn'
                    ]
                },
                'Principal': 'apigateway.amazonaws.com',
                'SourceArn': {
                    'Fn::Join': [
                        '',
                        [
                            'arn:aws:execute-api:',
                            {
                                'Ref': 'AWS::Region'
                            },
                            ':',
                            {
                                'Ref': 'AWS::AccountId'
                            },
                            ':',
                            {
                                'Ref': f'{api_name}Api'
                            },
                            '/*'
                        ]
                    ]
                }
            }
        },
        f'{capitalize(project)}ApiGatewayCloudWatchLogsRole': {
            'Type': 'AWS::IAM::Role',
            'Properties': {
                'AssumeRolePolicyDocument': {
                    'Version': '2012-10-17',
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Principal': {
                                'Service': [
                                    'apigateway.amazonaws.com'
                                ]
                            },
                            'Action': [
                                'sts:AssumeRole'
                            ]
                        }
                    ]
                },
                'Policies': [
                    {
                        'PolicyName': 'ApiGatewayLogsPolicy',
                        'PolicyDocument': {
                            'Version': '2012-10-17',
                            'Statement': [
                                {
                                    'Effect': 'Allow',
                                    'Action': [
                                        'logs:CreateLogGroup',
                                        'logs:CreateLogStream',
                                        'logs:DescribeLogGroups',
                                        'logs:DescribeLogStreams',
                                        'logs:PutLogEvents',
                                        'logs:GetLogEvents',
                                        'logs:FilterLogEvents'
                                    ],
                                    'Resource': '*'
                                }
                            ]
                        }
                    }
                ]
            }
        },
        f'{project_deployment}ApiGatewayAccount': {
            'Type': 'AWS::ApiGateway::Account',
            'Properties': {
                'CloudWatchRoleArn': {
                    'Fn::GetAtt': [
                        f'{capitalize(project)}ApiGatewayCloudWatchLogsRole',
                        'Arn'
                    ]
                }
            }
        },
        f'{project_deployment}ApiStage': {
            'DependsOn': [
                f'{project_deployment}ApiGatewayAccount'
            ],
            'Type': 'AWS::ApiGateway::Stage',
            'Properties': {
                'DeploymentId': {
                    'Ref': f'{project_deployment}ApiDeployment'
                },
                'MethodSettings': [
                    {
                        'DataTraceEnabled': True,
                        'HttpMethod': '*',
                        'LoggingLevel': 'INFO',
                        'ResourcePath': '/*'
                    }
                ],
                'RestApiId': {
                    'Ref': f'{api_name}Api'
                },
                'StageName': f'{project}-{deployment}',
                'Tags': [
                    {
                        'Key': 'Builder',
                        'Value': 'Polecat'
                    },
                    {
                        'Key': 'PolecatProject',
                        'Value': project
                    },
                    {
                        'Key': 'PolecatDeployment',
                        'Value': deployment
                    }
                ]
            }
        },
        f'{project_deployment}ApiDeployment': {
            'Type': 'AWS::ApiGateway::Deployment',
            'DependsOn': [
                f'{project_deployment}Request'
            ],
            'Properties': {
                'RestApiId': {
                    'Ref': f'{api_name}Api'
                }
            }
        },
        f'{project_deployment}Resource': {
            'Type': 'AWS::ApiGateway::Resource',
            'Properties': {
                'RestApiId': {
                    'Ref': f'{api_name}Api'
                },
                'ParentId': {
                    'Fn::GetAtt': [
                        f'{api_name}Api', 'RootResourceId'
                    ]
                },
                'PathPart': '{proxy+}'
            }
        },
        f'{project_deployment}Request': {
            'DependsOn': f'{project_deployment}ServerLambdaPermission',
            'Type': 'AWS::ApiGateway::Method',
            'Properties': {
                'ApiKeyRequired': False,
                'AuthorizationType': 'NONE',
                'HttpMethod': 'ANY',
                'Integration': {
                    'Type': 'AWS_PROXY',
                    'IntegrationHttpMethod': 'POST',
                    'Uri': {
                        'Fn::Join': [
                            '',
                            [
                                'arn:aws:apigateway:',
                                {
                                    'Ref': 'AWS::Region'
                                },
                                ':lambda:path/2015-03-31/functions/',
                                {
                                    'Fn::GetAtt': [
                                        f'{project_deployment}ServerLambda',
                                        'Arn'
                                    ]
                                },
                                '/invocations'
                            ]
                        ]
                    },
                    'IntegrationResponses': [
                        {
                            'StatusCode': 200
                        }
                    ]
                },
                'ResourceId': {
                    'Ref': f'{project_deployment}Resource'
                },
                'RestApiId': {
                    'Ref': f'{api_name}Api'
                },
                'MethodResponses': [
                    {
                        'StatusCode': 200
                    }
                ]
            }
        },
        f'{project_deployment}RootRequest': {
            'DependsOn': f'{project_deployment}ServerLambdaPermission',
            'Type': 'AWS::ApiGateway::Method',
            'Properties': {
                'ApiKeyRequired': False,
                'AuthorizationType': 'NONE',
                'HttpMethod': 'ANY',
                'Integration': {
                    'Type': 'AWS_PROXY',
                    'IntegrationHttpMethod': 'POST',
                    'Uri': {
                        'Fn::Join': [
                            '',
                            [
                                'arn:aws:apigateway:',
                                {
                                    'Ref': 'AWS::Region'
                                },
                                ':lambda:path/2015-03-31/functions/',
                                {
                                    'Fn::GetAtt': [
                                        f'{project_deployment}ServerLambda',
                                        'Arn'
                                    ]
                                },
                                '/invocations'
                            ]
                        ]
                    },
                    'IntegrationResponses': [
                        {
                            'StatusCode': 200
                        }
                    ]
                },
                'ResourceId': {
                    'Fn::GetAtt': [
                        f'{api_name}Api',
                        'RootResourceId'
                    ]
                },
                'RestApiId': {
                    'Ref': f'{api_name}Api'
                },
                'MethodResponses': [
                    {
                        'StatusCode': 200
                    }
                ]
            }
        }
    }


def create_domain_resources(project, deployment, api_name, domain, certificate_arn):
    project_deployment = f'{capitalize(project)}{capitalize(deployment)}'
    return {
        f'{project_deployment}DomainName': {
            'DependsOn': f'{project_deployment}ApiDeployment',
            'Type': 'AWS::ApiGateway::DomainName',
            'Properties': {
                'DomainName': domain,
                'EndpointConfiguration': {
                    'Types': [
                        'EDGE'
                    ]
                },
                'CertificateArn': certificate_arn
            }
        },
        f'{project_deployment}BasePath': {
            'DependsOn': f'{project_deployment}DomainName',
            'Type': 'AWS::ApiGateway::BasePathMapping',
            'Properties': {
                'DomainName': domain,
                'RestApiId': {
                    'Ref': f'{api_name}Api'
                },
                'Stage': f'{project}-{deployment}'
            }
        }
    }


def create_zone_resources(project, deployment, domain, zone):
    project_deployment = f'{capitalize(project)}{capitalize(deployment)}'
    return {
        f'{project_deployment}RecordSet': {
            'DependsOn': f'{project_deployment}DomainName',
            'Type': 'AWS::Route53::RecordSet',
            'Properties': {
                'Name': domain,
                'Type': 'A',
                'HostedZoneId': zone,
                'AliasTarget': {
                    'DNSName': {
                        'Fn::GetAtt': [
                            f'{project_deployment}DomainName',
                            'DistributionDomainName'
                        ]
                    },
                    'HostedZoneId': {
                        'Fn::GetAtt': [
                            f'{project_deployment}DomainName',
                            'DistributionHostedZoneId'
                        ]
                    },
                    'EvaluateTargetHealth': False
                }
            }
        }
    }


def create_output_resources(project, deployment, api_name):
    project_deployment = f'{capitalize(project)}{capitalize(deployment)}'
    return {
        f'{project_deployment}Url': {
            'Description': f'Polecat root URL of {project}/{deployment} API gateway',
            'Value': {
                'Fn::Join': [
                    '',
                    [
                        'https://',
                        {
                            'Ref': f'{api_name}Api'
                        },
                        '.execute-api.',
                        {
                            'Ref': 'AWS::Region'
                        },
                        f'.amazonaws.com/{project}-{deployment}/'
                    ]
                ]
            }
        }
    }
