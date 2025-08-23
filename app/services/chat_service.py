from typing import Dict, Any
from datetime import datetime
from core.graph import FinancialChatBot
from logger import logger, log_exception
from database.database import db_manager

class ChatService:
    def __init__(self):
        self.chatbot = FinancialChatBot()

    async def handle_uery(
            self,
            user_id: str,
            session_id: str,
            user_query: str
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Chat Service triggered for user: {user_id}, session: {session_id}")

            # Step1: Save user message first
            await self._save_message(user_id, session_id, "user", user_query)

            # Step2: Generate assistant response
            response = await self.chatbot.process_query(
                user_id=user_id,
                session_id=session_id,
                user_query=user_query
            )

            # Step3: Save assistant response
            await self._save_message(user_id, session_id, "assistant", response)

            return {
                "success": True,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in handle_query: {str(e)}")
            return {
                "success": False,
                "response": f"Error occurred while processing query: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _save_message(
            self,
            user_id: str,
            session_id: str,
            role: str,
            message: str
    ):
        """
        Save individual messages (user or assistant) in MongoDB.
        Role can be 'user' or 'assistant'.
        """
        try:
            chat_query = {
                "user_id": user_id,
                "session_id": session_id
            }

            message_entry = {
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }

            await db_manager.database.chats.update_one(
                chat_query,
                {
                    "$setOnInsert": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "created_at": datetime.now().isoformat()
                    },
                    "$push": {
                        "messages": message_entry
                    },
                    "$set": {
                        "updated_at": datetime.now().isoformat()
                    }
                },
                upsert=True
            )

            logger.info(f"{role.capitalize()} message saved for user: {user_id}, session: {session_id}")
            return True
        except Exception as e:
            return log_exception(e, logger)
