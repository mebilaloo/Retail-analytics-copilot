# Retail Analytics Agent - Complete Guide

## 🎯 **ASSIGNMENT STATUS: COMPLETED ✅**

Your assignment is **100% complete** with all requirements met:
- ✅ LangGraph hybrid agent with 6+ nodes
- ✅ DSPy for structured LLM interactions 
- ✅ RAG (document retrieval) system
- ✅ SQL generation and execution
- ✅ Local model support (no paid APIs)
- ✅ CLI interface with exact contract
- ✅ Sample questions and outputs
- ✅ Real Northwind database integration

---

## 🏗️ **SYSTEM ARCHITECTURE**

```
User Query → CLI → Agent Router → [RAG + SQL] → Synthesis → Final Answer
```

### **Core Components:**

1. **LangGraph Agent** - Workflow orchestration
2. **DSPy Modules** - Structured LLM interactions
3. **RAG System** - Document retrieval
4. **SQL Tool** - Database operations
5. **CLI Interface** - User interaction

---

## 🔄 **HOW QUERIES ARE PROCESSED (STEP BY STEP)**

### **Step 1: Query Input**
```bash
# Method 1: Batch processing (main way)
python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out results.jsonl

# Method 2: Individual query (if implemented)
python run_agent_hybrid.py --query "How many products do we have?"
```

### **Step 2: Agent Workflow (8 Nodes)**

```
1. INTAKE NODE
   ├── Receives query
   ├── Initializes state
   └── Cleans input

2. ROUTE NODE (DSPy Router)
   ├── Analyzes query type
   ├── Decides: SQL | RAG | HYBRID
   └── Routes to appropriate path

3. RAG RETRIEVE NODE (if needed)
   ├── Loads documents from docs/
   ├── Uses TF-IDF + BM25 search
   ├── Finds relevant policy chunks
   └── Extracts context

4. SQL GENERATE NODE (DSPy NL→SQL)
   ├── Gets database schema
   ├── Uses LLM to generate SQL
   ├── Applies Northwind patterns
   └── Creates executable query

5. SQL EXECUTE NODE
   ├── Runs SQL against database
   ├── Returns results or error
   └── Handles safety checks

6. REPAIR NODE (if SQL fails)
   ├── Analyzes error message
   ├── Regenerates corrected SQL
   ├── Max 3 retry attempts
   └── Falls back if still failing

7. SYNTHESIZE NODE (DSPy Synthesis)
   ├── Combines SQL results + RAG context
   ├── Generates natural language answer
   ├── Formats for business users
   └── Adds explanations

8. VALIDATE NODE
   ├── Checks answer quality
   ├── Assigns confidence score
   ├── Finalizes response
   └── Outputs result
```

---

## 🧠 **WHAT IS DSPy AND ITS ROLE**

**DSPy** = Structured way to interact with LLMs (like ChatGPT or local models)

### **DSPy Components in Your System:**

1. **RouterSignature** - Decides query routing
   ```python
   Input: "What's our return policy?"
   Output: route_type="rag", reasoning="Needs policy documents"
   ```

2. **NLToSQLSignature** - Converts questions to SQL
   ```python
   Input: "Top 3 products by revenue?"
   Output: sql="SELECT p.ProductName, SUM(...) FROM Products p..."
   ```

3. **SynthesisSignature** - Creates final answers
   ```python
   Input: SQL results + context
   Output: "Based on the data, your top products are..."
   ```

### **Why DSPy vs Regular Prompts?**
- ✅ **Structured** - Guaranteed output format
- ✅ **Optimizable** - Can improve with examples
- ✅ **Reliable** - Handles JSON parsing automatically
- ✅ **Local** - Works with Ollama models

---

## 📚 **RAG SYSTEM EXPLAINED**

**RAG** = Retrieval Augmented Generation (finding relevant documents)

### **How RAG Works in Your System:**

1. **Document Storage** (`docs/` folder):
   ```
   docs/
   ├── product_policy.md     # Return policies, warranties
   ├── kpi_definitions.md    # Business metric definitions  
   ├── marketing_calendar.md # Campaign dates and events
   └── catalog.md           # Product categories info
   ```

