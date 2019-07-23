bucket_policy = '''{
    "Version": "2008-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$bucket/projects/*/bundle/*"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "serverlessrepo.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$bucket/projects/*/code/*"
        }
    ]
}
'''

base_policy = '''{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "rds:*",
                "logs:*",
                "route53:ListHostedZonesByName",
                "route53:GetHostedZone",
                "route53:ChangeResourceRecordSets",
                "route53:GetChangeRequest",
                "route53:ListResourceRecordSets",
                "route53:GetChangeRequest",
                "route53:GetChange",
                "cloudformation:DescribeStackEvents",
                "acm:GetCertificate",
                "cloudformation:UpdateStack",
                "acm:ListCertificates",
                "cloudformation:ListStacks",
                "apigateway:*",
                "route53:ListHostedZones",
                "cloudformation:DescribeStackResources",
                "cloudformation:DescribeStacks",
                "cloudformation:CreateStack",
                "cloudformation:GetTemplate",
                "cloudformation:DeleteStack",
                "lambda:*",
                "iam:ListUsers",
                "iam:ListGroups",
                "iam:GetUser",
                "iam:GetRole",
                "iam:PassRole",
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:PutRolePolicy",
                "iam:DetachRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:AttachRolePolicy",
                "cloudformation:ValidateTemplate",
                "cloudfront:UpdateDistribution"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/polecat/projectRegistry"
        }
    ]
}
'''

administrator_policy = '''{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "rds:*",
                "iam:DeleteGroup",
                "iam:ListPolicies",
                "iam:AttachGroupPolicy",
                "iam:AddUserToGroup",
                "iam:CreateAccessKey",
                "iam:PutGroupPolicy",
                "iam:DeleteRolePolicy",
                "iam:ListUsers",
                "iam:ListGroups",
                "iam:GetUser",
                "iam:ListUsers",
                "iam:ListGroups",
                "iam:GetUser",
                "iam:GetRole",
                "iam:PassRole",
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:PutRolePolicy",
                "iam:DetachRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:AttachRolePolicy",
                "iam:CreateUser",
                "iam:GetGroup",
                "iam:CreateGroup",
                "iam:DeleteUser",
                "iam:CreatePolicy",
                "iam:ListGroupsForUser",
                "iam:DetachGroupPolicy",
                "iam:DeletePolicy",
                "logs:*",
                "s3:CreateBucket",
                "s3:ListBucket",
                "s3:DeleteObject",
                "s3:DeleteBucket",
                "s3:PutObject",
                "s3:GetObject",
                "s3:PutBucketPolicy",
                "route53:ListHostedZonesByName",
                "cloudformation:DescribeStackEvents",
                "acm:GetCertificate",
                "acm:ListCertificates",
                "acm:ListTagsForCertificate",
                "acm:RequestCertificate",
                "acm:DescribeCertificate",
                "acm:AddTagsToCertificate",
                "cloudformation:UpdateStack",
                "route53:DeleteHostedZone",
                "cloudformation:ListStacks",
                "route53:CreateHostedZone",
                "apigateway:*",
                "route53:ListHostedZones",
                "cloudformation:DescribeStackResources",
                "cloudformation:DescribeStacks",
                "cloudformation:CreateStack",
                "cloudformation:GetTemplate",
                "cloudformation:DeleteStack",
                "lambda:*",
                "ce:*",
                "cloudformation:ValidateTemplate"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "ssm:PutParameter",
                "ssm:DeleteParameter",
                "ssm:DeleteParameters",
                "ssm:GetParametersByPath",
                "ssm:GetParameters",
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/polecat/*"
        }
    ]
}
'''

project_policy = '''{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "rds:*",
                "logs:*",
                "route53:ListHostedZonesByName",
                "route53:GetHostedZone",
                "route53:ChangeResourceRecordSets",
                "route53:GetChangeRequest",
                "route53:ListResourceRecordSets",
                "route53:GetChangeRequest",
                "route53:GetChange",
                "cloudformation:DescribeStackEvents",
                "acm:GetCertificate",
                "cloudformation:UpdateStack",
                "acm:ListCertificates",
                "cloudformation:ListStacks",
                "apigateway:*",
                "route53:ListHostedZones",
                "cloudformation:DescribeStackResources",
                "cloudformation:DescribeStacks",
                "cloudformation:CreateStack",
                "cloudformation:GetTemplate",
                "cloudformation:DeleteStack",
                "lambda:*",
                "iam:ListUsers",
                "iam:ListGroups",
                "iam:GetUser",
                "iam:GetRole",
                "iam:PassRole",
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:PutRolePolicy",
                "iam:DetachRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:AttachRolePolicy",
                "cloudformation:ValidateTemplate"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "ssm:PutParameter",
                "ssm:DeleteParameter",
                "ssm:DeleteParameters",
                "ssm:GetParametersByPath",
                "ssm:GetParameters",
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/polecat/projects/$project/*"
        },
        {
            "Sid": "VisualEditor2",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/polecat/projectRegistry"
        },
        {
            "Sid": "VisualEditor3",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:DeleteObject",
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::$bucket/projects/$project",
                "arn:aws:s3:::$bucket/projects/$project/*"
            ]
        }
    ]
}
'''
