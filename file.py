from dotenv import load_dotenv
import os

print(os.getcwd())

load_dotenv()  # auto-detects .env in cwd

print(os.getenv("BUCKET_NAME"))