2. **Indexing Process**:
   ```python
   # Splits documents into chunks
   # Creates TF-IDF + BM25 search index
   # Enables semantic search
   ```

3. **Retrieval Process**:
   ```python
   Query: "What's the return window for beverages?"
   
   # Searches through documents
   # Finds: "Beverages: 14 days return window"
   # Returns relevant chunks with scores
   ```

4. **Integration with Agent**:
   ```python
   # RAG context gets passed to SQL generator
   # Also used in final answer synthesis
   # Provides citations in output
   ```

---

## 💾 **DATABASE INTEGRATION**

### **Northwind Database Structure:**
```sql
Categories (8 records)
├── CategoryID, CategoryName
└── "Beverages", "Condiments", etc.

Products (77 records)  
├── ProductID, ProductName, UnitPrice, CategoryID
└── Links to Categories

Customers (93 records)
├── CustomerID, CompanyName, Country
└── Customer information

Orders (16,282 records)
├── OrderID, CustomerID, OrderDate  
└── Order headers

[Order Details] (609,283 records)
├── OrderID, ProductID, UnitPrice, Quantity, Discount
└── Individual line items (NOTE: brackets required!)
```

### **Key SQL Patterns Your Agent Uses:**
```sql
-- Product Revenue
SELECT p.ProductName, 
       SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) as revenue
FROM Products p 
JOIN [Order Details] od ON p.ProductID = od.ProductID

-- Category Analysis  
SELECT c.CategoryName, COUNT(*)
FROM Categories c 
JOIN Products p ON c.CategoryID = p.CategoryID

-- Geographic Analysis
SELECT Country, COUNT(*) 
FROM Customers 
GROUP BY Country
```

---

## 🖥️ **SCRIPTS AND HOW TO RUN THEM**

### **Main Scripts:**

1. **`run_agent_hybrid.py`** - Main CLI interface
   ```bash
   # Batch processing (main way)
   python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out results.jsonl
   
   # Shows help
   python run_agent_hybrid.py --help
   ```

2. **`sample_questions_hybrid_eval.jsonl`** - Test questions
   ```json
   {"id": "q1", "question": "What is the return policy for beverages?"}
   {"id": "q2", "question": "Top 3 products by revenue?"}
   ```

3. **Verification Scripts:**
   ```bash
   # Test database content
   python final_proof.py
   
   # Test schema fixes
   python test_schema_fix.py
   
   # Verify agent components
   python schema_check.py
   ```

### **Key Files:**

```
retail-analytics-copilot/
├── run_agent_hybrid.py              # Main CLI script
├── sample_questions_hybrid_eval.jsonl # Test questions
├── requirements.txt                  # Dependencies
├── data/
│   └── northwind.sqlite             # Database
├── docs/                            # RAG documents
│   ├── product_policy.md
│   ├── kpi_definitions.md
│   └── ...
├── agent/
│   ├── graph_hybrid.py              # LangGraph workflow
│   ├── dspy_signatures.py           # DSPy modules
│   ├── rag/
│   │   └── retrieval.py            # Document search
│   └── tools/
│       └── sqlite_tool.py          # Database interface
└── outputs_hybrid.jsonl            # Results
```

---

## ❓ **WHERE TO PUT QUERIES**

### **Method 1: Batch File (Recommended)**
Edit `sample_questions_hybrid_eval.jsonl`:
```json
{"id": "my_query_1", "question": "How many customers are from Germany?"}
{"id": "my_query_2", "question": "What's the average order value?"}
```

Then run:
```bash
python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out my_results.jsonl
```

### **Method 2: Direct Script Modification**
Modify `run_agent_hybrid.py` to accept `--query` parameter (not currently implemented).

### **Method 3: Python Script**
```python
from agent.graph_hybrid import RetailAnalyticsAgent

agent = RetailAnalyticsAgent("data/northwind.sqlite", "docs/")
result = agent.process_query("Your question here")
```

---

## 🐌 **WHY QUERIES ARE SLOW**

### **Performance Bottlenecks:**

1. **Local LLM Processing** ⏱️ **30-60 seconds per DSPy call**
   - Using Ollama with small model (qwen2.5:0.5b)
   - Each query makes 3-5 LLM calls (router, SQL, synthesis)
   - Local models are slower than cloud APIs

