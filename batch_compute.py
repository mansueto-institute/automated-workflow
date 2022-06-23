from io import BytesIO
import pandas as pd
import boto3

client = boto3.client('s3')

file = client.get_object(
    Bucket='mansueto-workflow-testing',
    Key='df.parquet')

df = pd.read_parquet(BytesIO(file['Body'].read()))

df['new_column'] = df.WARD * df.WARD

buffer = BytesIO()
df.to_parquet(buffer, index=False, compression='gzip')

client.put_object(
    Bucket='mansueto-workflow-testing',
    Key='compute_df.parquet',
    Body=buffer.getvalue()
        )
