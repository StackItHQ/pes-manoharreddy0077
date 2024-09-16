from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from config import get_google_sheet
from sync_script import sync_sheet_to_db, sync_db_to_sheet
import datetime

app = Flask(__name__)

# Initialize Google Sheets
sheet = get_google_sheet()

DATABASE = 'mydatabase.db'
TIMESTAMP_FILE = 'timestamp.txt'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/sheet')
def sheet_view():
    # Fetch data from all three sheets
    employees_data = sheet['employees'].get_all_values()
    departments_data = sheet['departments'].get_all_values()
    projects_data = sheet['projects'].get_all_values()
    
    # Pass the data to the template
    return render_template('sheet.html', employees=employees_data, departments=departments_data, projects=projects_data)

@app.route('/db')
def db_view():
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM employees')
    employees = cursor.fetchall()
    
    cursor.execute('SELECT * FROM departments')
    departments = cursor.fetchall()
    
    cursor.execute('SELECT * FROM projects')
    projects = cursor.fetchall()
    
    conn.close()
    return render_template('db.html', employees=employees, departments=departments, projects=projects)

def get_last_sync_time(sheet_name):
    try:
        with open(f"{sheet_name}_{TIMESTAMP_FILE}", 'r') as file:
            last_sync_time = file.read().strip()
        return last_sync_time
    except FileNotFoundError:
        return None

def set_last_sync_time(sheet_name, timestamp):
    with open(f"{sheet_name}_{TIMESTAMP_FILE}", 'w') as file:
        file.write(str(timestamp))

def get_sheet_last_modified(sheet_name):
    try:
        sheet_metadata = sheet[sheet_name].fetch_sheet_metadata()
        last_modified = sheet_metadata['properties']['modifiedTime']
        return datetime.datetime.fromisoformat(last_modified[:-1])
    except Exception as e:
        print(f'Error fetching sheet metadata for {sheet_name}: {e}')
        return None

def sync_sheet_to_db(sheet_name, table_name, columns):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Fetch data from Google Sheets
        sheet_data = sheet[sheet_name].get_all_values()
        if not sheet_data:
            print(f'No data found in sheet: {sheet_name}')
            conn.close()
            return

        header = sheet_data[0]  # Header row
        data = sheet_data[1:]  # Data rows

        # Print fetched data
        print(f"Data from sheet {sheet_name}: {data}")

        # Clear the existing table data
        cursor.execute(f'DELETE FROM {table_name}')
        print(f"Cleared existing data in {table_name} table.")

        # Insert new data into the database
        for row in data:
            placeholders = ', '.join(['?'] * len(columns))
            query = f'INSERT OR REPLACE INTO {table_name} ({", ".join(columns)}) VALUES ({placeholders})'
            cursor.execute(query, row)
            print(f"Inserted row into {table_name}: {row}")

        conn.commit()
        conn.close()

        # Print last sync time and modified time
        last_sync_time = get_last_sync_time(sheet_name)
        last_modified = get_sheet_last_modified(sheet_name)
        print(f"Last sync time for {sheet_name}: {last_sync_time}")
        print(f"Last modified time for {sheet_name}: {last_modified}")

        set_last_sync_time(sheet_name, last_modified.isoformat())
        print(f'{table_name} table updated from Google Sheet ({sheet_name}) successfully.')
    except Exception as e:
        print(f'Error updating {table_name} table from Google Sheet ({sheet_name}): {e}')


@app.route('/sync_sheet_to_db', methods=['POST'])
def sync_sheet_to_db_route():
    try:
        # Define mappings for sheet names to table names and columns
        sheet_to_table = {
            'employees': ('employees', ['id', 'name', 'position', 'department_id']),
            'departments': ('departments', ['id', 'name']),
            'projects': ('projects', ['id', 'name', 'department_id'])
        }

        for sheet_name in sheet.keys():
            table_name, columns = sheet_to_table.get(sheet_name, (None, []))
            if table_name and columns:
                print(f"Triggering sync for sheet: {sheet_name} -> table: {table_name}")
                sync_sheet_to_db(sheet_name, table_name, columns)
            else:
                print(f"Invalid sheet name: {sheet_name}")

        return jsonify({"message": "Sheets synchronized to database successfully."})
    except Exception as e:
        return jsonify({"error": str(e)})


    
@app.route('/sync_db_to_sheet', methods=['POST'])
def sync_db_to_sheet_endpoint():
    try:
        sync_db_to_sheet()
        return jsonify({"message": "Google Sheet updated from database successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/edit_db', methods=['GET', 'POST'])
def edit_db():
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        table = request.form.get('table')
        action = request.form.get('action')
        id = request.form.get('id')
        name = request.form.get('name', '').strip()
        position = request.form.get('position', '').strip()
        department_id = request.form.get('department_id')

        print(f"Editing {table}: action={action}, id={id}, name={name}, position={position}, department_id={department_id}")

        if action == 'add':
            if table == 'employees':
                if not name or not position or not department_id:
                    return "All fields must be filled out for adding an employee."
            elif table == 'departments':
                if not name:
                    return "Name is required for adding a department."
            elif table == 'projects':
                if not name or not department_id:
                    return "Name and Department are required for adding a project."
        
        if table == 'employees':
            if action == 'add':
                if name and position and department_id:
                    cursor.execute('INSERT INTO employees (name, position, department_id) VALUES (?, ?, ?)', (name, position, department_id))
                else:
                    return "All fields are required for adding an employee."
            elif action == 'update' and id:
                if name and position and department_id:
                    cursor.execute('UPDATE employees SET name=?, position=?, department_id=? WHERE id=?', (name, position, department_id, id))
                else:
                    return "All fields are required for updating an employee."
            elif action == 'delete' and id:
                cursor.execute('DELETE FROM employees WHERE id=?', (id,))
        
        elif table == 'departments':
            if action == 'add':
                if name:
                    cursor.execute('INSERT INTO departments (name) VALUES (?)', (name,))
                else:
                    return "Name is required for adding a department."
            elif action == 'update' and id:
                if name:
                    cursor.execute('UPDATE departments SET name=? WHERE id=?', (name, id))
                else:
                    return "Name is required for updating a department."
            elif action == 'delete' and id:
                cursor.execute('DELETE FROM departments WHERE id=?', (id,))
        
        elif table == 'projects':
            if action == 'add':
                if name and department_id:
                    cursor.execute('INSERT INTO projects (name, department_id) VALUES (?, ?)', (name, department_id))
                else:
                    return "Name and Department are required for adding a project."
            elif action == 'update' and id:
                if name and department_id:
                    cursor.execute('UPDATE projects SET name=?, department_id=? WHERE id=?', (name, department_id, id))
                else:
                    return "Name and Department are required for updating a project."
            elif action == 'delete' and id:
                cursor.execute('DELETE FROM projects WHERE id=?', (id,))
        
        conn.commit()
        conn.close()
        return redirect(url_for('db_view'))

    cursor.execute('SELECT * FROM departments')
    departments = cursor.fetchall()
    conn.close()
    
    return render_template('edit_db.html', departments=departments)

if __name__ == '__main__':
    app.run(debug=True)