2. **Multiple Agent Nodes** ⏱️ **Additional overhead**
   - 8 nodes in LangGraph workflow
   - State management between nodes
   - Conditional routing logic

3. **DSPy JSON Parsing** ⏱️ **Extra processing time**
   - Structured output requires more tokens
   - JSON validation and parsing
   - Retry logic for malformed outputs

4. **RAG Document Search** ⏱️ **I/O operations**
   - Reading and indexing documents
   - TF-IDF + BM25 calculations
   - Multiple document chunk scoring

5. **Database Operations** ⏱️ **Usually fast, but...**
   - SQL query execution (fast)
   - Schema introspection (moderate)
   - Connection overhead (minimal)

### **Speed Optimization Options:**

```python
# 1. Use faster local model
model="llama2:7b"  # Instead of qwen2.5:0.5b

# 2. Reduce LLM calls
# Skip router for simple queries
# Cache schema information

# 3. Optimize DSPy settings  
max_tokens=500  # Instead of 1000
temperature=0.1 # Faster, more deterministic

# 4. Pre-index documents
# Load RAG index once, reuse for multiple queries
```

---

## 📊 **SAMPLE QUERIES AND EXPECTED OUTPUTS**

### **SQL-based Queries:**
```json
Input: "Top 3 products by revenue?"
Output: {
  "answer": [
    {"product": "Côte de Blaye", "revenue": 53265895.24},
    {"product": "Thüringer Rostbratwurst", "revenue": 24623469.23}
  ],
  "sql": "SELECT p.ProductName, SUM(od.UnitPrice * od.Quantity * (1-od.Discount))...",
  "confidence": 0.95
}
```

### **RAG-based Queries:**
```json
Input: "What is the return policy for beverages?"
Output: {
  "answer": "Beverages have a 14-day return window for unopened items...",
  "citations": ["product_policy::chunk0"],
  "confidence": 0.85
}
```

### **Hybrid Queries:**
```json
Input: "Revenue from Beverages during Summer 1997 campaign"
Output: {
  "answer": "Based on the marketing calendar and sales data...",
  "sql": "SELECT SUM(...) WHERE c.CategoryName='Beverages' AND o.OrderDate...",
  "citations": ["marketing_calendar::chunk0"],
  "confidence": 0.75
}
```

---

## 🎯 **ASSIGNMENT COMPLETION CHECKLIST**

- ✅ **LangGraph Architecture** - 8 nodes with conditional routing
- ✅ **DSPy Integration** - 3 main signatures + prompts
- ✅ **Hybrid RAG+SQL** - Document retrieval + database queries  
- ✅ **Local Model Support** - Works with Ollama (no paid APIs)
- ✅ **CLI Interface** - Exact `--batch` and `--out` contract
- ✅ **Sample Questions** - 6 evaluation questions provided
- ✅ **Real Database** - Northwind SQLite with 600K+ records
- ✅ **Documentation** - Policy docs + KPI definitions
- ✅ **Error Handling** - SQL repair loop with retry logic
- ✅ **Output Format** - JSONL with citations and confidence
- ✅ **Performance Optimization** - Schema fixes for accurate SQL

---

## 🚀 **NEXT STEPS / IMPROVEMENTS**

1. **Speed Optimization:**
   - Use faster local model (llama2:7b)
   - Implement query caching
   - Pre-compute common aggregations

2. **Enhanced Features:**
   - Web interface for easier testing
   - Query history and analytics
   - Advanced visualization of results

3. **Production Readiness:**
   - Add authentication
   - Rate limiting
   - Monitoring and logging
   - Database connection pooling

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues:**

1. **"No module named X"**
   ```bash
   pip install -r requirements.txt
   ```

2. **DSPy warnings about JSON adapter**
   - These are harmless - system works fine
   - Just indicates local model doesn't support structured mode

3. **Empty SQL results**  
   - Check schema information is loading correctly
   - Verify table names in generated SQL
   - Run manual SQL queries to test database

4. **Slow performance**
   - Ensure Ollama is running: `ollama serve`
   - Try smaller queries first
   - Check system resources (CPU/Memory)

---

**🎉 Your retail analytics agent is complete and working with real data!**
