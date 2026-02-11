# agents/sql_agent.py

from typing import Annotated, Literal, Optional, List, Dict, Any
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.message import AnyMessage, add_messages
from dotenv import load_dotenv
import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tools.schema_inspector import get_tables, get_table_columns
from tools.sql_executor import run_sql
# Load environment
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

# -------- Structured Query Format --------
class WhereClause(TypedDict):
    column: str
    operator: Literal["=", ">", "<", ">=", "<=", "LIKE", "!="]
    value: str


class QueryStructure(TypedDict):
    operation: Literal["SELECT", "COUNT"]
    table: str
    columns: List[str]
    where: Optional[List[WhereClause]]
    order_by: Optional[str]
    order_direction: Optional[Literal["ASC", "DESC"]]
    limit: Optional[int]


# -------- Agent State --------
class SQLAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    tables: list[str]
    selected_table: str
    columns: list[str]
    user_query: str
    query_structure: QueryStructure
    sql_query: str
    result: Any


# -------- Initialize LLM --------
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# -------- SQL Builder (Deterministic - No LLM!) --------
def build_sql_from_structure(structure: QueryStructure) -> str:
    """
    Build SQL query from structured format.
    This is 100% deterministic - no LLM errors possible!
    """
    
    # Start building query
    if structure["operation"] == "COUNT":
        sql = "SELECT COUNT(*)"
    else:
        # Quote columns with spaces
        columns = [f'"{col}"' if ' ' in col else col for col in structure["columns"]]
        if columns:
            sql = f"SELECT {', '.join(columns)}"
        else:
            sql = "SELECT *"
    
    # Add table
    sql += f" FROM {structure['table']}"
    
    # Add WHERE clauses
    if structure.get("where"):
        where_parts = []
        for clause in structure["where"]:
            col = f'"{clause["column"]}"' if ' ' in clause["column"] else clause["column"]
            op = clause["operator"]
            val = f"'{clause['value']}'"
            where_parts.append(f"{col} {op} {val}")
        
        sql += f" WHERE {' AND '.join(where_parts)}"
    
    # Add ORDER BY
    if structure.get("order_by"):
        col = structure["order_by"]
        col = f'"{col}"' if ' ' in col else col
        direction = structure.get("order_direction", "ASC")
        sql += f" ORDER BY {col} {direction}"
    
    # Add LIMIT (but NOT for COUNT queries)
    if structure.get("limit") and structure["operation"] != "COUNT":
        sql += f" LIMIT {structure['limit']}"
    
    return sql


# -------- Node 1: User Input --------
def user_input_node(state: SQLAgentState) -> SQLAgentState:
    """Store user query in state"""
    last_msg = state["messages"][-1]
    return {
        "messages": [HumanMessage(content=last_msg.content)],
        "user_query": last_msg.content
    }


# -------- Node 2: Fetch Tables --------
def fetch_tables_node(state: SQLAgentState) -> SQLAgentState:
    """Fetch all table names from database"""
    tables = get_tables()
    return {
        "messages": [AIMessage(content=f"Available tables: {tables}")],
        "tables": tables
    }


# -------- Node 3: Select Table --------
table_selection_prompt = ChatPromptTemplate.from_messages([
    ("system", "Output ONLY the most relevant table name from the list provided. No explanations."),
    ("user", "Question: {user_query}\nTables: {tables}\nTable:")
])


def select_table_node(state: SQLAgentState) -> SQLAgentState:
    """LLM chooses the most relevant table"""
    response = llm.invoke(
        table_selection_prompt.format_messages(
            user_query=state["user_query"],
            tables=", ".join(state["tables"])
        )
    )
    
    return {
        "messages": [AIMessage(content=f"Selected: {response.content.strip()}")],
        "selected_table": response.content.strip()
    }


# -------- Node 4: Fetch Schema --------
def fetch_schema_node(state: SQLAgentState) -> SQLAgentState:
    """Fetch column names for selected table"""
    table = state["selected_table"]
    columns = get_table_columns(table)
    
    return {
        "messages": [AIMessage(content=f"Columns: {columns}")],
        "columns": columns
    }


# -------- Node 5: Generate Query Structure (JSON) --------
structure_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a query structure analyzer. Output ONLY valid JSON, no markdown, no backticks, no explanations.

Your task: Convert the user's question into a structured query format.

CRITICAL RULE: Use ONLY the EXACT column names from the provided list. Copy them character-for-character including spaces and capitalization.

