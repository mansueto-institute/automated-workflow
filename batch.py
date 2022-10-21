import argparse
import aws

def batch(actor: aws.AWSActions) -> dict:
    response = actor.spot_job()

    return response


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # always required to authenticate
    parser.add_argument('--access', dest = 'access', type= str, required=True,
                        help='The AWS users access key.')
    parser.add_argument('--secret', dest = 'secret', type= str, required=True,
                        help='The AWS users secret acess key.')
    parser.add_argument('--maxcpu', dest= 'maxcpu', type= int, reqired=True,
                        help='Maximum vCPUs for spot job.')
    parser.add_argument('--desiredcpu', dest= 'desired_cpu', type= int, reqired=True,
                        help='Desired vCPUs for spot job.')
    parser.add_argument('--mincpu', dest= 'mincpu', type= int, reqired=True,
                        help='Minimum vCPUs for spot job.')
    parser.add_argument('--memory', dest= 'memory', type=int, reqired=True,
                        help='Memory for spot job.')
    parser.add_argument('--docker', dest= 'docker', type= int, reqired=True,
                        help="""Where to find the Docker image repo.
                                In the form: USERNAME/REPONAME:VERSION
                                Ex: 'angwar26/testrepo:latest'
                                                        """)

    args = parser.parse_args()

    actor = aws.AWSActions(args.access, args.secret,
                           args.maxcpu, args.desired_cpu,
                           args.mincpu, args.memory, args.docker)

    batch(actor)
