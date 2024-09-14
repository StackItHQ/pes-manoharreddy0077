import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credential.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key('19EW46Fb2En1AaYA5gXiBYzfWc5dBt2BBmvJrqyuxk1o').sheet1

def sync_sheet_to_db():
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    

    data = sheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    cursor.execute('DELETE FROM employees')


    for row in rows:
        cursor.execute('INSERT INTO employees (ID, Name, Position) VALUES (?, ?, ?)', row)

    conn.commit()
    conn.close()

def sync_db_to_sheet():
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()


    cursor.execute('SELECT * FROM employees')
    rows = cursor.fetchall()


    data = [['ID', 'Name', 'Position']]  
    data.extend(rows)


    sheet.update('A1', data)

    conn.close()
