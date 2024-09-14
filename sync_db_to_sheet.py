import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import schedule
import time


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credential.json', scope)
client = gspread.authorize(creds)
spreadsheet_id = '19EW46Fb2En1AaYA5gXiBYzfWc5dBt2BBmvJrqyuxk1o'
sheet = client.open_by_key(spreadsheet_id).sheet1


DATABASE = 'mydatabase.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def update_database_from_sheet():
    try:
        data = sheet.get_all_values()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL
        )
        ''')


        cursor.execute('DELETE FROM employees')


        for row in data[1:]:  
            cursor.execute('INSERT INTO employees (id, name, position) VALUES (?, ?, ?)', (row[0], row[1], row[2]))


        conn.commit()
        conn.close()

        print('Database updated from Google Sheet successfully.')
    except Exception as e:
        print(f'Error updating database from Google Sheet: {e}')

def update_sheet_from_database():
    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM employees')
        rows = cursor.fetchall()


        data = [['ID', 'Name', 'Position']]  
        for row in rows:
            data.append(list(row))


        sheet.update('A1', data)

        conn.close()

        print('Google Sheet updated from database successfully.')
    except Exception as e:
        print(f'Error updating Google Sheet from database: {e}')

def sync():
    update_sheet_from_database()
    update_database_from_sheet()


schedule.every(10).minutes.do(sync) 

if __name__ == "__main__":
    print("Starting synchronization...")
    while True:
        schedule.run_pending()
        time.sleep(1)
