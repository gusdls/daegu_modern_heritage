from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import cv2
import numpy as np
import sqlite3
from datetime import datetime
from deepface import DeepFace

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db():
    conn = sqlite3.connect("score.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            score INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def evaluate_expression_score(img):
    try:
        result = DeepFace.analyze(img, actions=["emotion"])[0]
        emotion = result["dominant_emotion"]

        print(emotion)

        emotion_scores = {
            "happy": 10,
            "surprise": 8,
            "neutral": 5,
            "sad": 3,
            "angry": 2,
            "fear": 1,
            "disgust": 1,
        }

        return emotion_scores.get(emotion, 5)
    except Exception as e:
        print(e)


@app.post("/upload/")
async def upload_image(location: str = Form(...), file: UploadFile = File(...)):
    file_bytes = await file.read()
    np_img = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    score = evaluate_expression_score(img)
    if score is None:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("score.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO scores (location, score, timestamp)
        VALUES (?, ?, ?)
    """,
        (location, score, timestamp),
    )
    conn.commit()
    conn.close()

    return {"location": location, "score": score, "timestamp": timestamp}

@app.get("/scores/")
def get_all_ratings():
    conn = sqlite3.connect("score.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM scores")
    records = cursor.fetchall()
    conn.close()

    return {"scores": records}


if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
