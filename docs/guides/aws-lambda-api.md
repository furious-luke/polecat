# Deploy "Star Wars" to AWS Lambda

WARNING: Following this guide may cause you to incur charges to your
AWS account. Various AWS infrastructure components will be created,
and when used, you will very likely be charged. Be sure to destroy all
unwanted infrastructure.

## Prerequisites

### AWS Account

Before beginning you'll need to make sure you have an AWS
account. Please visit the [AWS signup
page](https://portal.aws.amazon.com/billing/signup#/start) and follow
the instructions there. You will need to ensure your programmatic
login credentials, of the form `AWS_ACCESS_KEY_ID` AND
`AWS_SECRET_ACCESS_KEY`, are available in your shell environment.

## Method

Begin by creating the "Star Wars" example:

```bash
polecat example starwars
cd starwars
```

Deploying the Star Wars example is very similar to the included "hello
world" guide. Follow these steps to prepare for deployment, for more
details please visit the "hello world" deployment guide:

```bash
polecat aws initialise <bucket>
polecat project create starwars
polecat deployment create starwars production
polecat secret create helloworld production POLECAT_PROJECT starwars.project.StarWarsProject
polecat build starwars
polecat upload starwars
polecat upload-bundle starwars --source bundle.js
```

Before deploying our Star Wars example, we'll need to provision a
database and migrate our schema. To provision a new database for the
project/deployment:

```bash
polecat db create starwars production
```

To migrate the database we need to run an administration command:

```bash
polecat admin --project starwars --deployment production migrate
```

Now the project can be deployed:

```bash
polecat deploy starwars
```

To examine your new GraphQL API, use a schema inspector of your choice
(Altair, for example), and navigate to the public URL reported by the
deployment command, with `/graphql` appended.

## Cleanup

Cleanup all provisioned resources with:

```bash
polecat undeploy starwars
polecat db delete starwars production
polecat deployment delete starwars production
polecat project delete starwars
```
