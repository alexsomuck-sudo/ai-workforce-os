import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required for uploading videos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    print("============================================================")
    print("YouTube API Authentication Setup")
    print("============================================================")
    print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
    print("2. Create a project and enable 'YouTube Data API v3'")
    print("3. Create OAuth 2.0 Client ID (Desktop app)")
    print("4. Download the JSON file and rename it to 'youtube_credentials.json'")
    print("5. Place 'youtube_credentials.json' in this directory")
    print("============================================================")
    
    if not os.path.exists("youtube_credentials.json"):
        print("Error: 'youtube_credentials.json' not found.")
        return

    flow = InstalledAppFlow.from_client_secrets_file("youtube_credentials.json", SCOPES)
    # Using local server flow for authentication
    creds = flow.run_local_server(port=0, open_browser=False)
    
    # Save the credentials for the next run
    with open("youtube_token.json", "w") as token:
        token.write(creds.to_json())
    
    print("\n✓ Authentication successful! 'youtube_token.json' has been created.")
    print("You can now enable YOUTUBE_ENABLED=true in your .env file.")

if __name__ == "__main__":
    main()
