from io import BytesIO
import json
import re
import boto3
import botocore
import pandas as pd


class AWSActions:
    """
    Wraps all of our needed AWS functions, state for clients and credentials.
    """

    def __init__(self, access_key: str, secret_key: str, bucket: str = None,
                 region: str = 'us-east-2', maxvcpus: int = 4, desiredvcpus: int = 2,
                 minvcpus: int = 2, memory: int = 8192, docker: str = None) -> None:
        """
        Required inputs:
            access_key (str): AWS Access key for user
            secret_key (str): AWS Secret key for user
        Optional Inputs:
            bucket (str): name of bucket to be used, and created if it does not already exist
            region (str): region where services are to be used. Default is 'us-east-2'
            maxvcpus (int): number of vcpus to use in batch job
            desiredvcpus (int): number of desired vcpus to use in batch job
            minvcpus (int): min number of vcpus for batch job
            memory (int): hard limit of memory to supply to the container in MiB.
                          Used in resourceRequirements in create_job_def()
            docker (str): the name of the docker image to be used in the container.
                          Ex: angwar26/testrepo:latest where angwar26 is a username,
                          testrepo is a repository name on DockerHub, and latest is a version.
        """
        self.bucket = bucket
        self.region = region
        self.s3_client = self.get_client(access_key, secret_key, 's3')
        self.batch_client = self.get_client(access_key, secret_key, 'batch')
        self.iam_client = self.get_client(access_key, secret_key, 'iam')
        self.maxvcpus = maxvcpus
        self.desiredvcpus = desiredvcpus
        self.minvcpus = minvcpus
        self.memory = memory
        self.docker = docker

    def get_client(self, access_key: str, secret_key:str, client_type: str) -> boto3.client:
        """
        Authneticates session and gets correct client type per argparse arguments.
        Inputs:
            access_key (str): AWS Access key for a user
            secret_key (str): AWS Access key for a user
            client_type (str): type of boto3 client to init.
        Ouputs:
            client(boto3.client): session with correct service
        """

        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        client = session.client(client_type, region_name=self.region)

        return client


    def handle_bucket(self):
        """
        Creates a bucket if it doesn't exist with what's probably some sane defaults.
        Uses self.bucket for bucket name.
        To read AWS Documentation:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.create_bucket
        Inputs:
            region (str): the region for the bucket to be created in.
        """

        try:
            self.s3_client.head_bucket(
                Bucket=self.bucket,
                )
        # we can refine how we catch this exception later
        # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html
        except botocore.exceptions.ClientError:
            self.s3_client.create_bucket(
            ACL='private',
            Bucket=self.bucket,
            CreateBucketConfiguration={
                'LocationConstraint': self.region
                },
            ObjectOwnership='BucketOwnerEnforced'
            )


    def upload_file(self, key: str, df: pd.DataFrame) -> None:
        """
        Uploads a dataframe to S3 from memory.
        Inputs:
            key (str): The name of the file-to-be on S3.
        """

        buffer = BytesIO()
        df.to_parquet(buffer, index=False)

        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=f'{key}.parquet',
            Body=buffer.getvalue()
            )


    def download_file(self, key: str) -> pd.DataFrame:
        """
        Downloads a file from S3 and returns it as a pandas dataframe.
        Inputs:
            key (str): name of file to be downloaded
        """
        file = self.s3_client.get_object(
            Bucket=self.bucket,
            Key=f'{key}.parquet')

        df = pd.read_parquet(BytesIO(file['Body'].read()))

        return df


    def create_compute_env(self) -> dict:
        """
        Creates a compute environment for a SPOT batch job.
        Helper for check_criterion().
        To read AWS Documentation regarding this function see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html?highlight=batch#Batch.Client.create_compute_environment
        Ouputs:
            response (dict): dictionary of response info
        """

        response = self.batch_client.create_compute_environment(
        computeEnvironmentName='compute_test',
        type='MANAGED',
        state='ENABLED',
        computeResources={
            'type': 'SPOT',
            'allocationStrategy': 'SPOT_CAPACITY_OPTIMIZED',
            'maxvCpus': self.maxvcpus,
            'minvCpus': self.minvcpus,
            'desiredvCpus': self.desiredvcpus,
            'instanceRole': 'arn:aws:iam::921974715484:instance-profile/ecsInstanceRole',
            'instanceTypes': [
                'optimal',
            ],
            'securityGroupIds': [
                'sg-3b786b54'
            ],
            'subnets': [
                'subnet-6b457803',
                'subnet-fa650e80',
                'subnet-9c7daed0'
            ],
            'bidPercentage': 60,
            #'spotIamFleetRole': 'arn:aws:iam::921974715484:role/AmazonEC2SpotFleetRole'
        },
        serviceRole='arn:aws:iam::921974715484:role/service-role/AWSBatchServiceRole',
        )

        return response


    def create_queue(self) -> dict:
        """
        Creates a Job Queue for batch jobs.
        Helper for check_criterion().
        To read AWS documentation regarding this function see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html?highlight=batch#Batch.Client.create_job_queue
        Ouputs:
            response (dict): dictionary of response info
        """

        response = self.batch_client.create_job_queue(
            jobQueueName='compute_queue',
            state='ENABLED',
            priority=1,
            computeEnvironmentOrder=[
                {
                    'order': 100,
                    'computeEnvironment': 'compute_test'
                    },
                ],
            )

        return response


    def create_job_def(self) -> dict:
        """
        Creates a Job definition for a batch job.
        Helper for check_criterion().
        To read AWS documentation regarding this function see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html?highlight=batch#Batch.Client.register_job_definition
        Ouputs:
            response (dict): dictionary of response info
        """
        compute_role = self.iam_client.get_role(RoleName='compute_role')

        response = self.batch_client.register_job_definition(
            jobDefinitionName='compute_job_definition',
            type='container',
            containerProperties={
                'image': self.docker,
                'jobRoleArn': compute_role['Role']['Arn'],
                'executionRoleArn': compute_role['Role']['Arn'],
                'resourceRequirements': [
                    {
                        'type': 'MEMORY',
                        'value': str(self.memory),
                        },
                    {
                        'type': 'VCPU',
                        'value': str(self.minvcpus),
                        },
                        ],
                },
            )

        return response


    def create_roles(self) -> dict:
        """
        Creates roles with the necessar permissions for running a SPOT batch job.
        Helper for check_criterion().
        To read AWS documentation on the functions used:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.create_role
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.attach_role_policy
        Ouputs:
            response (dict): dictionary of response info
        """

        assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
                }
            ]
        }

        response = self.iam_client.create_role(
            RoleName='compute_role',
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
            )

        self.iam_client.attach_role_policy(
            RoleName=response['Role']['RoleName'],
            PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
            )
        self.iam_client.attach_role_policy(
            RoleName=response['Role']['RoleName'],
            PolicyArn='arn:aws:iam::aws:policy/CloudWatchFullAccess'
            )

        return response


    def check_criterion(self) -> bool:
        """
        Checks whether job criterion exists, creates criterion if not.
        Helper for spot_job().
        Ouputs:
            True or False (boolean): True if all iterables exist,
                                    False otherwise.
        """

        try:
            role_response = self.iam_client.get_role(RoleName='compute_role')
        except:
            role_response = self.create_roles()

        env_response = self.batch_client.describe_compute_environments(
            computeEnvironments=['compute_test'])

        job_response = self.batch_client.describe_job_definitions(
            jobDefinitions=['compute_job_definition'])

        queue_response = self.batch_client.describe_job_queues(
            jobQueues=['compute_queue'])

        if not job_response['jobDefinitions']:
            job_response = self.create_job_def()

        if not env_response['computeEnvironments']:
            env_response = self.create_compute_env()

        if not queue_response['jobQueues']:
            queue_response = self.create_queue()

        return all([queue_response,job_response, env_response, role_response])


    def submit_job(self) -> dict:
        """
        Submits SPOT batch job with all necessary info.
        Helper for spot_job()
        Inputs:
            batch_client (boto3.client): boto3 batch client
        Ouputs:
            response (dict): dictionary of response info
        """

        response = self.batch_client.submit_job(
            jobDefinition='compute_job_definition',
            jobName='job',
            jobQueue='compute_queue'
        )

        return response


    def spot_job(self) -> dict:
        """
        Brings together all constituent functions for running SPOT batch job.
        Gaurantees job criterion with check_criterion() and submits job with
        submit_job().
        Inputs:
            batch_client (boto3.client): boto3 batch client
            iam_client (boto3.client): boto3 iam client
        Ouputs:
            response (dict): dictionary of response info
        """
        responses = self.check_criterion()

        if responses:
            response = self.submit_job()

        return response
