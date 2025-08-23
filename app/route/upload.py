from fastapi import File, UploadFile, APIRouter, HTTPException
from logger import logger
from config.settings import settings
from services.upload_service import UploadService
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/upload", tags=["Upload Routes"])

@router.post("/upload_document")
async def upload_document(
    user_id: str,
    session_id: str,
    file: UploadFile = File(...)
):
    """Upload a document (CSV, EXCEL, PDF, DOCX)"""
    logger.info("Uploading document")
    try:
        if not file.filename:
            logger.warning("Upload attempt with no filename")
            raise HTTPException(
                status_code=400, 
                detail="No file uploaded"
            )

        file_extension = file.filename.rsplit(".", 1)[-1].lower()
        if file_extension not in settings.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file type attempted: {file_extension}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{file_extension}'. "
                       f"Supported types: {', '.join(settings.SUPPORTED_EXTENSIONS)}"
            )
        # Read file data
        file_data = await file.read()
        if not file_data:
            logger.warning("Empty file uploaded")
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        document = await UploadService(
            user_id=user_id,
            session_id=session_id,
            file_data=file_data,
            filename=file.filename,
            file_extension=file_extension
        ).upload_document()
        if document:
            if isinstance(document, dict) and "error" in document:
                return {
                    "success": False,
                    "message": document["error"]
                }
            response_data = {
                "success": True,
                "message": f"File '{file.filename}' uploaded successfully."
            }
        else:
            response_data = {
                "success": False,
                "message": f"File '{file.filename}' upload failed."
            }
        return JSONResponse(response_data)

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in upload_document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
