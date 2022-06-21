from io import BytesIO
import pandas as pd
import boto3
from aws import file_actions

client = boto3.client('s3')

file = client.get_object(
    Bucket='mansueto-workflow-testing',
    Key='df.csv')

df = pd.read_csv(BytesIO(file['Body'].read()))

df['new_column'] = df.WARD * df.WARD

df.to_csv('df.csv')

client.upload_file(
    Bucket='mansueto-workflow-testing',
    Key='compute_df.csv',
    Filepath='df.csv'
)

print('Data modified.')