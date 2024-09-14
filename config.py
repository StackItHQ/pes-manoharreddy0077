import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credential.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key('19EW46Fb2En1AaYA5gXiBYzfWc5dBt2BBmvJrqyuxk1o').sheet1
    return sheet
