import os
from typing import Literal, List
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from logger import logger, log_exception
from config.settings import settings

class PdfDocProcess:
    def __init__(self):
        pass

    async def _read_pdf_doc_files(
            self,
            file_extension: Literal["pdf", "docx"],
            file_data: bytes
    ):
        """
        Extract Text from PDF or DOCX files.
        Args:
            file_extension (Literal): "pdf" or "docx"
            file_data (bytes): File data in bytes

        Returns:
            str: Extracted text from the file
        """
        try:
            if file_extension == "pdf":
                text = ""
                pdf_stream = BytesIO(file_data)
                reader = PdfReader(pdf_stream)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
            
            elif file_extension == "docx":
                text = ""
                doc_stream = BytesIO(file_data)
                doc = Document(doc_stream)
                for para in doc.paragraphs:
                    if para.text.strip():
                        text += para.text + "\n"
                return text.strip()
            
            else:
                raise ValueError("Unsupported file extension. Only 'pdf' and 'docx' are allowed.")
        except Exception as e:
            return log_exception(e, logger)
    
    async def _get_doc_chunks(
            self,
            doc_text: str
    ) -> List[str]:
        """
        Split Text into chunks
        """
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size = 500,
                chunk_overlap = 100
            )
            chunks = text_splitter.split_text(
                doc_text
            )
            return chunks
        except Exception as e:
            return log_exception(e, logger)

    async def _get_text_embeddings(
            self,
            chunks: List[str],
            user_id: str,
            session_id: str
    ):
        """
        Create Faiss vector store using Geminiembeddings
        """
        try:
            # Step1: Define embedding model
            embedding = GoogleGenerativeAIEmbeddings(
                model=settings.GOOGLE_EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY
            )

            # Step2: Create FAISS vector store
            vector_store = FAISS.from_texts(
                chunks,
                embedding=embedding
            )

            # Step3: Create directory for FAISS stores if not exists
            storage_dir = os.path.join(
                "vectorstores", 
                f"{user_id}"
            )
            os.makedirs(
                storage_dir,
                exist_ok=True
            )

            # Step4: Define unique path for this user's session
            vector_path = os.path.join(
                storage_dir,
                f"document_{user_id}_{session_id}"
            )

            # Step5: Save FAISS index
            vector_store.save_local(vector_path)

            return vector_path
        except Exception as e:
            return log_exception(e, logger)
