from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from config import get_google_sheet
from sync_script import sync_sheet_to_db, sync_db_to_sheet

app = Flask(__name__)

# Initialize Google Sheets
sheet = get_google_sheet()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/sheet')
def sheet_view():
    data = sheet.get_all_values()
    return render_template('sheet.html', data=data)

@app.route('/db')
def db_view():
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees')
    rows = cursor.fetchall()
    conn.close()
    return render_template('db.html', rows=rows)

@app.route('/sync_sheet_to_db', methods=['POST'])
def sync_sheet_to_db_endpoint():
    try:
        sync_sheet_to_db()
        return jsonify({"message": "Database updated from Google Sheet successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sync_db_to_sheet', methods=['POST'])
def sync_db_to_sheet_endpoint():
    try:
        sync_db_to_sheet()
        return jsonify({"message": "Google Sheet updated from database successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/edit_db', methods=['GET', 'POST'])
def edit_db():
    if request.method == 'POST':
        id = request.form.get('id')
        name = request.form.get('name')
        position = request.form.get('position')
        action = request.form.get('action')

        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()

        if action == 'add':
            cursor.execute('INSERT INTO employees (ID, Name, Position) VALUES (?, ?, ?)', (id, name, position))
        elif action == 'update':
            cursor.execute('UPDATE employees SET Name=?, Position=? WHERE ID=?', (name, position, id))
        elif action == 'delete':
            cursor.execute('DELETE FROM employees WHERE ID=?', (id,))

        conn.commit()
        conn.close()
        return redirect(url_for('db_view'))

    return render_template('edit_db.html')

if __name__ == '__main__':
    app.run(debug=True)
