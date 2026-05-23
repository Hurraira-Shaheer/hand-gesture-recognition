from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "Hand Gesture Recognition API is running"}