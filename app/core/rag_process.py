import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from schema.models import ChatBotState
from logger import logger, log_exception
from config.settings import settings

class RAGProcess:
    def __init__(self):
        pass

    async def _rag_process(
            self,
            state: ChatBotState
    ) -> ChatBotState:
        """
        Process RAG queries by retrieving relevant documents and generating context.
        """
        try:
            logger.info(f"Startinf RAG process for user: {state['user_id']}, session: {state['session_id']}")

            # Step1: Check if vector store exists for this user/session
            vector_path = os.path.join(
                "vectorstores",
                f"{state["user_id"]}",
                f"document_{state["user_id"]}_{state["session_id"]}"
            )
            logger.info(f"Vector store path: {vector_path}")
            if not os.path.exists(
                vector_path
            ):
                logger.warning("No document vector store found for user")
                state["rag_result"] = {
                    "success": False,
                    "message" : "No documents found. Please upload files first.",
                    "retrieved_docs": []
                }
                return state

            # Step2: Load vector store
            vector_store = await self._get_vector_store(
                vector_path
            )

            # Step3: Perform similarity search
            retrieved_docs = vector_store.similarity_search_with_score(
                state["user_query"],
                k=3
            )

            if not retrieved_docs:
                logger.warning("No relevant documents found for the query")
                state["rag_result"] = {
                    "success": False,
                    "message": "No releavant information found in upload documents.",
                    "retrieved_docs": []
                }
                return state
            
            # Step4: Extract and format retrieved content
            retrieved_content = []
            for i, (doc, score) in enumerate(retrieved_docs):
                retrieved_content.append({
                    "chunk_id": i + 1,
                    "content": doc.page_content,
                    "relevance_score": float(score)
                })

            # Step5: Store RAG results in state
            state["rag_result"] = {
                "success": True,
                "message": "Documents retrieved successfully",
                "retrieved_docs": retrieved_content,
                "total_chunks": len(retrieved_content)
            }
            logger.info(f"RAG process completed. Retrieved {len(retrieved_content)} relevant chunks")
            logger.info(f"State after RAG process: {str(state)}")
            return state

        except Exception as e:
            logger.error(f"Error in RAG process: {str(e)}")
            state["rag_result"] = {
                "success": False,
                "message": f"Error processing documents: {str(e)}",
                "retrieved_docs":  []
            }
            return state
        

    async def _get_vector_store(
            self,
            vector_path
    ):
        """
        Load vector store
        """
        try:
            embedding = GoogleGenerativeAIEmbeddings(
            model=settings.GOOGLE_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
            vector_store = FAISS.load_local(
                vector_path,
                embedding,
                allow_dangerous_deserialization=True
            )
            return vector_store
        except Exception as e:
            return log_exception(e, logger)