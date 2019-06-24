# Certificates on AWS

## Prerequisites

### AWS Account

Before beginning you'll need to make sure you have an AWS
account. Please visit the [AWS signup
page](https://portal.aws.amazon.com/billing/signup#/start) and follow
the instructions there. You will need to ensure your programmatic
login credentials, of the form `AWS_ACCESS_KEY_ID` AND
`AWS_SECRET_ACCESS_KEY`, are available in your shell environment.

## Method

```bash
polecat certificate create test.com sub.test.com -n test
```

```bash
polecat certificate wait test.com
```

```bash
polecat publish production test.com --certificate=test
```

Here, `--certificate` can be either the main domain the certificate
was registered for, or the name associated with the certificate. In
this case the name was used.
