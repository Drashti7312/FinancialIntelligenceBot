from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from logger import logger
from route import upload, chat
from contextlib import asynccontextmanager
from database.database import db_manager


@asynccontextmanager
async def lifespan(
    app: FastAPI
):
    """Application lifespan manager"""
    try:
        await db_manager.connect_to_mongo()
    except Exception as e:
        logger.error(f"Error occurred while connecting to MongoDB: {e}")
        raise
    else:
        yield
    finally:
        await db_manager.close_mongo_connection()



app = FastAPI(
    title="Financial Intelligence ChatBot",
    description="AI-powered financial document analysis and chat system",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "https://localhost:9000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers=["*"]
)

app.include_router(upload.router)
# app.include_router(chat.router)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root page"""
    try:
        response = """
        <html>
            <head>
                <title>Financial Intelligence Chatbot</title>
            </head>
            <body style="font-family: Arial, sans-serif; margin: 40px;">
                <h1>💬 Financial Intelligence Chatbot</h1>
                <p>Welcome! This API provides AI-powered financial document analysis and chat features.</p>
                <h3>Available Endpoints</h3>
                <ul>
                    <li><a href="/docs">Swagger UI Documentation</a></li>
                </ul>
            </body>
        </html>
        """
        return response
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__=="__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8888,
        reload=True
    )
