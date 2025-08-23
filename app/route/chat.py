from fastapi import APIRouter, HTTPException
from logger import logger
from services.chat_service import ChatService

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
