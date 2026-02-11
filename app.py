# app_streamlit.py

import streamlit as st
from agents.supervisor import supervisor

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Autonomous Data Analyst",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🤖 Autonomous Data Analyst (v1)")
st.markdown("""
Ask questions about your database in natural language.

**Example queries**
- Count how many people have Smith as their last name  
- Show me the first 5 people  
- List all emails  
- Generate pie chart for male and female percentages
""")

st.divider()

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# --------------------------------------------------
# USER INPUT
# --------------------------------------------------
user_query = st.text_input(
    "💬 Enter your query",
    placeholder="e.g. Count total number of females"
)

submit = st.button("Run Query 🚀")

# --------------------------------------------------
# MAIN LOGIC
# --------------------------------------------------
if submit and user_query.strip():
    try:
        response = supervisor(user_query)

        # Save history
        st.session_state.history.append(
            {"query": user_query, "response": response}
        )
        
        # ---------------- SQL RESPONSE ----------------
        if response["next_agent"] == "sql":
            st.subheader("📝 Generated SQL")
            st.code(response["result"]["sql"], language="sql")

            st.subheader("📊 Results")
            st.write(response["result"]["rows"])

        # ---------------- VISUALIZATION RESPONSE ----------------
        elif response["next_agent"] == "viz":
            st.subheader("Generated python code")
            st.code(response["code"], language="python")
            st.subheader("🖼️ Visualization")
            st.pyplot(response["result"])

        # ---------------- ERROR ----------------
        elif response["next_agent"] == "error":
            st.error(response["result"]["message"])
            st.exception(response["result"]["error"])

        # ---------------- FALLBACK ----------------
        else:
            st.info(response["result"])

    except Exception as e:
        st.error("❌ Unexpected error")
        st.exception(e)

# --------------------------------------------------
# QUERY HISTORY (OPTIONAL BUT USEFUL)
# --------------------------------------------------
if st.session_state.history:
    st.divider()
    st.subheader("🕘 Query History")

    for i, item in enumerate(reversed(st.session_state.history), 1):
        with st.expander(f"Query {i}: {item['query']}"):
            resp = item["response"]
            if resp["next_agent"] == "sql":
                st.code(resp["result"]["sql"], language="sql")
                st.write(resp["result"]["rows"])
            else:
                st.write(resp["result"])
