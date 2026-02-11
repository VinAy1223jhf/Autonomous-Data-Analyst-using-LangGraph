# tests/test_viz_supervisor_integration.py

"""
End-to-end integration tests for the Visualization Agent.

This test file simulates the complete flow:
1. User query: "Generate pie chart for male and female percentages"
2. SQL Agent gets data
3. Data Transformer converts to viz-friendly format
4. Viz Agent generates matplotlib code
5. Python Executor runs the code
6. Plot is created and verified

Run with: pytest tests/test_viz_supervisor_integration.py -v
"""

from agents.sql_agent import generate_and_execute_sql
from agents.viz_agent import generate_viz_code
from tools.python_executor import run_plot_code
from tools.data_transformer import transform_sql_to_viz_data, format_data_for_llm

# ========================================
# MANUAL TESTING (for debugging)
# ========================================

def run_manual_test():
    """
    Manual test for debugging with actual agents.
    
    Run with: python -m tests.test_viz_supervisor_integration
    """
    print("=" * 60)
    print("🚀 Running Manual End-to-End Test")
    print("=" * 60)
    
    
    
    user_query = "Create a pie chart showing the percentage of males and females in the dataset"
    
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
    run_plot_code(viz_code, transformed_data)
    print(f"✅ Plot displayed!")


if __name__ == "__main__":
    run_manual_test()