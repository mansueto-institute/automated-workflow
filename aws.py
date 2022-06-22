from io import BytesIO
import json
import boto3
import pandas as pd


class AWSActions:
    """
    Wraps all of our needed AWS functions, state for clients and credentials.
    """

    def __init__(self, access_key: str, secret_key: str, bucket: str = None) -> None:
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.s3_client = self.get_client('s3')
        self.batch_client = self.get_client('batch')
        self.iam_client = self.get_client('s3')

    def get_client(self, client_type: str) -> boto3.client:
        """
        Authneticates session and gets correct client type per argparse arguments.
        Inputs:
            client_type (str): type of boto3 client to init.
        Ouputs:
            client(boto3.client): session with correct service
        """

        session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        if client_type == 'batch':
            client = session.client(client_type, region_name='us-east-2')
        else:
            client = session.client(client_type)

        return client


    def upload_file(self, key: str, df: pd.DataFrame) -> None:
        """
        Uploads a dataframe to S3 from memory.
        Inputs:
            key (str): The name of the file-to-be on S3.
        """

        buffer = BytesIO()
        df.to_parquet(buffer, index=False, compression='gzip')

        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=f'{key}.parquet.gzip',
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
            Key=f'{key}.parquet.gzip')

        df = pd.read_parquet(BytesIO(file['Body'].read()))

        return df


    def create_compute_env(self) -> dict:
        """
        Creates a compute environment for a SPOT batch job.
        Helper for check_criterion().
        Ouputs:
            response (dict): dictionary of response info
        """

        response = self.batch_client.create_compute_environment(
        computeEnvironmentName='compute_env',
        type='MANAGED',
        state='ENABLED',
        computeResources={
            'type': 'SPOT',
            'allocationStrategy': 'SPOT_CAPACITY_OPTIMIZED',
            'maxvCpus': 256,
            'desiredvCpus': 124,
            'instanceRole': 'ecsInstanceRole',
            'instanceTypes': [
                'optimal',
            ],
            'subnets': [
                'string',
            ],
            'bidPercentage': 50,
            'spotIamFleetRole': 'arn:aws:iam::921974715484:role/AmazonEC2SpotFleetRole'
        },
        serviceRole='arn:aws:iam::921974715484:role/service-role/AWSBatchServiceRole',
        )

        return response


    def create_queue(self) -> dict:
        """
        Creates a Job Queue for batch jobs.
        Helper for check_criterion().
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
                    'computeEnvironment': 'compute_env'
                    },
                ],
            )

        return response


    def create_job_def(self) -> dict:
        """
        Creates a Job definition for a batch job.
        Helper for check_criterion().
        Ouputs:
            response (dict): dictionary of response info
        """
        compute_role = self.iam_client.get_role(RoleName='compute_role')

        response = self.batch_client.register_job_definition(
            jobDefinitionName='compute_job_definition',
            type='container',
            containerProperties={
                'image': 'angwar26/testrepo:latest',
                'memory': 256,
                'vcpus': 16,
                'jobRoleArn': compute_role['Role']['Arn'],
                'executionRoleArn': compute_role['Role']['Arn']
                },
            )

        return response


    def create_roles(self) -> dict:
        """
        Creates roles with the necessar permissions for running a SPOT batch job.
        Helper for check_criterion().
        Ouputs:
            response (dict): dictionary of response info
        """

        service_linked_role_policy = {
        "Version":"2012-10-17",
        "Statement": [
            {
            "Sid":"",
            "Effect":"Allow",
            "Principal": {
                "Service": "spotfleet.amazonaws.com"
            },
            "Action":"sts:AssumeRole"
            }
            ]
        }

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
        """
        response = iam_client.create_role(
            RoleName='SpotFleetTaggingRole ',
            AssumeRolePolicyDocument=json.dumps(service_linked_role_policy)
            )

        iam_client.attach_role_policy(
            PolicyArn='arn:aws::iam::aws:policy/service-role/AmazonEC2SpotFleetTaggingRole'
            RoleName=response['Role']['RoleName']
        )

        response = iam_client.create_service_linked_role(
            AWSServiceName='spotfleet.amazonaws.com',
            Description='Role for Spot Fleet Tagging.'
            )
        """

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
            role_response = self.iam_client.get_role('compute_role')
        except:
            role_response = self.create_roles()

        env_response = self.batch_client.describe_compute_environments(
            computeEnvironments=['compute_env'])

        job_response = self.batch_client.describe_job_definition(
            jobDefinitions=['compute_job_definition'])

        queue_response = self.batch_client.describe_job_queues(
            jobQueues=['compute_queue'])

        if not queue_response['jobQueues']:
            queue_response = self.create_queue()

        if not job_response['jobDefinitions']:
            job_response = self.create_job_def()

        if not env_response['computeEnvironments']:
            env_response = self.create_compute_env()

        return all(queue_response,job_response, env_response, role_response)


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
            jobQueue='compute_env_queue'
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
