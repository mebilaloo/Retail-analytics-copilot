"""
LangGraph Hybrid Agent with 6+ nodes and repair functionality.
This module implements a retail analytics agent using LangGraph architecture.
"""

from typing import Dict, List, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import Graph, START, END
from langgraph.prebuilt import ToolNode
import dspy
from .dspy_signatures import RouterSignature, NLToSQLSignature, SynthesisSignature
from .rag.retrieval import retrieve_context
from .tools.sqlite_tool import SQLiteTool


class RetailAnalyticsAgent:
    """Hybrid agent combining LangGraph workflow with DSPy modules."""
    
    def __init__(self, db_path: str, docs_path: str):
        self.db_path = db_path
        self.docs_path = docs_path
        self.sqlite_tool = SQLiteTool(db_path)
        
        # Initialize DSPy modules - only SQL generation uses advanced optimizer
        self.router = dspy.Predict(RouterSignature)  # Simple prediction for routing
        self.nl_to_sql = dspy.ChainOfThought(NLToSQLSignature)  # MAIN OPTIMIZER: Complex SQL generation
        self.synthesis = dspy.Predict(SynthesisSignature)  # Simple prediction for synthesis
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> Graph:
        """Build the LangGraph workflow with 6+ nodes."""
        workflow = Graph()
        
        # Add nodes
        workflow.add_node("intake", self._intake_node)
        workflow.add_node("route", self._route_node)
        workflow.add_node("rag_retrieve", self._rag_retrieve_node)
        workflow.add_node("sql_generate", self._sql_generate_node)
        workflow.add_node("sql_execute", self._sql_execute_node)
        workflow.add_node("repair", self._repair_node)
        workflow.add_node("synthesize", self._synthesize_node)
        workflow.add_node("validate", self._validate_node)
        
        # Add edges
        workflow.add_edge(START, "intake")
        workflow.add_edge("intake", "route")
        workflow.add_conditional_edges(
            "route",
            self._route_decision,
            {"sql": "sql_generate", "rag": "rag_retrieve", "hybrid": "rag_retrieve"}
        )
        workflow.add_edge("rag_retrieve", "sql_generate")
        workflow.add_edge("sql_generate", "sql_execute")
        workflow.add_conditional_edges(
            "sql_execute",
            self._execution_decision,
            {"success": "synthesize", "repair": "repair"}
        )
        workflow.add_edge("repair", "sql_execute")
        workflow.add_edge("synthesize", "validate")
        workflow.add_edge("validate", END)
        
        return workflow.compile()
    
    def _intake_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 1: Process incoming query and initialize state."""
        query = state.get("query", "")
        
        return {
            **state,
            "original_query": query,
            "processed_query": query.strip(),
            "context": [],
            "sql_query": None,
            "sql_result": None,
            "repair_attempts": 0,
            "max_repair_attempts": 3
        }
    
    def _route_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 2: Route query to appropriate processing path."""
        query = state["processed_query"]
        
        # Use DSPy router to determine path
        prediction = self.router(query=query)
        route_type = prediction.route_type
        
        return {
            **state,
            "route_type": route_type,
            "routing_reason": prediction.reasoning
        }
    
    def _rag_retrieve_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 3: Retrieve relevant context using RAG."""
        query = state["processed_query"]
        
        # Retrieve context from documentation
        context = retrieve_context(query, self.docs_path)
        
        return {
            **state,
            "context": context
        }
    
    def _sql_generate_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 4: Generate SQL query using DSPy."""
        query = state["processed_query"]
        context = state.get("context", [])
        schema = self.sqlite_tool.get_schema()
        
        # Use DSPy to generate SQL
        prediction = self.nl_to_sql(
            query=query,
            schema=schema,
            context="\n".join(context)
        )
        
        return {
            **state,
            "sql_query": prediction.sql_query,
            "sql_reasoning": prediction.reasoning
        }
    
    def _sql_execute_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 5: Execute SQL query against database."""
        sql_query = state["sql_query"]
        
        try:
            result = self.sqlite_tool.execute_query(sql_query)
            return {
                **state,
                "sql_result": result,
                "execution_error": None,
                "execution_success": True
            }
        except Exception as e:
            return {
                **state,
                "sql_result": None,
                "execution_error": str(e),
                "execution_success": False
            }
    
    def _repair_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 6: Repair failed SQL queries."""
        original_sql = state["sql_query"]
        error = state["execution_error"]
        schema = self.sqlite_tool.get_schema()
        
        # Increment repair attempts
        repair_attempts = state.get("repair_attempts", 0) + 1
        
        if repair_attempts > state.get("max_repair_attempts", 3):
            return {
                **state,
                "sql_query": None,
                "repair_attempts": repair_attempts,
                "repair_failed": True
            }
        
        # Use DSPy to repair the query
        prediction = self.nl_to_sql(
            query=state["processed_query"],
            schema=schema,
            context=f"Previous query failed: {original_sql}\nError: {error}",
            repair_mode=True
        )
        
        return {
            **state,
            "sql_query": prediction.sql_query,
            "repair_attempts": repair_attempts,
            "repair_reasoning": prediction.reasoning
        }
    
    def _synthesize_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 7: Synthesize final response using DSPy."""
        query = state["original_query"]
        sql_result = state["sql_result"]
        context = state.get("context", [])
        
        # Use DSPy to synthesize response
        prediction = self.synthesis(
            query=query,
            sql_result=str(sql_result),
            context="\n".join(context)
        )
        
        return {
            **state,
            "final_response": prediction.response,
            "synthesis_reasoning": prediction.reasoning
        }
    
    def _validate_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 8: Simple validation and confidence scoring."""
        response = state.get("final_response", "")
        sql_result = state.get("sql_result", [])
        execution_success = state.get("execution_success", False)
        
        # Simple validation logic
        is_valid = len(response.strip()) > 0
        
        # Calculate confidence based on execution success and results
        confidence = 0.1  # Default low confidence
        if is_valid and execution_success:
            if sql_result and len(sql_result) > 0:
                confidence = 0.8  # High confidence - got results
            else:
                confidence = 0.5  # Medium confidence - executed but no results
        elif is_valid:
            confidence = 0.3  # Low-medium confidence - response but no SQL success
        
        return {
            **state,
            "is_valid": is_valid,
            "confidence": confidence,
            "validated_response": response if is_valid else "I apologize, but I couldn't generate a proper response."
        }
    
    def _route_decision(self, state: Dict[str, Any]) -> str:
        """Conditional routing logic."""
        return state.get("route_type", "hybrid")
    
    def _execution_decision(self, state: Dict[str, Any]) -> str:
        """Decide whether SQL execution was successful or needs repair."""
        if state.get("execution_success", False):
            return "success"
        elif state.get("repair_attempts", 0) < state.get("max_repair_attempts", 3):
            return "repair"
        else:
            return "success"  # Give up and synthesize with error info
    
    def run(self, query: str) -> Dict[str, Any]:
        """Run the hybrid agent on a query."""
        initial_state = {"query": query}
        final_state = self.graph.invoke(initial_state)
        return final_state


def create_agent(db_path: str, docs_path: str) -> RetailAnalyticsAgent:
    """Factory function to create a retail analytics agent."""
    return RetailAnalyticsAgent(db_path, docs_path)
