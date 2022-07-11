# automated-workflow

This project is meant to create generalized data engineering work flow templates so that they can be applied to specific projects at Mansueto.

## Github Actions

In order to explain Github Actions Workflow control I'll explain some code from our project.

```
name: test
on: [push]
jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Create ingestion environment
        uses: conda-incubator/setup-miniconda@v2.1.1
        with:
          miniconda-version: 'latest'
          channels: conda-forge
          environment-file: environment_ingest.yml
      - name: Ingest Data
        shell: bash -l {0}
        run: python ingest.py --bucket ${{ secrets.AWS_BUCKET }} --access ${{ secrets.AWS_ACCESS }} --secret ${{ secrets.AWS_SECRET }}
```

This code establishes that the workflow is called `test`, and declares a job `ingest` that runs on one of Gthub's free Ubuntu machines. `actions/checkout@v2` tells GitHub Actions to download the repo onto the machine when it starts the job. `conda-incubator/setup-miniconda@v2.1.1` tells Github Actions that we want to use the conda plugin for GitHub Actions and the following code specifies what kind of environment it should be.

```
shell: bash -l {0}
run: python ingest.py --bucket ${{ secrets.AWS_BUCKET }} --access ${{ secrets.AWS_ACCESS }} --secret ${{ secrets.AWS_SECRET }}
```

`bash -l {0}` is necessary to log-in to the shell where our conda environment will be located. `{0}` is a placeholder that Github Actions will fill in at run time. The following line runs our `ingest.py` script - remember that we checked out our project repo with the job earlier so we can use files from it in our workflow. This line also refernces our repo secrets that we uploaded with the [Github Actions Secrets API](https://docs.github.com/en/rest/actions/secrets). 

Some other notes about AWS.

`on: [push]` tells Github Actions to run our workflow whenever the repo is pushed to. To see more options for workflow triggers see: https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows


``` 
aws_compute:
    needs: [ingest, build_docker]
```
This declares that the `aws_compute` job requires the `ingest` and `build_docker` jobs to finish before it will run. The default is for all jobs to run in tandem. In order to have jobs run in a particualr order, a `needs` statement needs to be specified for that job.


## AWS

This project uploads from AWS buckets, downloads from AWS buckets, controls IAMs, creates the necessary environments for Batch jobs, and then submits them.

Prerequisites:

 - AWS permissions to access S3, Batch, IAMs.
 - Docker Image for batch job

The most important part of our script is the part that creates a Compute Environment, a Job Definition, a Role, and a Queue for the Batch job.

The job is run through a Docker environment that is fetched from DockerHub. The container executes its entry point when the Batch job starts.