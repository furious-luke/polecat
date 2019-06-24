from termcolor import colored

from ...utils.feedback import feedback
from .constants import CERTIFICATE, ZONE
from .operations import delete_parameter, set_parameter
from .utils import aws_client


@feedback
def publish(project, deployment, domain, certificate, zone, feedback):
    if not certificate:
        certificate = domain
    if not zone:
        # TODO: What is this thing actually doing?
        # zone = domain[:domain.rindex('.', domain.rindex('.') - 1)]
        zone = domain + '.'
    acm = aws_client('acm', region='us-east-1')
    r53 = aws_client('route53')
    ssm = aws_client('ssm')
    cert_arn = None
    possible_certs = []
    zone_id = None
    with feedback(f'Find certificate matching {colored(certificate, "yellow")}'):
        response = acm.list_certificates()
        for cert in response['CertificateSummaryList']:
            tags = acm.list_tags_for_certificate(
                CertificateArn=cert['CertificateArn']
            )['Tags']
            name_tag = [
                t for t in tags
                if t['Key'] == 'Name' and t['Value'] == certificate
            ]
            if len(name_tag) > 0:
                cert_arn = cert['CertificateArn']
                break
            elif cert['DomainName'] == certificate:
                cert_arn = cert['CertificateArn']
                break
            possible_certs.append(cert['DomainName'])
        if not cert_arn:
            raise Warning('failed')
    with feedback(f'Find hosted zone matching {colored(zone, "blue")}'):
        response = r53.list_hosted_zones()
        for hz in response['HostedZones']:
            if hz['Name'] == zone:
                zone_id = hz['Id']
        if not zone_id:
            raise Warning('failed')
    if not cert_arn:
        print(possible_certs)
        return
    with feedback(f'Publish {colored(project, "blue")}/{colored(deployment, "green")} to {colored(domain, "yellow")}'):
        name = CERTIFICATE.format(project, deployment, domain)
        set_parameter(name, cert_arn, ssm=ssm)
        name = ZONE.format(project, deployment, domain)
        if zone_id:
            set_parameter(name, str(zone_id), ssm=ssm)
        else:
            delete_parameter(name, ssm=ssm)


@feedback
def unpublish(project, deployment, domain, feedback):
    # TODO
    pass
