import gspread
from oauth2client.service_account import ServiceAccountCredentials
from queue import Queue
from portfolio_listener import PortfolioListener
import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# --- Load environment ---
load_dotenv()
GOOGLE_SHEETS_KEY = os.getenv("GOOGLE_SHEETS_KEY", "service_account.json")

# --- Google Sheets setup ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_KEY, scope)
client = gspread.authorize(creds)

# Open spreadsheet "AVAX-MM", worksheet "Delta Details"
spreadsheet = client.open("AVAX-MM")
sheet = spreadsheet.worksheet("Delta Details")

# --- Start listener ---
q = Queue(maxsize=1)
listener = PortfolioListener(queue=q)
listener.start()

try:
    while True:
        df = q.get()  # blocks until next snapshot arrives

        # Flatten DataFrame to rows
        rows = [df.reset_index().columns.values.tolist()] + df.reset_index().values.tolist()

        # Write starting at cell K46
        sheet.update(range_name="K46", values=rows)

        sheet.update(range_name="J44",
                    values=[[f"Last Published: {df.attrs.get('last_published')}"]])

        # Also write PV somewhere if you want (example: J45)
        sheet.update(range_name="J45",
                    values=[[f"Portfolio PV: {df.attrs.get('portfolio_value')}"]])


except KeyboardInterrupt:
    listener.stop()
    listener.join()
