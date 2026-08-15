"""
YouTube Service - Automated video uploading using YouTube Data API v3
"""
import os
import logging
from typing import Any, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from app.core.config import settings

logger = logging.getLogger("ai_workforce.services.youtube")

# Scopes required for uploading videos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeService:
    """Service for interacting with YouTube API."""

    def __init__(self):
        self.credentials_path = os.path.join(os.getcwd(), "youtube_credentials.json")
        self.token_path = os.path.join(os.getcwd(), "youtube_token.json")
        self.youtube = None
        self._is_authenticated = False

    def authenticate(self) -> bool:
        """
        Authenticate with YouTube API.
        Requires youtube_token.json or manual OAuth flow.
        """
        creds = None
        # The file youtube_token.json stores the user's access and refresh tokens
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing YouTube token: {e}")
                    return False
            else:
                logger.warning("YouTube token not found or invalid. Manual authentication required.")
                return False

        try:
            self.youtube = build("youtube", "v3", credentials=creds)
            self._is_authenticated = True
            return True
        except Exception as e:
            logger.error(f"Failed to build YouTube service: {e}")
            return False

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        category_id: str = "22",  # 22 is People & Blogs
        tags: list = None,
        privacy_status: str = "public"
    ) -> Dict[str, Any]:
        """
        Upload a video to YouTube.
        """
        if not self._is_authenticated:
            if not self.authenticate():
                return {"status": "error", "message": "YouTube authentication failed."}

        if not os.path.exists(file_path):
            return {"status": "error", "message": f"Video file not found: {file_path}"}

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or ["AI", "Automation", "Workforce"],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        try:
            media = MediaFileUpload(
                file_path,
                mimetype="video/mp4",
                resumable=True
            )

            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploading YouTube video: {int(status.progress() * 100)}%")

            logger.info(f"YouTube video uploaded successfully: {response.get('id')}")
            return {
                "status": "success",
                "video_id": response.get("id"),
                "url": f"https://www.youtube.com/watch?v={response.get('id')}"
            }

        except Exception as e:
            logger.error(f"YouTube upload error: {e}")
            return {"status": "error", "message": str(e)}

    def get_channel_info(self) -> Dict[str, Any]:
        """Get information about the authenticated channel."""
        if not self._is_authenticated:
            if not self.authenticate():
                return {"status": "error", "message": "YouTube authentication failed."}

        try:
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()
            return {"status": "success", "data": response}
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return {"status": "error", "message": str(e)}
