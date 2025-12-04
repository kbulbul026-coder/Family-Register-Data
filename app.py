from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import gspread
from gspread import exceptions as gspread_exceptions 
import time

# Flask सेटअप
app = Flask(__name__)
CORS(app) 

# Gspread कनेक्शन सेटअप
worksheet = None 

# --- यहाँ ID का उपयोग करें ---
# अपनी Google Sheet ID से इस placeholder को बदलें
SPREADSHEET_ID = "15VB3XxUTBX2OHe7I_Ab15jlY56bcEb5kX5Pk_s3bTuY" 
# -----------------------------

try:
    # 1. Google Sheets API क्रेडेंशियल्स का उपयोग करें
    gc = gspread.service_account(filename='credentials.json') 
    
    # 2. शीर्षक के बजाय ID का उपयोग करके अपनी Google Sheet खोलें
    spreadsheet = gc.open_by_key(SPREADSHEET_ID) 
    
    # 3. पहली वर्कशीट का उपयोग करें
    worksheet = spreadsheet.sheet1 
    
    print(f"Gspread connection successful using ID to '{spreadsheet.title}'.")
    
# Gspread API या अनुमति की त्रुटियों को पकड़ें
except gspread_exceptions.SpreadsheetNotFound:
    print(f"Gspread connection failed: Spreadsheet ID '{SPREADSHEET_ID}' not found.")
    print("FIX: Check the SPREADSHEET_ID in app.py is correct and the Service Account has access.")
except gspread_exceptions.APIError as e:
    error_message = str(e)
    if "403" in error_message or "PERMISSION_DENIED" in error_message:
         print(f"Gspread connection failed: Permission Denied (403).")
         print("FIX: You MUST share the Google Sheet with the Service Account email found in 'credentials.json'.")
    else:
        print(f"Gspread connection failed: API Error ({error_message}).")
except FileNotFoundError:
    print(f"Gspread connection failed: 'credentials.json' file not found.")
except Exception as e:
    print(f"Gspread connection failed: Unknown Error ({e}).")
    
# यदि कनेक्शन विफल होता है, तो उपयोगकर्ता को सूचित करें
if worksheet is None:
    @app.route('/api/members', methods=['GET', 'POST'])
    def api_failed():
        return jsonify({"status": "error", "message": "API initialization failed: Could not connect to Google Sheet."}), 500

# --- रूट: index.html को सर्व करने के लिए ---
@app.route('/')
def index():
    return render_template('index.html')
# ------------------------------------------------

# API routes for CRUD operations
@app.route('/api/members', methods=['GET'])
def get_members():
    """सभी परिवार के सदस्यों के डेटा को वापस करता है।"""
    try:
        # सभी डेटा प्राप्त करें
        data = worksheet.get_all_records()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        print(f"Error fetching data from sheet: {e}")
        return jsonify({"status": "error", "message": f"Could not retrieve data: {e}"}), 500

@app.route('/api/members', methods=['POST'])
def add_member():
    """Google Sheet में एक नया परिवार सदस्य जोड़ता है।"""
    data = request.json
    if not data or 'Name' not in data:
        return jsonify({"status": "error", "message": "Name field is required."}), 400
    
    # सुनिश्चित करें कि सभी अपेक्षित फ़ील्ड मौजूद हैं 
    expected_headers = [
        "Name", "Relationship", "FatherName", "Spouse", "Birthdate",
        "EducationalDetails", "UIDAI_No", "PAN_No", 
        "Cast_Certificate_No", "Residential_Certificate_No"
    ]
    
    # मानों की सूची तैयार करें
    row_data = [data.get(header, '') for header in expected_headers]
    
    try:
        # शीट में डेटा जोड़ें
        worksheet.append_row(row_data)
        time.sleep(0.5) 
        return jsonify({"status": "success", "message": "Member added successfully."})
    except Exception as e:
        print(f"Error appending data to sheet: {e}")
        return jsonify({"status": "error", "message": f"Could not add member: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