OUTPUT FORMAT (valid JSON only):
{{
  "operation": "SELECT" or "COUNT",
  "table": "table_name",
  "columns": ["exact_column_name"] or [] for COUNT,
  "where": [
    {{"column": "exact_column_name", "operator": "=", "value": "value"}}
  ] or null,
  "order_by": "exact_column_name" or null,
  "order_direction": "ASC" or "DESC" or null,
  "limit": 5 or null
}}

COLUMN NAME RULES:
- MUST use exact column names from the list (including spaces, capitalization)
- If you see "First Name" in the list, use "First Name" (not First_Name, not first_name)
- If you see "Last Name" in the list, use "Last Name" (not Last_Name, not lastname)
- If you see "Date of birth" in the list, use "Date of birth" (not birthdate, not dob)
- If you see Sex in the list, use Sex (not Gender)
- NEVER invent or modify column names

WHERE CLAUSE RULES:
- For "has Smith in last name" → use LIKE operator with %Smith%
- For "last name is Smith" → use = operator with Smith
- For "equals" → use = operator
- For "not equals" → use != operator
- Values are case-insensitive in SQL: 'Smith' matches 'smith'

ORDER BY RULES:
- "oldest" means earliest date → ORDER BY date column ASC
- "youngest" means latest date → ORDER BY date column DESC

EXAMPLES:

Question: "Count males"
Available columns: Index, "First Name", "Last Name", Sex, Email
{{
  "operation": "COUNT",
  "table": "people",
  "columns": [],
  "where": [{{"column": "Sex", "operator": "=", "value": "Male"}}],
  "order_by": null,
  "order_direction": null,
  "limit": null
}}

Question: "Count people with Smith in last name"
Available columns: Index, "First Name", "Last Name", Sex
{{
  "operation": "COUNT",
  "table": "people",
  "columns": [],
  "where": [{{"column": "Last Name", "operator": "LIKE", "value": "%Smith%"}}],
  "order_by": null,
  "order_direction": null,
  "limit": null
}}

Question: "First names of 3 oldest people"
Available columns: Index, "First Name", "Last Name", "Date of birth"
{{
  "operation": "SELECT",
  "table": "people",
  "columns": ["First Name"],
  "where": null,
  "order_by": "Date of birth",
  "order_direction": "ASC",
  "limit": 3
}}

Question: "Show me 5 people"
Available columns: Index, "First Name", "Last Name", Email
{{
  "operation": "SELECT",
  "table": "people",
  "columns": ["First Name", "Last Name", "Email"],
  "where": null,
  "order_by": null,
  "order_direction": null,
  "limit": 5
}}

OUTPUT ONLY THE JSON:"""),
    ("user", """Question: {user_query}
Table: {table}
Available columns: {columns}

