# 💰 Financial ChatBot

A multilingual, AI-powered financial assistant that can:

* Fetch uploaded table information per user/session
* Analyze queries and generate SQL automatically
* Execute SQL queries on structured financial data
* Retrieve and analyze content from uploaded documents (RAG)
* Generate contextual responses to user queries
* Maintain user/session-based conversation history

Backend: **Python (≥3.10)**
**Default Port**: `localhost:8888`

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Drashti7312/FinancialChatBot.git
cd FinancialChatBot
```

---

### 2️⃣ Backend Setup (Python)

1. **Create Python Environment** using `uv`:

   ```bash
   uv venv
   uv pip install -r requirements.txt
   # OR install from lock file
   uv pip sync uv.lock
   ```

2. **Run Backend**:

   ```bash
   python app/main.py
   ```

---

### 3️⃣ Environment Variables

1. Copy `.env.example` → `.env`:

   ```bash
   cp .env.example .env
   ```

2. Configure your API key and database:

   ```env
   GOOGLE_API_KEY=Your_Gemini_API_Key
   MONGODB_URL="mongodb://localhost:27017"
   SQL_CONNECTION_URL = "mysql+mysqlconnector://user:password@localhost:3306"
   ```

---

## 📂 Repository Structure

```
app/
 ├── config/            # App configuration
 │    └── settings.py
 ├── core/              # Core AI logic
 │    ├── rag_process.py
 ├── database/          # Mongo & SQL database connections
 │    └── database.py
 ├── schema/            # Pydantic models
 │    └── models.py
 ├── logger.py
 ├── main.py            # FastAPI entrypoint
 └── graph.py           # LangGraph workflow (FinancialChatBot)
solutions/              # Graph visualization (flow.png)
Documents/              # Sample financial documents
```

---

## 🔧 Workflow Overview (graph.py)

The chatbot uses **LangGraph** to define its execution flow.

### Flow:

1. **fetch\_table\_info** → Retrieve uploaded table metadata (per user/session)
2. **analyze\_query** → Use LLM to generate SQL query from user input and table schema
3. **Conditional Branching** →

   * `execute_sql`: Run the generated SQL on structured data
   * `rag_process`: If SQL is invalid, fallback to document retrieval
   * `generate_response`: If no data available, respond directly
4. **generate\_response** → Create final answer based on SQL results, RAG content, or fallback message
5. **END**

**Flow Diagram:**
![LangGraph Flow Diagram](solutions/flow.png)

---

## 🌍 Multilingual Support

* Implemented in `ChatGoogleGenerativeAI` prompt chains
* Queries and responses can be processed in multiple languages

---

## 💬 Chat Features

* **User & Session Tracking** — Every query is tied to a user and session
* **SQL Query Generation** — LLM generates optimized MySQL queries
* **Document Retrieval (RAG)** — If no table data fits, fallback to document search
* **Smart Response Generation** — Answers only from SQL results or RAG data
* **Error Handling** — Explains when data is missing or query cannot be answered

---

## 🧩 Tech Stack

* **Backend**: Python ≥3.10, FastAPI
* **LangGraph**: For state-based workflow orchestration
* **Google Generative AI (Gemini)**: LLM query analysis & response generation
* **Databases**:

  * MongoDB (chat history, documents)
  * SQL Engine (structured financial data)
