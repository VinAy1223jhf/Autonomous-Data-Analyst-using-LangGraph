# tools/data_transformer.py

from typing import Any, List, Dict, Union
from collections import Counter
from tools.schema_inspector import get_table_columns

def transform_sql_to_viz_data(sql_result: Any, query: str = "") -> Union[Dict, List]:
    """
    Transform SQL results into visualization-friendly format.
    
    Handles:
    - List of tuples (single column) → aggregated counts
    - List of tuples (multiple columns) → list of dicts
    - Already processed data → pass through
    
    Args:
        sql_result: Raw SQL result (list of tuples typically)
        query: Original user query (to infer intent)
        
    Returns:
        Transformed data ready for plotting
    """
    
    # If empty or None, return empty list
    if not sql_result:
        return []
    
    # If already a dict or simple list, return as-is
    if isinstance(sql_result, dict):
        return sql_result
    
    # Convert to list if not already
    if not isinstance(sql_result, list):
        sql_result = list(sql_result)
    
    # Check if it's a list of tuples
    if isinstance(sql_result[0], tuple):
        
        # CASE 1: Single column data (most common for viz)
        if len(sql_result[0]) == 1:
            # Extract values from tuples
            values = [item[0] for item in sql_result]
            
            # Check if categorical (strings) or numeric
            if isinstance(values[0], str):
                # Categorical data → count occurrences
                counts = Counter(values)
                
                # Return as dict for easy plotting
                return {
                    "categories": list(counts.keys()),
                    "counts": list(counts.values()),
                    "total": len(values),
                    "raw_values": values  # Keep original for reference
                }
            else:
                # Numeric data → return as list
                return {
                    "values": values,
                    "total": len(values)
                }
        
        # CASE 2: Multiple columns → convert to list of dicts
        else:
            num_cols = len(sql_result[0])

            # Generate generic column names
            column_names = [f"col_{i}" for i in range(num_cols)]

            rows = []
            for row in sql_result:
                row_dict = {
                    column_names[i]: row[i]
                    for i in range(num_cols)
                }
                rows.append(row_dict)

            return {
                "rows": rows,
                "columns": column_names,
                "total_rows": len(rows)
            }
    


def format_data_for_llm(transformed_data: Union[Dict, List]) -> str:
    """
    Format transformed data into a string description for the LLM.
    
    Args:
        transformed_data: Output from transform_sql_to_viz_data
        
    Returns:
        Human-readable description of the data structure
    """
    
    if isinstance(transformed_data, dict):
        if "categories" in transformed_data:
            # Categorical data
            sample = list(zip(
                transformed_data["categories"][:5], 
                transformed_data["counts"][:5]
            ))
            return f"""
Data type: Categorical counts
Structure: dict with 'categories' and 'counts' keys
Sample: {sample}
Total items: {transformed_data['total']}

Access pattern:
- categories = data['categories']  # List of category names
- counts = data['counts']           # List of counts for each category
"""
        elif "values" in transformed_data:
            # Numeric data
            sample = transformed_data["values"][:10]
            return f"""
Data type: Numeric values
Structure: dict with 'values' key
Sample: {sample}
Total items: {transformed_data['total']}

Access pattern:
- values = data['values']  # List of numeric values
"""
    
    # Fallback for list or other types
    sample = transformed_data[:5] if isinstance(transformed_data, list) else str(transformed_data)[:200]
    return f"""
Data type: {type(transformed_data).__name__}
Sample: {sample}

Access pattern:
- data is a {type(transformed_data).__name__}
"""


# ========================================
# TESTING
# ========================================

if __name__ == "__main__":
    # Test with sample SQL results
    
    # Test 1: Categorical data (Sex column)
    sql_result_sex = [('Male',), ('Female',), ('Male',), ('Male',), ('Female',), ('Male',)]
    transformed = transform_sql_to_viz_data(sql_result_sex)
    print("Test 1: Categorical Data")
    print(f"Input: {sql_result_sex}")
    print(f"Output: {transformed}")
    print(f"LLM Description:\n{format_data_for_llm(transformed)}")
    print("\n" + "="*60 + "\n")
    
    # Test 2: Numeric data (Ages)
    sql_result_ages = [(25,), (30,), (22,), (45,), (35,)]
    transformed = transform_sql_to_viz_data(sql_result_ages)
    print("Test 2: Numeric Data")
    print(f"Input: {sql_result_ages}")
    print(f"Output: {transformed}")
    print(f"LLM Description:\n{format_data_for_llm(transformed)}")