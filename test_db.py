import sqlite3

conn = sqlite3.connect('data/northwind.sqlite')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables:', [t[0] for t in tables])

cursor.execute('SELECT * FROM Products LIMIT 2;')
products = cursor.fetchall()
print('Sample products:', products)

conn.close()