JSON:""")
])


def generate_structure_node(state: SQLAgentState) -> SQLAgentState:
    """LLM generates structured query format (JSON)"""
    
    response = llm.invoke(
        structure_prompt.format_messages(
            user_query=state["user_query"],
            table=state["selected_table"],
            columns=", ".join(state["columns"])
        )
    )
    
    # Clean up response
    json_str = response.content.strip()
    
    # Remove markdown if present
    json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    # Parse JSON
    try:
        structure = json.loads(json_str)
        
        # VALIDATION: Force correct table name
        structure["table"] = state["selected_table"]
        
        # VALIDATION: Check all columns exist
        available_columns = state["columns"]
        
        # Validate selected columns
        if structure.get("columns"):
            for col in structure["columns"]:
                if col not in available_columns:
                    raise ValueError(
                        f"❌ Column '{col}' not found in table.\n"
                        f"Available columns: {', '.join(available_columns)}"
                    )
        
        # Validate WHERE clause columns
        if structure.get("where"):
            for clause in structure["where"]:
                if clause["column"] not in available_columns:
                    raise ValueError(
                        f"❌ Column '{clause['column']}' not found in WHERE clause.\n"
                        f"Available columns: {', '.join(available_columns)}"
                    )
        
        # Validate ORDER BY column
        if structure.get("order_by"):
            if structure["order_by"] not in available_columns:
                raise ValueError(
                    f"❌ Column '{structure['order_by']}' not found in ORDER BY.\n"
                    f"Available columns: {', '.join(available_columns)}"
                )
        
        # Set defaults
        if "operation" not in structure:
            structure["operation"] = "SELECT"
        if "columns" not in structure:
            structure["columns"] = []
        if "where" not in structure:
            structure["where"] = None
        if "order_by" not in structure:
            structure["order_by"] = None
        if "order_direction" not in structure:
            structure["order_direction"] = None
        if "limit" not in structure:
            structure["limit"] = None
            
        return {
            "messages": [AIMessage(content=f"Structure: {json.dumps(structure, indent=2)}")],
            "query_structure": structure
        }
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM: {json_str}\nError: {e}")




# def clean_sql_result(sql_result):
#     if not sql_result:
#         return sql_result

#     # Single-row, single-column → scalar (COUNT, SUM, AVG)
#     if (
#         isinstance(sql_result, list)
#         and len(sql_result) == 1
#         and isinstance(sql_result[0], tuple)
#         and len(sql_result[0]) == 1
#     ):
#         return sql_result[0][0]

#     # Multi-row, single-column → list
#     if (
#         isinstance(sql_result, list)
#         and isinstance(sql_result[0], tuple)
#         and len(sql_result[0]) == 1
#     ):
#         return [row[0] for row in sql_result]

#     return sql_result


    
# -------- Node 6: Build SQL & Execute (All in one!) --------
def build_and_execute_node(state: SQLAgentState) -> SQLAgentState:
    """
    Build SQL from structure and execute it immediately.
    This catches errors right away!
    """
    
    structure = state["query_structure"]
    
    # Build SQL (deterministic, no LLM)
    sql = build_sql_from_structure(structure)
    
    print(f"\n🔍 Built SQL: {sql}")
    
    # Execute SQL immediately
    try:
        result = run_sql(sql)
        # print(f"✅ Raw SQL Result: {result}")
        # final_result = clean_sql_result(result)
        print(f"✅ Execution successful")
        print(f"📊 Result: {result}")
        
        return {
            "messages": [AIMessage(content=f"SQL executed successfully")],
            "sql_query": sql,
            "result": result
        }
        
    except Exception as e:
        error_msg = f"SQL execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Return error in state
        return {
            "messages": [AIMessage(content=error_msg)],
            "sql_query": sql,
            "result": {"error": str(e)}
        }


from langgraph.graph import StateGraph, END

def build_graph():
    """Build the LangGraph workflow"""
    
    # Create the graph
    workflow = StateGraph(SQLAgentState)
    
    # Add nodes
    workflow.add_node("user_input", user_input_node)
    workflow.add_node("fetch_tables", fetch_tables_node)
    workflow.add_node("select_table", select_table_node)
    workflow.add_node("fetch_schema", fetch_schema_node)
    workflow.add_node("generate_structure", generate_structure_node)
    workflow.add_node("build_and_execute", build_and_execute_node)
    
    # Define edges (workflow)
    workflow.set_entry_point("user_input")
    workflow.add_edge("user_input", "fetch_tables")
    workflow.add_edge("fetch_tables", "select_table")
    workflow.add_edge("select_table", "fetch_schema")
    workflow.add_edge("fetch_schema", "generate_structure")
    workflow.add_edge("generate_structure", "build_and_execute")
    workflow.add_edge("build_and_execute", END)
    
    # Compile the graph
    return workflow.compile()


# Create the compiled graph
sql_agent_graph = build_graph()


# ========================================
# MAIN FUNCTION
# ========================================

def generate_and_execute_sql(user_query: str) -> Dict[str, Any]:
    """
    Main entry point called by supervisor.
    Uses LangGraph to execute the workflow.
    """
    
    # Initialize state
    initial_state = {
        "messages": [HumanMessage(content=user_query)]
    }
    
    # Run the graph
    final_state = sql_agent_graph.invoke(initial_state)
    
    # Return both SQL and results
    return {
        "sql": final_state.get("sql_query", ""),
        "result": final_state.get("result", ""),
        "structure": final_state.get("query_structure", {})
    }


# ========================================
# TESTING
# ========================================

if __name__ == "__main__":
    test_queries = [
        "Count how many people have Smith as their last name",
        "Count total number of males",
        "Show me the first 3 people",
        "List 5 emails",
        "Get first names of 3 oldest people",
        "Count total number of people",
        "How many people have Smith in their last name?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        try:
            response = generate_and_execute_sql(query)
            print(f"\n✅ SQL: {response['sql']}")
            print(f"📊 Result: {response['result']}")
        except Exception as e:
            print(f"❌ Error: {e}")

