# tools/sql_executor.py

from langchain_community.utilities import SQLDatabase

# Database URI - update path if needed
DB_URI = "sqlite:///database/people.db"

# Initialize database connection
db = SQLDatabase.from_uri(DB_URI)


def run_sql(query: str) -> str:
    """
    Execute SQL safely and return result as string.
    Deterministic tool – NO LLM HERE.
    
    Args:
        query: SQL query string to execute
        
    Returns:
        Query results as string, or error message
    """
    try:
        result = db.run(query)
        
        if not result:
            return "Query returned no results."
        
        return result
        
    except Exception as e:
        # Return the error for debugging
        raise Exception(f"SQL execution error: {str(e)}")


def get_db():
    """
    Expose DB object if schema/tools are needed.
    
    Returns:
        SQLDatabase instance
    """
    return db


# Optional: Helper function to get table names
def get_table_names() -> list[str]:
    """
    Get list of all table names in the database.
    
    Returns:
        List of table names
    """
    return db.get_usable_table_names()


# Optional: Helper function to get table info
def get_table_info(table_names: list[str] = None) -> str:
    """
    Get schema information for specified tables.
    
    Args:
        table_names: List of table names, or None for all tables
        
    Returns:
        Table schema information as string
    """
    return db.get_table_info(table_names=table_names)