import argparse
import aws

def batch(actor: aws.AWSActions) -> None:
    response = actor.spot_job()


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

    args = parser.parse_args()

    actor = aws.AWSActions(args.access, args.secret, args.bucket)

    batch(actor)
