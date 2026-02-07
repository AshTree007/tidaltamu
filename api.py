from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting...")
    yield
    print("Shutdown")

app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/add_doc")
async def add_doc(file: UploadFile = File(...), type: str = Form(...) ):
    if type in ["pdf", "docx", "txt"]:
        print("type: ", type)
        return {"message": f"Document added successfully, type: {type}"}
    
    elif type in ["mp4", "avi", "mkv"]:
        print("type: ", type)
        return {"message": f"Video added successfully, type: {type}"}
    
    elif type in ["mp3", "wav", "aac"]:
        print("type: ", type)
        return {"message": f"Audio added successfully, type: {type}"}

    return {"message": "Unknown file type"}
