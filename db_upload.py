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
        contents = open(file_path, "r").read()
        s3_client.put_object(Bucket=AWS_BUCKET, Key=key, Body=contents, ContentType=file_name[-3:])
        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': AWS_BUCKET, 'Key': key}, ExpiresIn=3600)
        return {'key': key, 'name': file_name, 'url': url, 'content_type': file_name[-3:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upload failed: {e}')
    
def startup():
    global s3_client, AWS_BUCKET
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_BUCKET = os.getenv("AWS_BUCKET")
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )