import boto3
import os
import time
import uuid
import mimetypes
import json
import urllib.request
from fastapi import HTTPException
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Attr

load_dotenv()

# Global variables
s3_client = None
rekognition = None
comprehend = None
transcribe = None
dynamodb = None
AWS_BUCKET = None

def make_key(filename: str) -> str:
    return f"{int(time.time())}_{uuid.uuid4().hex}_{filename}"

def startup():
    global s3_client, AWS_BUCKET, rekognition, comprehend, transcribe, dynamodb
    
    AWS_REGION = os.getenv("S3_REGION")
    AWS_BUCKET = os.getenv("BUCKET_NAME")

    if not AWS_BUCKET:
        print("CRITICAL ERROR: AWS_BUCKET not found. Check .env file.")

    if s3_client is None:
        try:
            s3_client = boto3.client('s3', region_name=AWS_REGION)
            rekognition = boto3.client('rekognition', region_name=AWS_REGION)
            comprehend = boto3.client('comprehend', region_name=AWS_REGION)
            transcribe = boto3.client('transcribe', region_name=AWS_REGION)
            dynamo_resource = boto3.resource('dynamodb', region_name=AWS_REGION)
            dynamodb = dynamo_resource.Table('MediaTags')
            print(f"AWS Services Initialized. Bucket: {AWS_BUCKET}")
        except Exception as e:
            print(f"Failed to connect to AWS: {e}")

def get_ai_tags(bucket, key, file_ext):
    """Helper: Asks AWS Rekognition what is in the image"""
    if file_ext not in ['jpg', 'jpeg', 'png']:
        return [] 

    try:
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=5,
            MinConfidence=80
        )
        return [label['Name'] for label in response['Labels']]
    except Exception as e:
        print(f"AI Tagging Error: {e}")
        return []

def get_text_tags(text):
    """Extract tags from text using AWS Comprehend key phrases"""
    global comprehend
    if comprehend is None:
        startup()
    
    try:
        response = comprehend.detect_key_phrases(
            Text=text[:5000],  # Comprehend has 5000 char limit per request
            LanguageCode='en'
        )
        tags = [phrase['Text'] for phrase in response['KeyPhrases']]
        return tags[:10]  # Limit to 10 top tags
    except Exception as e:
        print(f"Text Tagging Error: {e}")
        return []

def process_text_file(bucket, key):
    """Download text file from S3 and extract tags using Comprehend"""
    global s3_client
    if s3_client is None:
        startup()
    
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        text_content = response['Body'].read().decode('utf-8')
        tags = get_text_tags(text_content)
        return tags
    except Exception as e:
        print(f"Text File Processing Error: {e}")
        return []

def process_audio_file(bucket, key):
    """Start AWS Transcribe job, wait for completion, and extract tags"""
    global transcribe, s3_client
    if transcribe is None:
        startup()
    
    try:
        # Start transcription job
        job_name = f"transcribe_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'S3Object': {'Bucket': bucket, 'Key': key}},
            MediaFormat=key.split('.')[-1].lower(),  # mp3, wav, etc.
            LanguageCode='en-US'
        )
        
        # Wait for job to complete
        max_attempts = 60
        attempt = 0
        while attempt < max_attempts:
            response = transcribe.get_transcription_job(
                TranscriptionJobName=job_name
            )
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Download the transcript JSON
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                with urllib.request.urlopen(transcript_uri) as response:
                    transcript_json = json.loads(response.read().decode('utf-8'))
                    transcript_text = transcript_json['results']['transcripts'][0]['transcript']
                
                tags = get_text_tags(transcript_text)
                return tags
            elif status == 'FAILED':
                print(f"Transcription job failed: {response['TranscriptionJob']['FailureReason']}")
                return []
            
            attempt += 1
            time.sleep(1)
        
        print("Transcription job timed out")
        return []
    except Exception as e:
        print(f"Audio File Processing Error: {e}")
        return []

