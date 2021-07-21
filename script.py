import time

import boto3
import dns.resolver


class DomainConfigurator:
  def __init__(self):
    self._acm_client = boto3.client('acm')
    self._cf_client = boto3.client('cloudformation')
    self._r53_client = client = boto3.client('route53')

    self._template_url = 'some s3 bucket object'
    self._acm_resource_name = 'TLSCert'
    self._zone_resource_name = 'DNSZone'

    self._valid_nameservers = [
      'ns1.example.com',
      'ns2.example.com',
      'ns3.example.com'
    ]

  def _check_correct_nameserver_config(self, domain):
    result = dns.resolver.query(domain, 'NS')
    return (result == _valid_nameservers)

  def _get_acm_arn(self, domain):
    try:
      response = self._cf_client.describe_stack_resources(
        StackName=self._stack_name(domain)
        LogicalResourceId=self._acm_resource_name
      )
    except:
      return ''

    return response['StackResourceDetail']['PhysicalResourceId']  # Hopefully an ARN

  def _get_domains_awaiting_config(self):
    waiting_domains_list = []
    # Do some kind of database lookup to populate the list
    return waiting_domains_list

  def _get_zone_id(self, domain):
    response = self._cf_client.describe_stack_resources(
      StackName=self._stack_name(domain)
      LogicalResourceId=self._zone_resource_name
    )

    return response['StackResourceDetail']['PhysicalResourceId']

  def _set_up_dns_validation(self, acm_arn):
    response = self._acm_client.describe_certificate(
      CertificateArn=acm_arn
    )

    dns_record_required = response['Certificate']['DomainValidationOptions'][0]['ResourceRecord']
    self._r53_client.change_resource_record_sets(
      HostedZoneId=self._get_zone_id(domain),
      ChangeBatch=dns_record_required  # This might actually be in the right format!
    )

  def _is_stack_building(self, domain_list):
    """Making no attempt to handle failed stacks, which it probably should."""
    domain_stacks = []
    for domain in domain_list:
      domain_stacks[] = self._stack_name(domain)

    # This should absolutely have pagination
    response = self._cf_client.list_stacks(
      StackStatusFilter=['CREATE_IN_PROGRESS']
    )

    found_building_stack = False

    for building_stack in response['StackSummaries']:
      if building_stack['StackName'] in domain_stacks:
        found_building_stack = True
        break

    return found_building_stack

  def _stack_name(self, domain):
    return 'HostingFor' + domain  # I doubt a dot is valid here, but you get the idea

  def _start_template_creation(self, domain):
    self._cf_client.create_stack(
      StackName=self._stack_name(domain)
      TemplateURL=self._template_url
      Parameters=[
        {ParameterKey: 'DomainName', ParameterValue: domain}
      ]
    )

  def main():
    domains_to_process = self._get_domains_awaiting_config()
    for domain in domains_to_process:
      if self._check_correct_nameserver_config(domain):
        self._start_template_creation(domain)
        acm_arn = ''
        while acm_arn == '':
          acm_arn = self._get_acm_arn(domain)
          if acm_arn == '':
            time.sleep(2)
        self._set_up_dns_validation(acm_arn)

    while True:
      if self._is_stack_building(domains_to_process):
          time.sleep(10)
      else:
        break

    # Job done, you might want to update the database now


if __name__ == "__main__":
    runner = DomainConfigurator()
    runner.main()
