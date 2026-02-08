import os
import time
import uuid
import requests
import boto3
import ffmpeg
from dotenv import load_dotenv


# ================== CONFIG ==================
# Load .env from repo root (one level above this file's folder)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

REGION = os.getenv("AWS_REGION")

# S3 Bucket to upload your audio/video
S3_BUCKET = os.getenv("S3_BUCKET")

# Local file to transcribe
INPUT_FILE = "test_file.mp3"  # Replace with your file

# Name for the transcription job (must be unique)
TRANSCRIPTION_JOB_NAME = f"hackathon-job-{int(time.time())}"

# Optional output bucket for transcription JSON (leave None to skip)
OUTPUT_BUCKET = None
# ============================================

# ----- Step 1: Convert MP4 to MP3 if needed -----
filename, ext = os.path.splitext(INPUT_FILE)
if ext.lower() == ".mp4" or ext.lower() == '.mpeg4':
    mp3_file = filename + ".mp3"
    print(f"Converting {INPUT_FILE} to {mp3_file}...")
    
    ffmpeg_path = r"C:\ffmpeg\ffmpeg.exe"  # full path to ffmpeg.exe
    ffmpeg.input(INPUT_FILE).output(
        mp3_file, format='mp3', acodec='mp3', audio_bitrate='192k'
    ).run(overwrite_output=True, cmd=ffmpeg_path)
    AUDIO_FILE = mp3_file
else:
    AUDIO_FILE = INPUT_FILE

# ----- Step 2: Connect to AWS clients -----
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_SESSION_TOKEN:
    raise RuntimeError("Missing AWS credentials in .env (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)")
s3 = boto3.client(
    "s3",
    region_name=REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

transcribe = boto3.client(
    "transcribe",
    region_name=REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

# ----- Step 3: Upload audio to S3 -----
s3_key = os.path.basename(AUDIO_FILE)
print(f"Uploading {AUDIO_FILE} to S3 bucket {S3_BUCKET}...")
s3.upload_file(AUDIO_FILE, S3_BUCKET, s3_key)
s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
print("Upload complete:", s3_uri)

# ----- Step 4: Start transcription job with unique name -----
TRANSCRIPTION_JOB_NAME = f"hackathon-job-{uuid.uuid4().hex}"
print(f"Starting transcription job: {TRANSCRIPTION_JOB_NAME}")

job_args = {
    "TranscriptionJobName": TRANSCRIPTION_JOB_NAME,
    "LanguageCode": "en-US",
    "Media": {"MediaFileUri": s3_uri},
}
if OUTPUT_BUCKET:
    job_args["OutputBucketName"] = OUTPUT_BUCKET

transcribe.start_transcription_job(**job_args)

# ----- Step 5: Wait for job to complete -----
print("Waiting for transcription job to complete...")
while True:
    status = transcribe.get_transcription_job(TranscriptionJobName=TRANSCRIPTION_JOB_NAME)
    job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]
    if job_status in ["COMPLETED", "FAILED"]:
        break
    print("Current status:", job_status)
    time.sleep(5)

if job_status == "FAILED":
    print("Transcription failed:", status)
    exit(1)

# ----- Step 6: Download transcript JSON -----
transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
print("Transcript JSON available at:", transcript_uri)

response = requests.get(transcript_uri)
transcript_json = response.json()

# ----- Step 7: Convert to plain text -----
transcript_text = transcript_json["results"]["transcripts"][0]["transcript"]

text_file = f"{filename}_transcript.txt"
with open(text_file, "w", encoding="utf-8") as f:
    f.write(transcript_text)

print(f"Transcript saved to {text_file}")
print("=== DONE ===")