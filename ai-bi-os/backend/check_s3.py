import os
from dotenv import load_dotenv
load_dotenv('.env')

import boto3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    endpoint_url=os.getenv('AWS_ENDPOINT_URL'),
    region_name=os.getenv('AWS_REGION')
)
bucket = os.getenv('AWS_BUCKET_NAME')
try:
    response = s3_client.list_objects_v2(Bucket=bucket)
    if 'Contents' in response:
        print(f'Found {len(response.get("Contents", []))} files in bucket {bucket}:')
        for obj in response['Contents']:
            print(f" - {obj['Key']} ({obj['Size']} bytes)")
    else:
        print(f'Bucket {bucket} is empty.')
except Exception as e:
    print('Error:', e)
