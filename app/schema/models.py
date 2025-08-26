from pydantic import BaseModel, Field
from typing import Optional, TypedDict, List, Dict, Any

class SQLResponse(BaseModel):
    response: bool = Field(
        description="Is SQL Query possible or not"
    )
    message: str = Field(
        description="Full SQL Query"
    )
    table_name: Optional[str] = Field(
        None, 
        description="Relevant sql_tablename from the Tables Information"
    )

class ChatBotState(TypedDict):
    user_id: str
    session_id: str
    user_query: str
    table_info: Optional[List[Dict[str, Any]]]
    sql_response: Optional[SQLResponse]
    sql_result: Optional[List[Dict[str, Any]]]
    rag_result: Dict
    final_response: str
    messages: List[Any]
