# Publish StarWars

## Prerequisites

### AWS Account

Before beginning you'll need to make sure you have an AWS
account. Please visit the [AWS signup
page](https://portal.aws.amazon.com/billing/signup#/start) and follow
the instructions there. You will need to ensure your programmatic
login credentials, of the form `AWS_ACCESS_KEY_ID` AND
`AWS_SECRET_ACCESS_KEY`, are available in your shell environment.

### Route53 Domain

In order to publish a project with Polecat you'll need to have
purchased a domain name. It's easiest to purchase the domain with AWS
Route53, but not necessary. In this guide we will assume the domain
"starwars.com"

### Star Wars AWS Lambda Guide

This guide follows on from deploying the Star Wars example to AWS
Lambda. Please work through that guide first.

## Method

The first step in publishing a Polecat project is to ensure you have a
valid certificate. Polecat can assist in creating one, however you can
carry out this step manually with AWS's certificate manager.

Create a certificate for your domain with the following command:

```bash
polecat certificate create starwars.com sub.starwars.com -n starwars
```

Here we have added an additional subdomain to the certificate,
"sub.starwars.com", and have given a name to the certificate of
"starwars". The name is useful for uniquely identifying one of
multiple certificates for the same domain.

Validating a certificate can take up to 30 minutes. Polecat can
timeout while waiting for validation, to rerun the wait command use:

```bash
polecat certificate wait starwars
```

Here we have used the name of the certificate instead of the domain,
but "starwars.com" would also have worked.

Now that we have a domain and a certificate, we can publish our
project:

```bash
polecat publish production starwars.com --certificate=starwars
polecat deploy
```

Here, `--certificate` can be either the main domain the certificate
was registered for, or the name associated with the certificate. In
this case the name was used. If the certificate option is omitted a
certificate with the same domain as the published domain is used.

Now we can access the Star Wars project at "https://starwars.com".
