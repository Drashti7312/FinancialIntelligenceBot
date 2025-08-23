from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from typing import Optional
from config.settings import settings
from logger import logger, log_exception
from sqlalchemy import create_engine, text

class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.fs_bucket = None

    async def connect_to_mongo(self):
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.database = self.client[settings.MONGODB_NAME]
            self.fs_bucket = AsyncIOMotorGridFSBucket(self.database)
            logger.info("Connected to mongodb")
        except Exception as e:
            return log_exception(e, logger)
        
    async def close_mongo_connection(self):
        try:
            if self.client:
                self.client.close()
                logger.info("Mongodb connection closed")
        except Exception as e:
            return log_exception(e, logger)

def get_sql_engine():
    engine = create_engine(settings.SQL_CONNECTION_URL)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.SQL_DB_NAME}"))
    return create_engine(f"{settings.SQL_CONNECTION_URL}/{settings.SQL_DB_NAME}")

db_manager = DatabaseManager()

sql_engine = get_sql_engine()