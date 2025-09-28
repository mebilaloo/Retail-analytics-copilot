"""
DSPy Signatures for the Retail Analytics Agent.
Defines the input/output signatures for Router, NL→SQL, and Synthesis modules.
"""

import dspy
from typing import List, Optional


class RouterSignature(dspy.Signature):
    """DSPy signature for routing queries to appropriate processing paths."""
    
    query: str = dspy.InputField(desc="The user's natural language query")
    
    route_type: str = dspy.OutputField(
        desc="The routing decision: 'sql' for pure SQL queries, 'rag' for document retrieval, or 'hybrid' for both",
        choices=["sql", "rag", "hybrid"]
    )
    reasoning: str = dspy.OutputField(desc="Explanation of why this routing decision was made")


class NLToSQLSignature(dspy.Signature):
    """DSPy signature for converting natural language to SQL queries."""
    
    query: str = dspy.InputField(desc="The user's natural language query")
    schema: str = dspy.InputField(desc="The database schema information")
    context: str = dspy.InputField(desc="Additional context from RAG retrieval or repair information")
    repair_mode: Optional[bool] = dspy.InputField(desc="Whether this is a repair attempt", default=False)
    
    sql_query: str = dspy.OutputField(desc="The generated SQL query")
    reasoning: str = dspy.OutputField(desc="Explanation of the SQL query generation process")


class SynthesisSignature(dspy.Signature):
    """DSPy signature for synthesizing final responses."""
    
    query: str = dspy.InputField(desc="The original user query")
    sql_result: str = dspy.InputField(desc="The result from SQL query execution")
    context: str = dspy.InputField(desc="Additional context from RAG retrieval")
    format_hint: Optional[str] = dspy.InputField(desc="Expected output format (number, string, list, etc.)", default="")
    
    response: str = dspy.OutputField(desc="The final natural language response to the user")
    reasoning: str = dspy.OutputField(desc="Explanation of how the response was constructed")


class ValidationSignature(dspy.Signature):
    """DSPy signature for validating generated responses."""
    
    query: str = dspy.InputField(desc="The original user query")
    response: str = dspy.InputField(desc="The generated response")
    sql_result: str = dspy.InputField(desc="The SQL execution result")
    
    is_valid: bool = dspy.OutputField(desc="Whether the response adequately answers the query")
    confidence: float = dspy.OutputField(desc="Confidence score between 0.0 and 1.0")
    feedback: str = dspy.OutputField(desc="Specific feedback on response quality")


class EntityExtractionSignature(dspy.Signature):
    """DSPy signature for extracting key entities from queries."""
    
    query: str = dspy.InputField(desc="The user's natural language query")
    
    entities: List[str] = dspy.OutputField(desc="List of key entities mentioned in the query")
    entity_types: List[str] = dspy.OutputField(desc="Types of entities (product, customer, date, metric, etc.)")
    intent: str = dspy.OutputField(desc="The primary intent of the query (analysis, comparison, trend, etc.)")


class SQLValidationSignature(dspy.Signature):
    """DSPy signature for validating SQL queries before execution."""
    
    sql_query: str = dspy.InputField(desc="The generated SQL query")
    schema: str = dspy.InputField(desc="The database schema information")
    
    is_valid: bool = dspy.OutputField(desc="Whether the SQL query is syntactically and semantically valid")
    issues: List[str] = dspy.OutputField(desc="List of potential issues or errors in the query")
    suggestions: List[str] = dspy.OutputField(desc="Suggestions for improving the query")


class RetailMetricsSignature(dspy.Signature):
    """DSPy signature for calculating retail-specific metrics."""
    
    query: str = dspy.InputField(desc="The user's query about retail metrics")
    data: str = dspy.InputField(desc="The raw data from SQL execution")
    
    metrics: List[str] = dspy.OutputField(desc="List of calculated retail metrics")
    interpretations: List[str] = dspy.OutputField(desc="Business interpretations of the metrics")
    recommendations: List[str] = dspy.OutputField(desc="Actionable recommendations based on the analysis")


# Example usage and configuration
def configure_dspy_modules(model_name: str = "qwen2.5:0.5b", base_url: str = "http://localhost:11434/v1"):
    """Configure DSPy with local Ollama model."""
    import os
    try:
        lm = dspy.LM(
            model=f"openai/{model_name}",
            api_base=base_url,
            api_key="ollama",  # Ollama doesn't require real key
            max_tokens=1000
        )
        dspy.settings.configure(lm=lm)
        return lm
    except Exception as e:
        print(f"Warning: DSPy configuration failed: {e}")
        print("Continuing with fallback logic...")
        return None


# Prompt templates for better performance
ROUTER_PROMPT = """
You are a query router for a retail analytics system. Analyze the user's query and determine the best processing path:

- 'sql': For queries that can be answered with database queries alone (sales numbers, inventory counts, etc.)
- 'rag': For queries requiring domain knowledge from documentation (policies, definitions, procedures)
- 'hybrid': For queries that need both database analysis and contextual information

Consider the complexity and requirements of the query to make the best routing decision.
"""

NL_TO_SQL_PROMPT = """
You are an expert SQL developer for the Northwind retail database. Convert natural language queries to SQL using the provided schema.

IMPORTANT NORTHWIND TABLE NAMES:
- Categories (CategoryID, CategoryName) - Product categories like 'Beverages', 'Condiments'
- Products (ProductID, ProductName, UnitPrice, UnitsInStock, CategoryID) - Individual products  
- Customers (CustomerID, CompanyName, Country) - Customer information
- Orders (OrderID, CustomerID, OrderDate) - Order headers
- [Order Details] (OrderID, ProductID, UnitPrice, Quantity, Discount) - Order line items (NOTE: Use brackets!)

COMMON QUERY PATTERNS:
- Product revenue: SELECT p.ProductName, SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) FROM Products p JOIN [Order Details] od ON p.ProductID = od.ProductID
- Category analysis: SELECT c.CategoryName, COUNT(*) FROM Categories c JOIN Products p ON c.CategoryID = p.CategoryID  
- Customer orders: SELECT c.CompanyName, COUNT(*) FROM Customers c JOIN Orders o ON c.CustomerID = o.CustomerID
- Geographic analysis: Use c.Country from Customers table

CRITICAL RULES:
1. NEVER use tables like 'sales_data', 'beverages' - they don't exist!
2. Always use [Order Details] with brackets for order line items
3. Revenue = UnitPrice * Quantity * (1 - Discount)
4. Use proper JOINs - Orders table doesn't contain product info directly
5. CategoryName values: 'Beverages', 'Condiments', 'Dairy Products', etc.

If in repair mode, fix the previous query based on the error information provided.
"""

SYNTHESIS_PROMPT = """
You are a retail analytics expert. Synthesize the SQL results and contextual information into a clear, actionable response for business users.

Guidelines:
- Use business-friendly language, avoid technical jargon
- Provide clear insights and interpretations
- Include relevant numbers and percentages
- Suggest actionable next steps when appropriate
- Structure the response logically (overview, key findings, recommendations)
- Consider retail-specific KPIs and metrics
"""
