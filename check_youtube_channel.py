import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.youtube_service import YouTubeService

def main():
    service = YouTubeService()
    if not service.authenticate():
        print("Authentication failed!")
        return
    try:
        # Get channel info
        request = service.youtube.channels().list(
            part="snippet,statistics",
            mine=True
        )
        response = request.execute()
        
        if "items" in response:
            channel = response["items"][0]
            print(f"Connected Channel Name: {channel['snippet']['title']}")
            print(f"Channel ID: {channel['id']}")
            print(f"Custom URL: {channel['snippet'].get('customUrl', 'N/A')}")
            print(f"Subscribers: {channel['statistics']['subscriberCount']}")
        else:
            print("No channel found for this account.")
    except Exception as e:
        print(f"Error fetching channel info: {e}")

if __name__ == "__main__":
    main()
