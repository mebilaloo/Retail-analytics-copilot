import sqlite3

print("🔍 SCHEMA MISMATCH ANALYSIS")
print("=" * 50)

# Connect to database
conn = sqlite3.connect('data/northwind.sqlite')
cursor = conn.cursor()

# Get actual tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
actual_tables = sorted([row[0] for row in cursor.fetchall()])

print("📊 ACTUAL Northwind Tables:")
for table in actual_tables:
    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
    count = cursor.fetchone()[0]
    print(f"   • {table}: {count} records")

print("\n❌ WHAT YOUR AGENT GENERATED (Wrong):")
wrong_queries = [
    "SELECT category, SUM(quantity) FROM sales_data",  # sales_data doesn't exist
    "SELECT product, SUM(...) FROM Orders",  # Orders doesn't have product info 
    "SELECT TotalRevenue FROM beverages",  # beverages table doesn't exist
]

for query in wrong_queries:
    print(f"   • {query}")

print("\n✅ WHAT IT SHOULD GENERATE (Correct):")

# Test a correct query
correct_query = """
SELECT p.ProductName, 
       ROUND(SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)), 2) as revenue
FROM Products p 
JOIN [Order Details] od ON p.ProductID = od.ProductID 
GROUP BY p.ProductID, p.ProductName 
ORDER BY revenue DESC 
LIMIT 3
"""

print("   • Top 3 products by revenue:")
try:
    cursor.execute(correct_query)
    results = cursor.fetchall()
    for row in results:
        print(f"     - {row[0]}: ${row[1]}")
except Exception as e:
    print(f"     Error: {e}")

conn.close()

print("\n🎯 CONCLUSION:")
print("✅ Your agent IS working - it generates real SQL")
print("✅ Database has real data") 
print("❌ LLM doesn't know correct Northwind schema")
print("💡 Solution: Fix schema information in DSPy prompts")
