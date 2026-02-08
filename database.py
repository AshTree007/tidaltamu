import sqlite3
import json
import uuid
from typing import List
from process_transcript import process_transcript
from tags import generate_tags
import os

# ----- DATABASE SETUP -----
DB_NAME = "file_metadata.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT,
            s3_uri TEXT,
            transcript TEXT,
            keywords TEXT
        )
    """)
    conn.commit()
    conn.close()

def wipe_db():
	if os.path.exists(DB_NAME):
		os.remove(DB_NAME)
		print(f"{DB_NAME} deleted.")
	else:
		print(f"{DB_NAME} does not exist.")


# ----- ADD A FILE -----
def add_file(filename: str, s3_uri: str, transcript: str, keywords: List[str]):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    file_id = str(uuid.uuid4())
    c.execute(
        "INSERT INTO files (id, filename, s3_uri, transcript, keywords) VALUES (?, ?, ?, ?, ?)",
        (file_id, filename, s3_uri, transcript, json.dumps(keywords))
    )
    conn.commit()
    conn.close()
    print(f"Added file {filename} with id {file_id}")


# ----- SEARCH FILES BY KEYWORDS -----
def search_files(query_keywords: List[str]):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, filename, s3_uri, keywords FROM files")
    results = []

    for row in c.fetchall():
        file_id, filename, s3_uri, keywords_json = row
        file_keywords = json.loads(keywords_json)
        if any(k.lower() in [fk.lower() for fk in file_keywords] for k in query_keywords):
            results.append({
                "id": file_id,
                "filename": filename,
                "s3_uri": s3_uri,
                "keywords": file_keywords
            })

    conn.close()
    return results


# ----- EXAMPLE USAGE -----
if __name__ == "__main__":
	#init_db()
     
	# fileName = "test_vid.mpeg4"
	# s3_uri = "s3://tidal-tamu-hackathon-bucket/test_vid.mp3"
	# transcript = process_transcript('test_vid_transcript.txt')
	# keywords = generate_tags(transcript)
	# print(keywords)

	# add_file(fileName, s3_uri, transcript, keywords)
    
	# fileName = "test_file.mp3"
	# s3_uri = "s3://tidal-tamu-hackathon-bucket/test_file.mp3"
	# transcript = process_transcript('test_file_transcript.txt')
	# keywords = generate_tags(transcript)
	# print(keywords)
     
	# add_file(fileName, s3_uri, transcript, keywords)
     
	search_query = ['project']
	matches = search_files(search_query)
     
	print('Search results for: ', search_query)
     
	for m in matches:
		print(f"- {m['filename']} ({m['s3_uri']}), keywords: {m['keywords']}")

#     # Example: Add a file
#     example_filename = "cold_war_video.mp4"
#     example_s3_uri = "s3://tidal-hackathon-bucket/cold_war_video.mp4"
#     example_transcript = "In 1962, President John F. Kennedy addressed the nation about the Cuban Missile Crisis..."
#     example_keywords = ["Cold War", "Cuban Missile Crisis", "John F. Kennedy", "Cuba", "United States"]

#     add_file(example_filename, example_s3_uri, example_transcript, example_keywords)

#     # Example: Search for files containing "Cuba"
#     search_query = ["Cuba"]
#     matches = search_files(search_query)
#     print("Search results for", search_query)
#     for m in matches:
#         print(f"- {m['filename']} ({m['s3_uri']}), keywords: {m['keywords']}")
