# Deploy "hello world" to AWS Lambda

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

Begin by creating the "hello world" example:

```bash
polecat example helloworld
cd helloworld
```

Polecat requires an AWS bucket to store server code archives, frontend
bundles, and media. This bucket may be shared between any number of
projects, but it is often easier to use a different bucket for each
project. Begin by initialising Polecat for an AWS bucket (be sure to
use the name of your bucket in place of `<bucket>`):

```bash
polecat aws initialise <bucket>
```

If this is the first time running this command you will be presented
with the administrator credentials for Polecat, please store these for
future reference. It's recommended to use these credentials instead of
your root credentials for Polecat administrative tasks.

Now we can register our "hello world" project:

```bash
polecat project create helloworld
```

Projects may contain any number of "deployments"; a deployment is a
particular instance of the server and backend code you use for a
project. For example, you may have a "staging" and a "production"
deployment, where your staging deployment is running the latest
version of your code, and your production deployment is running the
most recent stable version. Let's create a production deployment for
our project:

```bash
polecat deployment create helloworld production
```

When deploying Polecat projects, the entrypoint for the project must be specified
as a "secret". Secrets are environmental values supplied to deployments to configure
the behvior of Polecat. To specify the project entrypoint:

```bash
polecat secret create helloworld production POLECAT_PROJECT_MODULE helloworld.project.HelloWorldProject
```

Before we can deploy our project and deployment, we need to build and
upload both the server archive and the frontend bundle. Let's start by
building and uploading our server:

```bash
polecat build helloworld
polecat upload helloworld
```

Usually you would need to setup your frontend code to be bundled using
your bundler of choice (Webpack, Parcel, etc), however in this
instance the `bundle.js` file shipped with the "hello world" example
can be used directly. Upload it with:

```bash
polecat upload-bundle helloworld --source bundle.js
```

We're now ready to deploy our project. To redeploy all deployments,
use:

```bash
polecat deploy helloworld
```

If you happened to have multiple deployments, let's say staging and
production, you could deploy just staging with:

```bash
polecat deploy helloworld staging
```

This command will return an internal URL you may use to view your
newly deployed Lambda.

## Cleanup

Cleanup all provisioned resources with:

```bash
polecat undeploy helloworld
polecat deployment delete production
polecat project delete helloworld
```
