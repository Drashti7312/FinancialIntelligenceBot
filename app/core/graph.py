import pandas as pd
from typing import Literal
from langgraph.graph import StateGraph, END
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from database.database import db_manager, sql_engine
from config.settings import settings
from logger import logger
from schema.models import ChatBotState, SQLResponse
from core.rag_process import RAGProcess

class FinancialChatBot:
    def __init__(self):
        self.output_parser = PydanticOutputParser(
            pydantic_object=SQLResponse
        )
        self.llm = ChatGoogleGenerativeAI(
            model = settings.GOOGLE_GEMINI_MODEL,
            google_api_key = settings.GOOGLE_API_KEY,
            temperature = 0.1
        )
        self.graph = self._build_graph()

    def _build_graph(
            self
    ) -> StateGraph:
        """
        Build the LangGraph Workflow
        """
        workflow = StateGraph(ChatBotState)

        # Add nodes
        workflow.add_node("fetch_table_info", self._fetch_table_info)
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("execute_sql", self._execute_sql)
        workflow.add_node("rag_process", self._rag_process)
        workflow.add_node("generate_response", self._generate_response)

        # Define edges
        workflow.set_entry_point("fetch_table_info")
        workflow.add_edge("fetch_table_info", "analyze_query")
        workflow.add_conditional_edges(
            "analyze_query",
            self._should_execute_sql,
            {
                "execute": "execute_sql",
                "respond": "generate_response",
                "rag": "rag_process"
            }
        )
        workflow.add_edge("execute_sql", "generate_response")
        workflow.add_edge("rag_process", "generate_response")
        workflow.add_edge("generate_response", END)
        
        flow = workflow.compile()
        # Save the graph visualization as PNG
        # try:
        #     import os
        #     png_data = flow.get_graph().draw_mermaid_png()
        #     os.makedirs("solutions", exist_ok=True)
        #     with open("solutions/flow.png", "wb") as f:
        #         f.write(png_data)
        #     logger.info("Graph visualization saved as flow.png")
        # except Exception as viz_error:
        #     logger.warning(f"Could not save graph visualization: {viz_error}")

        return flow
    
    async def _fetch_table_info(
            self,
            state: ChatBotState
    ) -> ChatBotState:
        """
        Fetch all table information from MongoDB based on user_id and session_id
        """
        try:
            logger.info(f"Fetching table info for user: {state['user_id']}, session: {state['session_id']}")

            table_info =  await db_manager.database.documents_data.find_one(
                {
                    "user_id": state['user_id'],
                    "session_id": state['session_id']
                },
                {
                    "_id": 0,
                    "documents": 1
                }
            )
            if table_info and "documents" in table_info:
                state["table_info"] = table_info["documents"]
                logger.info(f"Found {len(table_info['documents'])} tables for user")
            else:
                state["table_info"] = []
                logger.warning(f"No table information found for user")
            logger.info(f"State After Fetching Table Info {str(state)}")
            return state
        except Exception as e:
            logger.error(f"Error occured while fetching table info: {e}")
            return state

    async def _analyze_query(
            self,
            state: ChatBotState
    ) -> ChatBotState:
        """
        Analyze user query with LLM to generate SQL Query. 
        """
        try:
            system_prompt = """
You are an expert financial data analyst and SQL query generator. Your goal is to create a correct, optimized SQL query based on the user question and the given table schema details.

### Context:
- User Query: {user_query}
- Available Tables & Schema: {table_information}

### Rules:
1. Only use tables and columns mentioned in `table_information`. Do NOT assume columns that do not exist.
2. Prefer using **table aliases** for clarity.
3. If the query involves joining multiple tables, use appropriate **JOIN conditions** based on matching keys (e.g., user_id, transaction_id).
4. Use **aggregate functions** (SUM, AVG, COUNT) where relevant.
5. If the user asks for recent data, assume **ORDER BY date DESC LIMIT X** where X is reasonable (like 10).
6. Avoid SELECT *; only select necessary columns.
7. Return only the SQL query, nothing else. Do not explain or include extra text.
8. Validate SQL syntax and make sure it will run in MySQL 8.0.
9. Do NOT include `DROP`, `DELETE`, `INSERT`, or any destructive statements.

### Required Output Format:
{format_instructions}

### Additional Considerations:
- If the user asks for a date range, use BETWEEN or appropriate filtering.
- For percentage calculations, use correct MySQL syntax.
- Always enclose column names and table names in backticks (`) if needed.
"""
            prompt = PromptTemplate(
                template=system_prompt,
                input_variables=["user_query", "table_information"],
                partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
            )

            chain = prompt | self.llm | self.output_parser
            response = await chain.ainvoke({
                "user_query": state["user_query"],
                "table_information": state["table_info"]
            })
            if not isinstance(response, SQLResponse):
                logger.error("Invalid response format from LLM")
                state["sql_response"] = SQLResponse(
                    response=False, 
                    message="Invalid SQL generation."
                )
            state["sql_response"] = response
            logger.info(f"State After Analyze Query {str(state)}")
            return state
        except Exception as e:
            logger.error(f"Error in analyze_query: {str(e)}")
            state["sql_response"] = SQLResponse(
                response=False,
                message="Error processing your request. Please try again."
            )
            return state
        
    def _should_execute_sql(
            self,
            state: ChatBotState
    ) -> Literal["execute", "respond", "rag"]:
        """
        Conditional edge function to determine next step
        """
        if not state["sql_response"] or not state["sql_response"].response :
            logger.info("SQL response is None - routing to RAG node")
            return "rag"
        elif state["sql_response"] and state["sql_response"].response:
            logger.info("Execute SQL Node will be called")
            return "execute"
        else:
            logger.info("Direct Response will be generated")
            return "respond"
    
    async def _execute_sql(
            self,
            state: ChatBotState
    ) -> ChatBotState:
        """
        Execute the SQL query and fetch results
        """
        try:
            if not state["sql_response"] or not state["sql_response"].message:
                state["sql_result"] = []
                return state
            query = state["sql_response"].message
            if "DROP" in query.upper() or "DELETE" in query.upper():
                raise ValueError("Potential dangerous SQL detected.")
            df = pd.read_sql(query, sql_engine)
            state["sql_result"] = df.to_dict('records')
            logger.info(f"SQL query executed successfully. Retrieved {len(state['sql_result'])} rows")
            logger.info(f"State after executing sql query {str(state)}")
            return state
        except Exception as e:
            logger.error(f"Error executing SQL query: {str(e)}")
            state["sql_result"] = []
            state["sql_response"] = SQLResponse(
                response=False,
                message = f"""Error execting query: {str(e)}
                Previous sql_response: {str(state["sql_response"])}"""
            )
            return state
        
    async def _generate_response(
            self,
            state: ChatBotState
    ) -> ChatBotState:
        """
        Generate final response using LLM
        """
        try:
            if state["sql_response"] and state["sql_response"].response and state["sql_result"]:
                # Successful query execution
                logger.info("Successful query execution. ")
                system_prompt = """
You are a financial data analyst. Analyze the SQL query result and provide insights that are relevant to the asked query.

### Instructions:
1. **ALWAYS base your response ONLY on the given SQL Query Result and user query.**
2. First, identify what the user has asked to provide.
3. Then, generate answer structured output based on SQL Query Result
4. Do not guess values; only use provided data.
5. If the result is empty, respond: "No data found for your query."
6. If query is unrelated to financial data, say: "I am a Financial ChatBot. Please ask me questions related to financial data."
7. Be concise (max 200 words), clear, and business-oriented.
8. No need to add anything extra, just provide SQL Query result related answer.
9. Try to provide full answer based on user query and SQL Query result
10. If for example 'SUM(`transaction_count`)": null' provide as SQL Query Result it means, No data found related to User Query, So, respond accordingly.

User Query: {user_query}
SQL Query Result:
{sql_result}
"""
            elif state["rag_result"]:
                 system_prompt = """
You are a financial data analyst. Analyze RAG result and user query, and provide insights based on the retrieved document content.

Rules:
1. **ALWAYS base your response ONLY on the given RAG Result and user query.**
2. First, identify what the user has asked to provide.
3. Then, generate answer structured output based on RAG Result content.
4. If the RAG result contains no relevant information for the query, clearly state: "The uploaded documents don't contain information relevant to your query."
5. If the RAG result is empty or failed, respond: "No documents found. Please upload files first."
6. Make sure to include all relevant details from the retrieved document chunks.
7. Be concise (max 200 words), clear, and business-oriented.
8. If the query is unrelated to financial documents, say: "I am a Financial ChatBot. Please ask me questions related to financial documents or data."
9. Reference specific document sections when providing information (e.g., "According to the document...").
10. Do not hallucinate or add information not present in the RAG Result.

User Query: {user_query}
RAG Result: {rag_result}
"""
            else:
                # Failed query or no data
                logger.info("Failed query or no data")
                system_prompt = """
You are a helpful financial assistant. Explain clearly why the query cannot be answered with the given data.

### Rules:
1. Be empathetic and helpful.
2. Keep response concise (max 50 words).
3. If the query is unrelated to finance, respond: "I am a Financial ChatBot. Please ask questions related to financial data."
4. If it's a greeting, greet back and invite a financial question.
5. If table info is missing, inform the user they must upload documents.
6. If no matching data, say the query returned no results.

User Query: {user_query}
SQL Query Response: {sql_response}
SQL Query Result: {sql_result}
"""
  
            prompt = PromptTemplate(
                template=system_prompt,
                input_variables=["user_query", "sql_response", "sql_result"]
            )

            chain = prompt | self.llm
            response = await chain.ainvoke({
                "user_query": state["user_query"],
                "sql_response": state["sql_response"],
                "sql_result": state["sql_result"],
                "rag_result": state["rag_result"]
            })
            state["final_response"] = response.content
            logger.info(f"Final response returned to user: {state['final_response']}")
            logger.info(f"Final State: {str(state)}")
            return state
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            state["final_response"] = "I apologize, but I encountered an error while processing your request. Please try again."
            return state

    async def process_query(
            self,
            user_id: str,
            session_id: str,
            user_query: str
    ) -> str:
        """
        Main method to process user queries

        Args:
            user_id: User Identifier
            session_id: Session Identifier
            user_query: User's Query related to Financial data
        Returns:
            Final response string
        """
        initial_state = ChatBotState(
            user_id=user_id,
            session_id=session_id,
            user_query=user_query,
            table_info=None,
            sql_response=None,
            sql_result=None,
            rag_result={},
            final_response="",
            messages=[]
        )
        try:
            final_state = await self.graph.ainvoke(initial_state)
            return {
                "sql_response": final_state["sql_response"],
                "sql_result": final_state["sql_result"],
                "rag_result": final_state["rag_result"],
                "response": final_state["final_response"]
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error while processing your request. Please try again."
            }

    async def _rag_process(
            self,
            state: ChatBotState
    ):
        try:
            logger.info("Starting RAG process")
            state = await RAGProcess()._rag_process(
                state
            )
            return state
        except Exception as e:
            logger.info(f"Error in RAG process: {str(e)}")
            return state
