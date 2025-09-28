import sys
sys.path.append('.')
from agent.tools.sqlite_tool import SQLiteTool

print('🗄️ Testing SQL tool...')
tool = SQLiteTool('data/northwind.sqlite')
result = tool.execute_query('SELECT ProductName, UnitPrice FROM Products LIMIT 3')
print('✅ Query executed successfully:')
for row in result:
    print(f'  📦 {row["ProductName"]}: ${row["UnitPrice"]}')
