import sqlite3


conn = sqlite3.connect('mydatabase.db')
cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments (id)
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments (id)
)
''')


cursor.execute('''
INSERT INTO departments (name)
VALUES
    ('Engineering'),
    ('Marketing'),
    ('Product Development')
''')


cursor.execute('''
INSERT INTO employees (name, position, department_id)
VALUES
    ('John Doe', 'Software Engineer', 1),
    ('Jane Smith', 'Data Scientist', 1),
    ('Emily Johnson', 'Product Manager', 3),
    ('Michael Brown', 'Marketing Specialist', 2),
    ('Linda Davis', 'Product Designer', 3)
''')


cursor.execute('''
INSERT INTO projects (name, department_id)
VALUES
    ('Project Alpha', 1),
    ('Project Beta', 2),
    ('Project Gamma', 3),
    ('Project Delta', 1),
    ('Project Epsilon', 3)
''')


conn.commit()
conn.close()

print("Tables 'employees', 'departments', and 'projects' created and data inserted.")