def process_video_file(bucket, key):
    """Start AWS Rekognition Video job, wait for completion, and extract labels"""
    global rekognition
    if rekognition is None:
        startup()
    
    try:
        # Start label detection job for video
        client_request_token = uuid.uuid4().hex[:8]
        response = rekognition.start_label_detection(
            Video={'S3Object': {'Bucket': bucket, 'Name': key}},
            ClientRequestToken=client_request_token,
            MinConfidence=70
        )
        
        job_id = response['JobId']
        
        # Wait for job to complete
        max_attempts = 300  # 5 minutes with 1 second intervals
        attempt = 0
        while attempt < max_attempts:
            response = rekognition.get_label_detection(
                JobId=job_id
            )
            status = response['JobStatus']
            
            if status == 'SUCCEEDED':
                # Extract labels from all frames and get unique ones
                labels_set = set()
                for label_obj in response['Labels']:
                    if 'Label' in label_obj:
                        labels_set.add(label_obj['Label']['Name'])
                
                return list(labels_set)[:10]  # Limit to 10 unique labels
            elif status == 'FAILED':
                print(f"Video label detection failed: {response.get('StatusMessage', 'Unknown error')}")
                return []
            
            attempt += 1
            time.sleep(1)
        
        print("Video label detection job timed out")
        return []
    except Exception as e:
        print(f"Video File Processing Error: {e}")
        return []


def upload_file(file_path: str) -> str:
    global s3_client, AWS_BUCKET, dynamodb
    if s3_client is None: startup()
        
    file_name = file_path.split('/')[-1]
    key = make_key(file_name)
    file_ext = file_name.split('.')[-1].lower()
    
    try:
        # 1. Upload to S3
        with open(file_path, "rb") as f:
            contents = f.read()

        # Use proper MIME type for ContentType
        content_type, _ = mimetypes.guess_type(file_name)
        if not content_type:
            content_type = 'application/octet-stream'

        s3_client.put_object(
            Bucket=AWS_BUCKET, 
            Key=key, 
            Body=contents, 
            ContentType=content_type
        )
        
        url = s3_client.generate_presigned_url(
            'get_object', 
            Params={'Bucket': AWS_BUCKET, 'Key': key}, 
            ExpiresIn=3600
        )
        
        # 2. Get Tags based on file type & Save to DB
        tags = []
        
        if file_ext in ['jpg', 'jpeg', 'png']:
            # Image tagging using Rekognition
            tags = get_ai_tags(AWS_BUCKET, key, file_ext)
        elif file_ext in ['txt', 'md']:
            # Text tagging using Comprehend
            tags = process_text_file(AWS_BUCKET, key)
        elif file_ext in ['mp3', 'wav']:
            # Audio tagging using Transcribe + Comprehend
            tags = process_audio_file(AWS_BUCKET, key)
        elif file_ext in ['mp4', 'mov']:
            # Video tagging using Rekognition Video
            tags = process_video_file(AWS_BUCKET, key)
        
        if dynamodb:
            try:
                dynamodb.put_item(
                    Item={
                        'filename': key,
                        'original_name': file_name,
                        'url': url,
                        'tags': tags,
                        'created_at': str(int(time.time()))
                    }
                )
            except Exception as e:
                print(f"DB Save Error: {e}")

        return {'key': key, 'name': file_name, 'url': url, 'tags': tags}

    except Exception as e:
        print(f"UPLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Upload failed: {e}')

def list_files():
    # Fetch from DynamoDB to get tags, but include 'key' for deletion
    global dynamodb, s3_client, AWS_BUCKET
    if dynamodb is None: startup()
    
    try:
        response = dynamodb.scan()
        items = response.get('Items', [])
        
        final_list = []
        for item in items:
            key = item['filename']
            # Generate fresh URL
            fresh_url = s3_client.generate_presigned_url(
                'get_object', 
                Params={'Bucket': AWS_BUCKET, 'Key': key}, 
                ExpiresIn=3600
            )
            
            final_list.append({
                "name": item.get('original_name', key),
                "key": key,  # <--- CRITICAL FOR DELETE BUTTON
                "url": fresh_url,
                "tags": item.get('tags', []),
                "size": 0 
            })
            
        return final_list
        
    except Exception as e:
        print(f"DB LIST ERROR: {e}")
        return []

def search_files(query: str):
    global dynamodb
    if dynamodb is None: startup()
    try:
        response = dynamodb.scan(
            FilterExpression=Attr('tags').contains(query) | Attr('original_name').contains(query)
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Search Error: {e}")
        return []

def delete_file(key: str):
    # Helper to delete from S3 and DynamoDB
    global s3_client, AWS_BUCKET, dynamodb
    if s3_client is None: startup()
    
    try:
        # Delete from S3
        s3_client.delete_object(Bucket=AWS_BUCKET, Key=key)
        # Delete from DynamoDB
        if dynamodb:
            dynamodb.delete_item(Key={'filename': key})
        return True
    except Exception as e:
        print(f"Delete Error: {e}")
        return False