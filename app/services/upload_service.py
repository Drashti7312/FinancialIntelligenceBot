from typing import Dict, Any
from datetime import datetime
from config.settings import settings
from database.database import db_manager, sql_engine
from logger import logger, log_exception
from services.excel_process import ExcelFileProcess
from services.pdf_doc_process import PdfDocProcess

class UploadService:
    def __init__(
            self, 
            user_id, 
            session_id,
            file_data,
            filename,
            file_extension
        ):
        self.excel_utils = ExcelFileProcess()
        self.pdf_doc_utils = PdfDocProcess()
        self.user_id = user_id
        self.session_id = session_id
        self.file_data = file_data
        self.filename = filename
        self.file_extension = file_extension

    async def upload_document(
            self
    ):
        try:
            # Check file already exists or not
            logger.info("Checking if file already exists")
            if await self.check_exist_files():
                logger.info("File already exists")
                return {"error": "File already exists"}
            
            logger.info("File Extension is %s", self.file_extension)
            if self.file_extension in settings.EXCEL_FILE_EXTENSIONS:
                logger.info("Processing Excel file")
                return await self._excel_file_process()
            elif self.file_extension in settings.DOCUMENT_FILE_EXTENSIONS:
                logger.info("Processing Document file")
                return await self.pdf_doc_process()
            else:
                logger.warning("Unsupported file extension: %s", self.file_extension)
                return {"error": "Unsupported file extension"}
        except Exception as e:
            return log_exception(e, logger)

    async def _excel_file_process(
            self
    ):
        try:
            logger.info("Processing Excel file")
            # Step1: Read Excel file
            df = await self.excel_utils._read_excel_files(
                self.file_extension, 
                self.file_data
            )
            if df.empty:
                logger.warning("Uploaded Excel file is empty: %s", self.filename)
                return {"error": "Uploaded file is empty"}
            
            # Step2: Data Cleaning
            cleaned_df = await self.excel_utils._data_cleaning(df)

            # Step3: Fetch Information from the table
            df_info = await self.excel_utils._fetch_df_info(cleaned_df)

            # Step4: Store excel file info into GridFS
            file_id = await self.save_file_gridfs()

            # Step5: Save Excel Info and file id in document collection
            await self.save_file_and_details(file_id, df_info)

            # Step6: Save file in local SQLLite
            table_name = f"user_id_{self.user_id}_file_id_{file_id}".replace("-","_")
            cleaned_df.to_sql(
                table_name, 
                con=sql_engine,
                if_exists="replace", 
                index=False
            )
            logger.info(f"Table Name {table_name} created in SQLite database")
            return True
        except Exception as e:
            return log_exception(e, logger)


    async def save_file_gridfs(
            self
    ) -> str:
        try:
            file_id = await db_manager.fs_bucket.upload_from_stream(
                self.filename,
                self.file_data,
                metadata={
                    "user_id": self.user_id,
                    "session_id": self.session_id
                }
            )
            return str(file_id)
        except Exception as e:
            return log_exception(e, logger)
        
    async def save_file_and_details(
            self,
            file_id: str,
            documents_details: Dict[str, Any]
    ): 
        try:
            documents_details["file_id"] = file_id
            documents_details["filename"] = self.filename
            documents_details["sql_tablename"] = f"user_id_{self.user_id}_file_id_{file_id}".replace("-","_")
            documents_details["file_extension"] = self.file_extension
            documents_details["uploaded_at"] = datetime.now()
            await db_manager.database.documents_data.update_one(
                {
                    "user_id": self.user_id,
                    "session_id": self.session_id
                },
                {
                    "$push": 
                        {
                            "documents": documents_details
                        },
                        "$setOnInsert": {"created_at": datetime.now()}
                },
                upsert=True
            )
            logger.info("Document added in collection")
            return True
        except Exception as e:
            return log_exception(e, logger)

    async def check_exist_files(
            self
    ):
        try:
            return await db_manager.database["fs.files"].find_one({
                "filename": self.filename,
                "metadata.session_id": self.session_id,
                "metadata.user_id": self.user_id
            })
        except Exception as e:
            return log_exception(e, logger)

    async def pdf_doc_process(
            self
    ):
        try:
            logger.info("Processing Excel file")
            # Step1: Read Excel file
            doc_text = await self.pdf_doc_utils._read_pdf_doc_files(
                self.file_extension, 
                self.file_data
            )
            logger.info("Document text extracted")
            # Step2: Split into chunks
            chunks = await self.pdf_doc_utils._get_doc_chunks(
                doc_text
            )
            logger.info("Document text splitted into chunks")

            # Step3: Generate embeddings and store it to FAISS
            await self.pdf_doc_utils._get_text_embeddings(
                chunks,
                self.user_id,
                self.session_id
            )
            logger.info("Document embeddings created and stored in FAISS")

            # Step4: Store excel file info into GridFS
            await self.save_file_gridfs()

            return True
        except Exception as e:
            return log_exception(e, logger)
