# agents/supervisor.py

from agents.sql_agent import generate_and_execute_sql
from agents.viz_agent import generate_viz_code
from tools.python_executor import run_plot_code
from tools.data_transformer import transform_sql_to_viz_data, format_data_for_llm

def supervisor(user_query: str) -> dict:
    """
    Supervisor agent that routes queries to appropriate sub-agents.
    
    Current version (v1): SQL-only routing
    Future: Can add visualization, analysis, etc.
    
    Args:
        user_query: The user's natural language question
        
    Returns:
        dict with 'next_agent' and 'result' keys
    """
    
    uq = user_query.lower()

    # check for visualization-type query
    viz_keywords = ["plot", "graph", "visualize", "chart", "show me a graph of", "show me a plot of","create"]
    sql_keywords = ["count", "list", "show", "fetch", "oldest", "youngest", 
                    "how many", "find", "get", "select", "display", "who",
                    "what", "which", "all", "total", "first", "last"]
    if any(word in uq for word in viz_keywords):
        try:
            # Step 1: Get data from SQL agent
            print(f"\n📊 Query: {user_query}")
            sql_response = generate_and_execute_sql(user_query)
            print(f"✅ SQL: {sql_response['sql']}")
            print(f"✅ Data: {sql_response['result']}")
            
            # Step 2: Transform data
            print(f"\n🔄 Transforming data...")
            transformed_data = transform_sql_to_viz_data(sql_response['result'], user_query)
            data_description = format_data_for_llm(transformed_data)
            print(f"✅ Transformed: {transformed_data}")
            
            # Step 3: Generate viz code
            print(f"\n🎨 Generating visualization code...")
            viz_code = generate_viz_code(user_query, transformed_data, data_description)
            print(f"✅ Generated Code:\n{viz_code}")
            
            # Step 4: Execute visualization
            print(f"\n🖼️  Executing plot...")
            fig = run_plot_code(viz_code, transformed_data)
            print(f"✅ Plot displayed!")
            return {
                "next_agent": "viz",
                "result": fig,
                "code": viz_code
            }
        except Exception as e:
            print(f"\n❌ Error in visualization pipeline: {e}")
            return {
                "next_agent": "error",
                "result": {
                    "error": str(e),
                    "message": "Failed to process visualization query"
                }
            }

    # Check if this is a SQL-type query
    
    
    elif any(word in uq for word in sql_keywords):
        try:
            print(f"\n🔄 Routing to SQL Agent...")
            print(f"   User query: {user_query}")
            
            # Call SQL agent (generates + executes in one step!)
            response = generate_and_execute_sql(user_query)
            
            # Check if there was an error
            if isinstance(response["result"], dict) and "error" in response["result"]:
                return {
                    "next_agent": "error",
                    "result": {
                        "sql": response["sql"],
                        "error": response["result"]["error"],
                        "message": "SQL execution failed"
                    }
                }
            
            # Success!
            return {
                "next_agent": "sql",
                "result": {
                    "sql": response["sql"],
                    "rows": response["result"],
                    "structure": response.get("structure", {})
                }
            }
            
        except Exception as e:
            print(f"\n❌ Error in SQL pipeline: {e}")
            return {
                "next_agent": "error",
                "result": {
                    "error": str(e),
                    "message": "Failed to process SQL query"
                }
            }

    # Default: Query not supported
    return {
        "next_agent": "end",
        "result": "I can only handle data queries right now. Try asking me to count, list, or show data."
    }