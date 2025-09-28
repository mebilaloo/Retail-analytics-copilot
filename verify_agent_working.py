#!/usr/bin/env python3

from agent.graph_hybrid_new import create_agent
import json

# Initialize agent
agent = create_agent('data/northwind.sqlite', 'docs/')

def run_case(qid, question, format_hint='string'):
    """Run a test case and show detailed diagnostics."""
    item = {
        'id': qid,
        'question': question,
        'format_hint': format_hint
    }
    state = agent.run(item)
    
    print('=' * 60)
    print(f'ID: {qid}')
    print(f'Question: {question}')
    print(f'Answer: {state.get("final_answer")}')
    print(f'Confidence: {state.get("confidence")}')
    print(f'SQL Query: {state.get("sql_query")}')
    print(f'SQL Error: {state.get("sql_error")}')
    
    sql_result = state.get('sql_result')
    if sql_result is not None:
        print(f'SQL Result Rows: {len(sql_result)}')
        if len(sql_result) > 0:
            print(f'First few results: {sql_result[:3]}')
    else:
        print('SQL Result: None')
    
    print(f'Citations: {state.get("citations")}')
    print(f'Route Type: {state.get("route_type")}')
    
    # Show trace to prove which nodes were executed
    trace = state.get('trace', [])
    print(f'Executed Nodes: {[t.get("node") for t in trace]}')
    
    # Show context for RAG questions
    context = state.get('context', [])
    if context:
        print(f'Retrieved Context ({len(context)} chunks):')
        for i, ctx in enumerate(context[:2]):  # Show first 2 chunks
            print(f'  Chunk {i+1}: {ctx[:100]}...')
    
    return state

print("Testing Retail Analytics Agent - Proving Real Functionality")
print("=========================================================")

# Test 1: Pure SQL question - count orders in 1997
print("\n🔍 TEST 1: SQL Query - Count Orders in 1997")
run_case('verify_orders_1997', 'How many orders were placed in 1997?', 'number')

# Test 2: SQL with joins - top customer by revenue  
print("\n🔍 TEST 2: SQL Query with Joins - Top Customer by Revenue")
run_case('verify_top_customer_1997', 'Who was the top customer by revenue in 1997?', 'string')

# Test 3: Document retrieval - policy question
print("\n🔍 TEST 3: Document Retrieval - Return Policy")
run_case('verify_policy_beverages', 'What is the return policy for beverages?', 'number')

# Test 4: Hybrid - requires both SQL and docs
print("\n🔍 TEST 4: Hybrid Query - AOV in Winter 1997")
run_case('verify_aov_winter', 'What was the average order value in winter 1997?', 'number')

print("\n" + "=" * 60)
print("✅ VERIFICATION COMPLETE")
print("If you see real SQL queries, actual row counts, and retrieved document chunks,")
print("then the agent is working with REAL data, not hardcoded fallbacks!")
