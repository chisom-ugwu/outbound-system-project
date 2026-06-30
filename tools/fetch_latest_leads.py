#!/usr/bin/env python3
"""
tools/fetch_latest_leads.py
Webhook receiver that downloads the latest raw leads CSV from Google Drive,
streams it locally to .tmp/companies.csv, and immediately deletes it from the Drive.
Cleaned for production-level use.
"""

import os
import sys
import json
import io
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

# Ensure local directories exist
os.makedirs(".tmp", exist_ok=True)

load_dotenv()

PORT = int(os.getenv("WEBHOOK_PORT", 8080))
SECRET = os.getenv("WEBHOOK_SECRET", "super_secret_token")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
OUTPUT_PATH = os.path.join(".tmp", "companies.csv")

def handle_drive_file(file_id):
    """
    Downloads file from Google Drive and deletes it.
    Uses service account credentials for authentication.
    """
    print(f"[Fetch Leads] Downloading Drive File ID: {file_id}")
    
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"[Fetch Leads] Error: Credentials file not found at {CREDENTIALS_PATH}")
        return False

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        
        scopes = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )
        service = build('drive', 'v3', credentials=creds)
        
        # Download the file content
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"[Fetch Leads] Download progress: {int(status.progress() * 100)}%")
            
        fh.seek(0)
        with open(OUTPUT_PATH, 'wb') as f:
            f.write(fh.read())
            
        print(f"[Fetch Leads] Streamed downloaded lead file to {OUTPUT_PATH}")
        
        # Delete source cloud file
        service.files().delete(fileId=file_id).execute()
        print(f"[Fetch Leads] Safely deleted file {file_id} from Google Drive")
        return True
        
    except ImportError:
        print("[Fetch Leads] Error: Google API libraries are missing. Please install google-api-python-client.")
        return False
    except Exception as e:
        print(f"[Fetch Leads] Error processing Drive File: {e}")
        return False

class WebhookHTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. Authorize Webhook
        token = self.headers.get("X-Webhook-Token")
        if not token or token != SECRET:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized: Missing or invalid X-Webhook-Token")
            return
            
        # 2. Parse Payload
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Bad Request: Empty Body")
            return
            
        try:
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode('utf-8'))
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Bad Request: Invalid JSON")
            return
            
        file_id = payload.get("file_id")
        if not file_id:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Bad Request: Missing 'file_id' key")
            return
            
        # 3. Process File Download
        success = handle_drive_file(file_id)
        if success:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "file_saved": OUTPUT_PATH}).encode())
        else:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Error downloading files")

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, WebhookHTTPHandler)
    print(f"[Fetch Leads] Starting webhook receiver on port {PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Fetch Leads] Shutting down.")
        httpd.server_close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_arg = sys.argv[1]
        print(f"[Fetch Leads] Manual mode trigger with: {file_arg}")
        handle_drive_file(file_arg)
    else:
        run_server()
