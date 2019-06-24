import time

from polecat.utils import to_list
from polecat.utils.feedback import feedback
from termcolor import colored

from .exceptions import KnownError
from .utils import aws_client


@feedback
def create_certificate(domains, name=None, feedback=None):
    domains = to_list(domains)
    acm = aws_client('acm', region='us-east-1')
    r53 = aws_client('route53')
    main_domain = domains[0]
    alternatives = domains[1:]
    with feedback(f'Creating certificate request for {colored(main_domain, "yellow")}'):
        hosted_zone_id = get_hosted_zone_id(main_domain, r53=r53)
        options = {
            'DomainName': main_domain,
            'ValidationMethod': 'DNS',
        }
        if alternatives:
            options['SubjectAlternativeNames'] = alternatives
        response = acm.request_certificate(**options)
        cert_arn = response['CertificateArn']
        acm.add_tags_to_certificate(
            CertificateArn=cert_arn,
            Tags=[{
                'Key': 'Name',
                'Value': name
            }]
        )
        attempt = 0
        while True:
            response = acm.describe_certificate(CertificateArn=cert_arn)
            options = response['Certificate']['DomainValidationOptions'][0]
            try:
                record = options['ResourceRecord']
                break
            except KeyError:
                attempt += 1
                if attempt == 3:
                    raise
                time.sleep(5)
        r53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'CREATE',
                    'ResourceRecordSet': {
                        'Name': record['Name'],
                        'Type': record['Type'],
                        'TTL': 300,
                        'ResourceRecords': [{
                            'Value': record['Value']
                        }]
                    }
                }]
            }
        )


@feedback
def wait_certificate(domain, feedback=None):
    acm = aws_client('acm', region='us-east-1')
    with feedback(f'Waiting for certificate {colored(domain, "yellow")}'):
        cert_arn = get_certificate_arn(domain)
        waiter = acm.get_waiter('certificate_validated')
        try:
            waiter.wait(CertificateArn=cert_arn)
        except:
            raise Warning('timed out (try again)')


def get_certificate_arn(domain, acm=None):
    acm = aws_client('acm', client=acm, region='us-east-1')
    paginator = acm.get_paginator('list_certificates')
    possible_certs = []
    for info in paginator.paginate():
        for cert in info['CertificateSummaryList']:
            tags = acm.list_tags_for_certificate(
                CertificateArn=cert['CertificateArn']
            )['Tags']
            name_tag = [
                t for t in tags
                if t['Key'] == 'Name' and t['Value'] == domain
            ]
            if len(name_tag) > 0:
                return cert['CertificateArn']
            elif cert['DomainName'] == domain:
                return cert['CertificateArn']
            possible_certs.append(cert['DomainName'])
    error = KnownError('unknown domain')
    error.possible_certificates = possible_certs
    raise error


def get_hosted_zone_id(domain, r53=None):
    r53 = aws_client('r53', client=r53)
    dns_name = get_dns_name_from_domain(domain)
    response = r53.list_hosted_zones_by_name(DNSName=dns_name)
    try:
        return response['HostedZones'][0]['Id']
    except (KeyError, IndexError):
        raise KnownError('unknown domain')


def get_dns_name_from_domain(domain):
    return '.'.join(domain.split('.')[-2:]) + '.'
