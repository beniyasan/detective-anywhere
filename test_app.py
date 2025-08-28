"""
最小限のテスト用FastAPIアプリ
Cloud Run上での動作確認用
"""

from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Test App")

@app.get("/")
def root():
    return {"message": "Hello World", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "test"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)