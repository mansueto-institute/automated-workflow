from io import BytesIO
import pandas as pd
import boto3

client = boto3.client('s3')

file = client.get_object(
    Bucket='mansueto-workflow-testing',
    Key='df.csv')

df = pd.read_csv(BytesIO(file['Body'].read()))

df['new_column'] = df.WARD * df.WARD

buffer = BytesIO()
df.to_parquet(buffer, index=False, compression='gzip')

client.put_object(
    Bucket='mansueto-workflow-testing',
    Key=f'compute_df.parquet.gzip',
    Body=buffer.getvalue()
        )