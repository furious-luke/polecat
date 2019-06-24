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
polecat deployment create production
polecat secret create production POLECAT_PROJECT_MODULE starwars.project.StarWarsProject
polecat build
polecat upload
polecat upload-bundle --source bundle.js
```

Before deploying our Star Wars example, we'll need to provision a
database and migrate our schema. To provision a new database for the
project/deployment:

```bash
polecat db create production
```

Before running the migrations we first need to deploy our functions
(the ability to migrate a database prior to deployment is in the
roadmap):

```bash
polecat deploy
```

To migrate the database we need to run an administration command:

```bash
polecat admin production migrate
```

Navigate to the URL reported by the above "deploy" command. You should
see data loaded from your new API.

To explore the GraphQL API, use a schema inspector of your choice
(Altair, for example), and navigate to the public URL reported by the
deployment command, with `/graphql` appended.

## Cleanup

Cleanup all provisioned resources with:

```bash
polecat undeploy starwars
polecat db delete production
polecat deployment delete production
polecat project delete starwars
```

Note: Please confirm all resources have been terminated via the AWS
console.
