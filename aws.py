import argparse
import boto3
import sys


def get_client(client_type: str, access_key: str, secret_key: str) -> boto3.client:
    """
    Authneticates session and gets correct per client type argparse arguments..
    Inputs:
        client_type (str): type of boto3 client to init.
        acces_key (str): AWS acces key
        secret_key (str): AWS secret key
    Ouputs:
        client(boto3.session.client): session with correct service
    """

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    client = session.client(client_type)

    return client


def file_actions(client: boto3.session.client, file_function: str):
    """
    Determines whether uploading/downloading to AWS
    and runs the correct function from the client.
    Inputs:
        client (boto3.session.client): client to fetch functions from
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
        client = get_client('batch', args.access, args.secret)
        pass
