import boto3
import os
import time
import uuid
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

def make_key(filename: str) -> str:
    return f"{int(time.time())}_{uuid.uuid4().hex}_{filename}"


def upload_file(file_path: str) -> str:
    startup()
    file_name = file_path.split('/')[-1]
    key = make_key(file_name)
    try:
        contents = open(file_path, "rb").read()
        s3_client.put_object(Bucket=AWS_BUCKET, Key=key, Body=contents, ContentType=file_name[-3:])
        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': AWS_BUCKET, 'Key': key}, ExpiresIn=3600)
        return {'key': key, 'name': file_name, 'url': url, 'content_type': file_name[-3:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upload failed: {e}')
    
def startup():
    global s3_client, AWS_BUCKET
    
    # FIX 2: Removed AWS_ACCESS_KEY and AWS_SECRET_KEY
    # The EC2 Instance Role handles permissions automatically.
    
    # Ensure you have your bucket name in your .env file or replace it here
    AWS_BUCKET = os.getenv("AWS_BUCKET", "YOUR-ACTUAL-BUCKET-NAME-HERE") 
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1") 
    
    # Initialize S3 client (Auto-detects credentials from EC2 Role)
    if s3_client is None:
        s3_client = boto3.client('s3', region_name=AWS_REGION)