import os
from pydantic_settings import BaseSettings
from typing import List
from logger import logger

class Settings(BaseSettings):
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    MONGODB_NAME: str = "financial_chatbot_main"
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GOOGLE_GEMINI_MODEL: str = "gemini-2.0-flash-lite"
    SQL_CONNECTION_URL: str = os.getenv("SQL_CONNECTION_URL")
    SQL_DB_NAME: str = "financial_chatbot"

    SUPPORTED_EXTENSIONS: List[str] = ['csv', 'xlsx', 'xls', 'pdf', 'docx']
    EXCEL_FILE_EXTENSIONS: List[str] = ['csv', 'xlsx', 'xls']
    DOCUMENT_FILE_EXTENSIONS: List[str] = ['pdf', 'docx']

    SUPPORTED_LANGUAGES: List[str] = [
        "English", 
        "Spanish", 
        "French", 
        "German", 
        "Italian", 
        "Portuguese", 
        "Dutch", 
        "Russian",
        "Chinese",
        "Japanese",
        "Korean",
        "Arabic",
        "Hindi",
        "Gujarati",
        "Marathi"
    ]

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            logger.info("Settings initialized successfully")
        except Exception as e:
            logger.error(f"Settings initialization failed: {e}")
            raise

settings = Settings()
