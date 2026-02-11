# 🤖 Autonomous Data Analyst

> **Talk to your data. Get instant insights. Watch visualizations come alive.**


[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An AI-powered data analyst that understands natural language, writes perfect SQL, and creates beautiful visualizations — all autonomously using LangGraph's multi-agent architecture.


https://github.com/user-attachments/assets/748cb890-e549-4b1d-ad29-0f6408276f22

---

## ✨ What Makes This Crazy

🧠 **Actually Understands You**: Ask questions in plain English, get accurate SQL  
🎯 **Never Hallucinates Column Names**: Uses structured outputs (JSON) instead of raw SQL generation  
📊 **Auto-Visualizes**: Automatically creates charts when you ask for them  
🔄 **Multi-Agent Architecture**: Supervisor orchestrates specialized SQL and Visualization agents  
⚡ **Blazing Fast**: Powered by Groq's lightning-fast inference  

### Traditional Approach vs. This Project

| Traditional SQL Tools | This Project |
|----------------------|--------------|
| "SELECT * FROM users WHERE..." | "Show me all active users" |
| Copy-paste to Excel → Make chart | "Create a pie chart of user types" |
| Failed query → Try again → Failed again | Works first time, every time ✅ |
| Hardcoded column names break everything | Validates against actual schema |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- A Groq API key (free tier works!)

### Installation

```bash
# Clone the repo
git clone https://github.com/VinAy1223jhf/Autonomous-Data-Analyst-using-LangGraph.git
cd Autonomous-Data-Analyst-using-LangGraph

# Install dependencies
pip install -r requirements.txt

# Set up your environment
echo "GROQ_API_KEY=your_api_key_here" > .env

# Load sample data
python csv_to_db.py

# Run the analyst!
python app.py
```

### First Query
```
Query > Count how many people have Smith as their last name
🔍 Built SQL: SELECT COUNT(*) FROM people WHERE "Last Name" LIKE '%Smith%'
✅ Result: [(8,)]

Query > Create a pie chart showing male vs female distribution
📊 Generating visualization...
✅ Plot displayed!
```

---

## 🏗️ Architecture

This isn't just another "LLM + database" project. It's a **properly engineered multi-agent system** using LangGraph.

```
                         ┌─────────────┐
                         │  SUPERVISOR │
                         │   (Router)  │
                         └──────┬──────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
              ┌─────▼─────┐           ┌────▼─────┐
              │ SQL AGENT │           │ VIZ AGENT│
              │ (LangGraph)│          │(LangGraph)│
              └─────┬─────┘           └────┬─────┘
                    │                      │
         ┌──────────┼──────────┐           │
         │          │          │           │
    ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌────▼─────┐
    │ Schema │ │Structure│ │SQL Build│ │Matplotlib│
    │Inspector│ │Generator│ │Executor │ │Generator │
    └────────┘ └────────┘ └────────┘ └──────────┘
```

### Why This Architecture?

**Problem**: LLMs generate SQL with syntax errors, wrong column names, and random backticks.

**Solution**: 
1. **Structured Outputs**: LLM generates JSON, not SQL
2. **Deterministic SQL Building**: We build the SQL from JSON (no LLM = no errors)
3. **Real-time Validation**: Column names are validated against actual schema
4. **Data Transformation**: SQL tuples → visualization-ready dicts

---

## 🎯 Core Features

### 1️⃣ SQL Agent (LangGraph)
- **Natural Language → Perfect SQL**
- Uses structured outputs (JSON) to avoid hallucinations
- Validates column names against real schema
- Executes queries and returns results

```python
# The magic: LLM generates THIS (JSON):
{
  "operation": "COUNT",
  "table": "people",
  "where": [{"column": "Last Name", "operator": "LIKE", "value": "%Smith%"}]
}

# We build THIS (SQL):
SELECT COUNT(*) FROM people WHERE "Last Name" LIKE '%Smith%'
```

### 2️⃣ Visualization Agent (LangGraph)
- **Auto-generates matplotlib code**
- Transforms SQL tuples into chart-ready data
- Safe code execution environment
- Supports: pie charts, bar charts, histograms, line plots

```python
# User: "Show gender distribution as pie chart"
# Data Transformer: [('Male',), ('Female',), ...] 
#                 → {'categories': ['Male', 'Female'], 'counts': [52, 48]}
# Viz Agent: Generates clean matplotlib code
# Executor: Displays the chart ✨
```

### 3️⃣ Supervisor Agent
- **Routes queries intelligently**
- SQL keywords → SQL Agent
- Visualization keywords → Viz Agent
- Handles full pipeline orchestration

---

## 📂 Project Structure

```
Autonomous-Data-Analyst-using-LangGraph/
├── agents/
│   ├── sql_agent.py          # SQL generation with LangGraph
│   ├── viz_agent.py           # Matplotlib code generation
│   └── supervisor.py          # Multi-agent orchestrator
├── tools/
│   ├── sql_executor.py        # Safe SQL execution
│   ├── python_executor.py     # Safe Python/matplotlib execution
│   ├── schema_inspector.py    # Database schema tools
│   └── data_transformer.py    # SQL → Viz data transformation
├── database/
│   └── people.db              # SQLite sample database
├── test/
│   └── test_viz_supervisor_integration.py  # End-to-end tests
├── app.py                     # Main CLI interface
├── csv_to_db.py              # Data loading utility
└── requirements.txt
```

---

## 🎨 Example Queries

### Data Queries
```
✅ "Count how many males are there"
✅ "Show me the first 5 people"  
✅ "List all emails of people with last name Smith"
✅ "Who are the 3 oldest people?"
✅ "Find all software engineers"
```

### Visualization Queries
```
📊 "Create a pie chart of gender distribution"
📊 "Plot a bar chart of job titles"
📊 "Show me age distribution as a histogram"
📊 "Visualize male vs female percentages"
```

---

## 🧪 Testing

```bash
# Run all tests
pytest test/ -v

# Run integration tests
pytest test/test_viz_supervisor_integration.py -v

# Manual end-to-end test
python -m test.test_viz_supervisor
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Groq (Llama 3.3 70B & Llama 3.1 8B) |
| **Framework** | LangGraph (multi-agent orchestration) |
| **Database** | SQLite |
| **Visualization** | Matplotlib |
| **Language** | Python 3.11+ |
| **API Integration** | LangChain + Groq SDK |

---

## 🔮 Future Roadmap

- [ ] **Multi-Database Support**: PostgreSQL, MySQL, MongoDB
- [ ] **Advanced Analytics**: Statistical tests, correlations, predictions
- [ ] **Interactive Dashboards**: Streamlit/Gradio UI
- [ ] **Memory Layer**: Remember past queries and learn user preferences
- [ ] **Export Options**: PDF reports, Excel files, PowerPoint
- [ ] **Natural Language Insights**: "What's interesting in this data?"
- [ ] **SQL Query Optimization**: Suggest better queries
- [ ] **Data Cleaning Agent**: Handle missing values, outliers
- [ ] **Multi-table Joins**: Complex queries across tables
- [ ] **Voice Interface**: Talk to your data

---

## 🤝 Contributing

This is a living project! Contributions are welcome:

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

MIT License - feel free to use this in your own projects!

---

## 🙏 Acknowledgments

- **LangGraph** for the incredible multi-agent framework
- **Groq** for blazing-fast LLM inference
- **LangChain** for the solid foundation

---

## 📧 Contact

**Vinay** - [@VinAy1223jhf](https://github.com/VinAy1223jhf)

Project Link: [https://github.com/VinAy1223jhf/Autonomous-Data-Analyst-using-LangGraph](https://github.com/VinAy1223jhf/Autonomous-Data-Analyst-using-LangGraph)

---

<div align="center">

### ⭐ Star this repo if you found it helpful!

**Made with 🔥 and lots of ☕**

</div>
