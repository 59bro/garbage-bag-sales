import sqlite3

conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE product_specs (id INTEGER PRIMARY KEY, spec_name TEXT)')
conn.execute('CREATE TABLE inventory_transactions (id INTEGER PRIMARY KEY, spec_id INTEGER, transaction_date TEXT, transaction_type TEXT, quantity INTEGER)')
conn.execute('INSERT INTO product_specs VALUES (1, "Item A")')
conn.execute('INSERT INTO inventory_transactions VALUES (1, 1, "2026-07-21", "초기재고", 16349)')
conn.execute('INSERT INTO inventory_transactions VALUES (2, 1, "2026-07-20", "출고", 100)')
conn.execute('INSERT INTO inventory_transactions VALUES (3, 1, "2026-07-21", "출고", 50)')
conn.commit()

cursor = conn.cursor()
cursor.execute('''
SELECT 
    COALESCE(init.quantity, 0)
    + COALESCE(SUM(CASE WHEN it.transaction_type = '입고' THEN it.quantity ELSE 0 END), 0)
    - COALESCE(SUM(CASE WHEN it.transaction_type = '출고' THEN it.quantity ELSE 0 END), 0)
    AS current_stock
FROM product_specs ps
LEFT JOIN inventory_transactions init 
       ON init.spec_id = ps.id AND init.transaction_type = '초기재고'
LEFT JOIN inventory_transactions it 
       ON it.spec_id = ps.id 
      AND it.transaction_type != '초기재고'
      AND (init.transaction_date IS NULL OR it.transaction_date >= init.transaction_date)
WHERE ps.id = 1
GROUP BY ps.id, init.quantity
''')
print(cursor.fetchall())
