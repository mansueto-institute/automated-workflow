import argparse
import pandas as pd
import aws

def compute(actor: aws.AWSActions):
    """
    Downloads file. Modifies it. Reuploads it.
    """
    df = actor.download_file('df')

    df['new_column'] = df.WARD * df.WARD

    actor.upload_file(df, 'df')


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
    parser.add_argument('--bucket', dest='bucket', required=True,
                        help='The name of the AWS bucket.')

    args = parser.parse_args()

    actor = aws.AWSActions(args.access, args.secret, args.bucket)

    compute(actor)
