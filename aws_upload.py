import argparse
import boto3

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', dest='bucket', help='The name of the AWS bucket.')
    parser.add_argument('--key',  dest = 'key', help='The AWS key.')
    parser.add_argument('--access', dest = 'access', help='The AWS users access key.')
    parser.add_argument('--secret', dest = 'secret', help='The AWS users secret acess key.')
    parser.add_argument('--path', dest='path', help='The filepath to be uploaded.')

    args = parser.parse_args()

    session = boto3.Session(
        aws_access_key_id=args.access,
        aws_secret_access_key=args.secret,
    )

    client = session.client('s3')
    response = client.upload_file(
        Filename=args.path,
        Bucket=args.bucket,
        Key=args.key
    )
