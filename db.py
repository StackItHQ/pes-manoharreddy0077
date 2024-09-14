import sqlite3


conn = sqlite3.connect('mydatabase.db')
cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    position TEXT NOT NULL
)
''')

cursor.execute('''
INSERT INTO employees (name, position)
VALUES
    ('John Doe', 'Software Engineer'),
    ('Jane Smith', 'Data Scientist'),
    ('Emily Johnson', 'Product Manager')
''')
cursor.execute('''
INSERT INTO employees (name, position)
VALUES
    ('John Doe1', 'Software Engineer'),
    ('Jane Smith2', 'Data Scientist'),
    ('Emily Johnson3', 'Product Manager')
''')

conn.commit()
conn.close()

print("Table 'employees' created and data inserted.")
