import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import schedule
import time
import datetime

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credential.json', scope)
client = gspread.authorize(creds)
spreadsheet_id = '19EW46Fb2En1AaYA5gXiBYzfWc5dBt2BBmvJrqyuxk1o'
sheet = {
    'employees': client.open_by_key(spreadsheet_id).worksheet('Employees'),
    'departments': client.open_by_key(spreadsheet_id).worksheet('Departments'),
    'projects': client.open_by_key(spreadsheet_id).worksheet('Projects')
}

DATABASE = 'mydatabase.db'
TIMESTAMP_FILE = 'timestamp.txt'

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
        last_sync_time = get_last_sync_time(sheet_name)
        last_modified = get_sheet_last_modified(sheet_name)
        
        if last_modified and (not last_sync_time or last_modified > datetime.datetime.fromisoformat(last_sync_time)):
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            sheet_data = sheet[sheet_name].get_all_values()
            if not sheet_data:
                print(f'No data found in sheet: {sheet_name}')
                conn.close()
                return

            header = sheet_data[0]
            data = sheet_data[1:]

            cursor.execute(f'DELETE FROM {table_name}')
            for row in data:
                placeholders = ', '.join(['?'] * len(columns))
                query = f'INSERT OR REPLACE INTO {table_name} ({", ".join(columns)}) VALUES ({placeholders})'
                cursor.execute(query, row)
                print(f"Inserted row: {row}")

            conn.commit()
            conn.close()
            set_last_sync_time(sheet_name, last_modified.isoformat())
            print(f'{table_name} table updated from Google Sheet ({sheet_name}) successfully.')
        else:
            print(f'No changes detected in Google Sheet ({sheet_name}).')
    except Exception as e:
        print(f'Error updating {table_name} table from Google Sheet ({sheet_name}): {e}')

def sync_db_to_sheet():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, position, department_id FROM employees')
        employees_data = cursor.fetchall()
        employees_data = [['ID', 'Name', 'Position', 'DepartmentID']] + [list(row) for row in employees_data]
        sheet['employees'].clear()
        sheet['employees'].update('A1', employees_data)

        cursor.execute('SELECT id, name FROM departments')
        departments_data = cursor.fetchall()
        departments_data = [['ID', 'Name']] + [list(row) for row in departments_data]
        sheet['departments'].clear()
        sheet['departments'].update('A1', departments_data)

        cursor.execute('SELECT id, name, department_id FROM projects')
        projects_data = cursor.fetchall()
        projects_data = [['ID', 'Name', 'DepartmentID']] + [list(row) for row in projects_data]
        sheet['projects'].clear()
        sheet['projects'].update('A1', projects_data)

        conn.close()

        print('Google Sheets updated from database successfully.')
    except Exception as e:
        print(f'Error updating Google Sheets from database: {e}')

def check_for_updates():
    sheet_to_table = {
        'employees': ('employees', ['id', 'name', 'position', 'department_id']),
        'departments': ('departments', ['id', 'name']),
        'projects': ('projects', ['id', 'name', 'department_id'])
    }

    for sheet_name in sheet.keys():
        table_name, columns = sheet_to_table.get(sheet_name, (None, []))

        print(f"Processing {sheet_name}: table_name={table_name}, columns={columns}")

        if table_name and columns:
            sync_sheet_to_db(sheet_name, table_name, columns)
        else:
            print(f"Invalid sheet name: {sheet_name}")

schedule.every(1).minute.do(check_for_updates)

if __name__ == "__main__":
    print("Starting synchronization...")
    while True:
        schedule.run_pending()
        time.sleep(1)
