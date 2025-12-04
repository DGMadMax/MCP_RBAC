"""
SQL MCP Server - Text-to-SQL with RBAC
Port: 8002
Adapted from user's rag_utils/csv_query.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from langchain_groq import ChatGroq
from sqlalchemy.orm import Session
import tabulate

from app.config import settings
from app.database import SessionLocal
from app.models import Employee
from app.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# FastAPI App
# =============================================================================
app = FastAPI(
    title="SQL MCP Server",
    description="Text-to-SQL with RBAC table filtering",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq LLM
llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_model,
    temperature=0.0
)


# =============================================================================
# RBAC Logic (from user's code)
# =============================================================================
def get_allowed_tables_for_role(role: str) -> list[str]:
    """
    Determine which tables a role can access
    Adapted from user's csv_query.py
    """
    if role.lower() == "c-level":
        # C-Level can see all tables
        return ["employees", "general_data"]  # Add more tables as needed
    elif role.lower() == "employee":
        # General employees only see general data
        return ["general_data"]
    else:
        # Team members see their department + general
        # e.g., "HR Team" → ["employees", "general_data"]
        # "Finance Team" → ["finance_data", "general_data"]
        if "hr" in role.lower():
            return ["employees", "general_data"]
        elif "finance" in role.lower():
            return ["finance_data", "general_data"]
        else:
            return ["general_data"]


FORBIDDEN_KEYWORDS = ["insert", "update", "delete", "drop", "alter", "create", "truncate"]


def is_safe_query(sql: str) -> bool:
    """
    Check if SQL query is safe (SELECT only)
    Adapted from user's csv_query.py
    """
    lowered = sql.strip().lower().rstrip(";")
    
    # Must start with SELECT
    if not lowered.startswith("select"):
        return False
    
    # Must not contain forbidden keywords
    if any(word in lowered for word in FORBIDDEN_KEYWORDS):
        return False
    
    return True


# =============================================================================
# Text-to-SQL (adapted from user's code, using Groq)
# =============================================================================
def translate_nl_to_sql(question: str, allowed_tables: list[str]) -> str:
    """
    Convert natural language question to SQL query using Groq
    Adapted from user's csv_query.py (replaced OpenAI → Groq)
    """
    # Get schema for allowed tables
    db = SessionLocal()
    
    # For now, we only have employees table
    # TODO: Extend with more tables as needed
    schema_info = """
Table: employees
Columns: id, employee_id, full_name, role, department, email, location, 
         date_of_birth, date_of_joining, manager_id, salary, leave_balance, 
         leaves_taken, attendance_pct, performance_rating, last_review_date
"""
    
    db.close()
    
    # Filter schema to only allowed tables
    allowed_schema = "\n".join([
        line for line in schema_info.split("\n")
        if any(table in line.lower() for table in allowed_tables)
    ])
    
    # Prompt for Groq LLM
    prompt = f"""You are a SQL expert. Convert the following natural language question into a valid SQLite SELECT query.

Available Tables and Columns:
{allowed_schema}

Rules:
1. ONLY use tables from the schema above
2. ONLY generate SELECT queries (no INSERT/UPDATE/DELETE)
3. Use proper SQL syntax for SQLite
4. If aggregating, use appropriate GROUP BY
5. Return ONLY the SQL query, no explanations

Question: {question}

SQL Query:"""
    
    try:
        response = llm.invoke(prompt)
        sql = response.content.strip()
        
        # Clean up SQL (remove markdown code blocks if present)
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        logger.debug(f"Generated SQL: {sql}")
        return sql
        
    except Exception as e:
        logger.error(f"Failed to generate SQL: {str(e)}")
        raise


# =============================================================================
# Schemas
# =============================================================================
class SQLQueryRequest(BaseModel):
    query: str
    user_role: str
    user_id: int


class SQLQueryResponse(BaseModel):
    success: bool
    sql: Optional[str] = None
    result: Optional[str] = None
    row_count: Optional[int] = None
    error: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================
@app.post("/query", response_model=SQLQueryResponse)
async def execute_sql_query(request: SQLQueryRequest):
    """
    Execute text-to-SQL query with RBAC filtering
    
    Flow:
    1. Get allowed tables for user role
    2. Generate SQL using Groq
    3. Validate SQL (safety check)
    4. Execute against SQLite
    5. Return formatted results
    """
    try:
        logger.info(f"SQL query request from user {request.user_id} (role: {request.user_role})")
        
        # Step 1: Get allowed tables
        allowed_tables = get_allowed_tables_for_role(request.user_role)
        logger.debug(f"Allowed tables for {request.user_role}: {allowed_tables}")
        
        # Step 2: Generate SQL
        sql = translate_nl_to_sql(request.query, allowed_tables)
        
        # Step 3: Safety check
        if not is_safe_query(sql):
            logger.warning(f"Unsafe SQL query blocked: {sql}")
            return SQLQueryResponse(
                success=False,
                error="Only SELECT queries are allowed"
            )
        
        # Step 4: Execute query
        db = SessionLocal()
        try:
            result = db.execute(sql)
            rows = result.fetchall()
            columns = result.keys()
            
            # Step 5: Format as markdown table
            if rows:
                # Convert to list of tuples for tabulate
                table_data = [[str(cell) for cell in row] for row in rows]
                markdown_table = tabulate.tabulate(table_data, headers=columns, tablefmt="github")
            else:
                markdown_table = "No results found."
            
            logger.info(f"SQL query successful | Rows: {len(rows)}")
            
            return SQLQueryResponse(
                success=True,
                sql=sql,
                result=markdown_table,
                row_count=len(rows)
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"SQL query failed: {str(e)}")
        return SQLQueryResponse(
            success=False,
            error=str(e)
        )


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "SQL MCP Server",
        "port": 8002,
        "llm_ready": llm is not None
    }


# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
