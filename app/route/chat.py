from fastapi import APIRouter, HTTPException
from logger import logger
from services.chat_service import ChatService
from database.database import db_manager

router = APIRouter(prefix="/api/v1/chat", tags=["Chat Routes"])

@router.post("/chat")
async def chat_api(
    user_id: str,
    session_id: str,
    query: str
):
    """Chat Endpoint"""
    try:
        return await ChatService().handle_uery(
            user_id=user_id,
            session_id=session_id,
            user_query=query
        )

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in chat_api: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions/{user_id}")
async def get_user_sessions(
    user_id: str
):
    """
    Get all user sessions
    """
    logger.info(f"Fetching sessions for user_id: {user_id}")
    existing_data = await db_manager.database.chats.find(
        {
            "user_id": user_id
        },
        {
            "_id": 0,
            "session_id": 1
        }
    ).to_list(length=None)

    return existing_data


@router.get("/chat_history/{session_id}/{user_id}")
async def get_session_chat(
    session_id: str,
    user_id: str
):
    """
    Get chat history for a session
    """
    try:
        logger.info(f"Fetching chat history for session_id: {session_id}, user_id: {user_id}")
        existing_data = await db_manager.database.chats.find_one(
            {
                "session_id": session_id,
                "user_id": user_id
            },
            {
                "_id": 0,
                "messages": 1
            }
        )
        if not existing_data or "messages" not in existing_data:
            logger.warning(f"No messages found for session_id: {session_id}, user_id: {user_id}")
            return []
        
        messages = [
            {
                "role": msg["role"],
                "message": msg["message"],
                "timestamp": msg["timestamp"]
            }
            for msg in existing_data["messages"]
        ]
        logger.info(f"Retreieved {len(messages)} messages for session_id: {session_id}, user_id: {user_id}")
        return messages
    except Exception as e:
        logger.error(f"Error in get_session_chat: {e}")
        return []
