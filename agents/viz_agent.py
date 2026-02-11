# agents/viz_agent.py

from typing import Any, Dict
from dotenv import load_dotenv
import os
import re

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# -------------------------------------------------
# ENV
# -------------------------------------------------
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

# -------------------------------------------------
# PROMPT
# -------------------------------------------------
viz_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a data visualization expert.

Your task:
- Generate Python matplotlib code ONLY
- The code will receive a variable called `data`
- `data` has been PRE-PROCESSED for easy visualization
- DO NOT perform data transformations or aggregations
- The data is READY TO PLOT

DATA FORMAT (IMPORTANT):
- For categorical data (e.g., gender distribution):
  data = {{
    'categories': [('Male'), ('Female')],
    'counts': [52, 48],
    'total': 100
  }}
  
- For numeric data (e.g., ages):
  data = {{
    'values': [25, 30, 22, 45, ...],
    'total': 100
  }}

STRICT RULES:
- Use matplotlib ONLY
- Do NOT import anything (matplotlib is already available as `plt`)
- Do NOT explain anything
- Do NOT wrap code in markdown or backticks
- Assume `data` already exists in scope
- Use ONLY: data['categories'], data['counts'], data['values']
- Do NOT use: len(), sum(), min(), max(), Counter(), set(), sorted()
- Data is ALREADY aggregated - just plot it!

CHART RULES:
- For categorical data → use data['categories'] and data['counts']
- For numeric data → use data['values']
- Pie chart: plt.pie(data['counts'], labels=data['categories'], autopct='%1.1f%%')
- Bar chart: plt.bar(data['categories'], data['counts'])
- Histogram: plt.hist(data['values'], bins=10)

EXAMPLE CODE FOR PIE CHART:
plt.pie(data['counts'], labels=data['categories'], autopct='%1.1f%%')
plt.title('Distribution')
plt.show()

EXAMPLE CODE FOR BAR CHART:
plt.bar(data['categories'], data['counts'])
plt.xlabel('Category')
plt.ylabel('Count')
plt.title('Distribution')
plt.show()

REMEMBER: Data is already processed! Just access the dict keys and plot!
"""
        ),
        (
            "user",
            """
User request:
{query}

Data structure:
{data}

Generate ONLY the matplotlib code to plot this data.
"""
        )
    ]
)
# -------------------------------------------------
# HELPER FUNCTION
# -------------------------------------------------
def strip_code_markers(code: str) -> str:
    """
    Remove markdown code fences and backticks from LLM output.
    
    Handles patterns like:
    - ```python ... ```
    - ```... ```
    - ``` ... ```
    """
    # Remove markdown code blocks
    code = re.sub(r'^```(?:python)?\s*\n', '', code, flags=re.MULTILINE)
    code = re.sub(r'\n```\s*$', '', code, flags=re.MULTILINE)
    
    # Remove any remaining standalone backticks
    code = code.strip('`').strip()
    
    return code

# -------------------------------------------------
# PUBLIC FUNCTION
# -------------------------------------------------
def generate_viz_code(query: str, data: Any, data_description: str = "") -> str:
    """
    Generates matplotlib code (string) for visualization.
    Strips any markdown backticks before returning.
    
    Args:
        query: User's visualization request
        data: Transformed data (dict or list)
        data_description: Description of data structure for LLM
    """

    response = llm.invoke(
        viz_prompt.format_messages(
            query=query,
            data=data_description if data_description else str(data)
        )
    )

    raw_code = response.content.strip()
    
    # Strip backticks before returning
    clean_code = strip_code_markers(raw_code)
    
    return clean_code

def sanitize_plot_code(code: str) -> str:
    """
    Removes all import statements from generated Python code.
    This is required because the executor already injects libraries (e.g., plt).
    """

    cleaned_lines = []

    for line in code.splitlines():
        stripped = line.strip()

        # Skip any import statements
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


