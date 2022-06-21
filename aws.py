import argparse
import boto3
import sys


def get_client(client_type: str, access_key: str, secret_key: str) -> boto3.client:
    """
    Authneticates session and gets correct client type per argparse arguments.
    Inputs:
        client_type (str): type of boto3 client to init.
        acces_key (str): AWS acces key
        secret_key (str): AWS secret key
    Ouputs:
        client(boto3.client): session with correct service
    """

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    if client_type == 'batch':
        client = session.client(client_type, region_name='us-east-2')
    else:
        client = session.client(client_type)

    return client


def file_actions(client: boto3.client, file_function: str):
    """
    Determines whether uploading/downloading to AWS
    and runs the correct function from the client.
    Inputs:
        client (boto3.client): client to fetch functions from
        file_function (str): 'upload' or 'download', from args.action.
    Outputs:
        response: response from the AWS bucket

    """

    func = getattr(client, file_function + '_file')
    response = func(
        Filename=args.path,
        Bucket=args.bucket,
        Key=args.key
    )

    return response

def create_job_criterion(batch_client: boto3.client, iam_client: boto3.client):
    """
    Creates a compute environment, a job definition,
    a job queue, and starts a batch job on an Spot instance.
    Inputs:
        client (boto3.client): boto3 batch client
    """

    response = batch_client.create_compute_environment(
    computeEnvironmentName='compute_env',
    type='MANAGED',
    state='ENABLED',
    computeResources={
        'type': 'SPOT',
        'allocationStrategy': 'SPOT_CAPACITY_OPTIMIZED',
        'maxvCpus': 256,
        'desiredvCpus': 123,
        'instanceTypes': [
            'optimal',
        ],
        'imageId': 'string',
        'subnets': [
            'string',
        ],
        'bidPercentage': 50,
        'spotIamFleetRole': 'string'
    },
    serviceRole='string'
    )

    response = batch_client.create_job_queue(
    jobQueueName='compute_env_queue',
    state='ENABLED',
    priority=1,
    computeEnvironmentOrder=[
        {
            'order': 100,
            'computeEnvironment': 'compute_env'
        },
    ],
)

    compute_role = iam.get_role(RoleName='computeRole')

    response = client.register_job_definition(
    jobDefinitionName='compute_job_definition',
    type='container',
    containerProperties={
        'image': 'angwar26/testrepo:latest',
        'memory': 256,
        'vcpus': 16,
        'jobRoleArn': compute_role['Role']['Arn'],
        'executionRoleArn': compute_role['Role']['Arn'],
        'environment': [
            {
                'name': 'AWS_DEFAULT_REGION',
                'value': 'ap-northeast-1',
            }
        ]
    },
)



def check_criterion(batch_client: boto3.client, iam_client: boto3.client):
    env_response = batch_client.describe_compute_environments(
        computeEnvironments=[
            'compute_env',
            ]
    )
    job_response = batch_client.describe_job_definition(
    )
    queue_response = batch_client.describe_job_definition(

    )



def run_job(batch_client: boto3.client):

    response = client.submit_job(
        jobDefinition='compute_job_definition',
        jobName='job',
        jobQueue='compute_env_queue'
)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # options for control flow
    parser.add_argument('action', choices=['upload','download', 'spot'],
                        help='Upload/Download to an AWS bucket or \
                        run compute.py in an AWS spot instance.')

    # always required to authenticate
    parser.add_argument('--access', dest = 'access', required=True,
                        help='The AWS users access key.')
    parser.add_argument('--secret', dest = 'secret', required=True,
                        help='The AWS users secret acess key.')

    # extra flags for upload/download
    parser.add_argument('--bucket', dest='bucket', required='upload' or 'download' in sys.argv,
                        help='The name of the AWS bucket.')
    parser.add_argument('--key',  dest = 'key', required='upload' or 'download' in sys.argv,
                        help='Is filename to-be on server for upload. \
                        Is filename to-be on local for download.')
    parser.add_argument('--path', dest='path', required='upload' or 'download' in sys.argv,
                        help='For upload is the path to be uploaded.\
                        For download is the path to be downloaded to.')

    args = parser.parse_args()


    if args.action in ('upload','download'):
        client = get_client('s3', args.access, args.secret)
        response = file_actions(client, args.action)
    else:
        batch_client = get_client('batch', args.access, args.secret)
        iam_client = get_client('iam', args.access, args.secret)

        create_job(batch_client, iam_client)
