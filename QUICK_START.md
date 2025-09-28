# 🎓 QUICK START 

## **Assignment: LangGraph + DSPy Hybrid Agent**
**Status: ✅ COMPLETE - Ready for Grading**

---

## **🚀 HOW TO RUN (3 Steps)**

### **Step 1: Install**
```bash
pip install -r requirements.txt
ollama pull qwen2.5:0.5b  # Download from https://ollama.ai
```

### **Step 2: Start Ollama**
```bash
ollama serve  # In separate terminal
```

### **Step 3: Run Assignment**
```bash
python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out 
```

**⏱️ Expected Time:** 5-10 minutes for 6 questions  

---

## **✅ WHAT YOU'LL SEE**

The system will process 6 test questions and generate answers like:

```json
{"id": "q1", "final_answer": "Beverages have a 14-day return policy...", "citations": ["product_policy::chunk0"]}
{"id": "q2", "final_answer": "Top products: Côte de Blaye ($53M)...", "sql": "SELECT p.ProductName, SUM(...)"}
```

**✅ Real SQL queries generated**  
**✅ Real database results (600K+ records)**  
**✅ Document citations from policy files**

---

## **🔍 ASSIGNMENT REQUIREMENTS CHECK**

| Requirement | ✅ Status | Where to Verify |
|-------------|-----------|-----------------|
| **LangGraph 6+ nodes** | ✅ Done | `agent/graph_hybrid.py` lines 36-43 |
| **DSPy integration** | ✅ Done | `agent/dspy_signatures.py` (3 signatures) |
| **RAG system** | ✅ Done | `docs/` folder + `agent/rag/` |
| **Local model** | ✅ Done | Uses Ollama (no paid APIs) |
| **CLI interface** | ✅ Done | `--batch` and `--out` flags work |
| **Sample questions** | ✅ Done | `sample_questions_hybrid_eval.jsonl` |

---

## **🧪 QUICK TESTS**

### **Test Database:**
```bash
python -c "import sqlite3; c=sqlite3.connect('data/northwind.sqlite'); print('Products:', c.execute('SELECT COUNT(*) FROM Products').fetchone()[0])"
```
**Expected:** `Products: 77`

### **Test Documents:**
```bash
ls docs/
```
**Expected:** 4 files (policies, KPIs, calendar, catalog)

### **Test Components:**
```bash
python test_schema_fix.py
```
**Expected:** Schema loaded, SQL working, real data results

---

## **💡 WHAT MAKES THIS SPECIAL**

- **Real Business Data:** 77 products, 93 customers, 600K+ order records
- **Hybrid Intelligence:** Combines database queries + document search
- **Error Handling:** SQL repair loop (fixes wrong queries automatically)
- **Local Deployment:** No API keys, runs completely offline
- **Citations:** Shows exactly where answers come from

---

## **🚨 TROUBLESHOOTING**

- **Slow?** ⏳ Normal (30-60 sec per query with local LLM)
- **Warnings?** ⚠️ DSPy JSON warnings are harmless
- **Crashes?** 🔧 Check if Ollama is running: `ollama serve`

---

