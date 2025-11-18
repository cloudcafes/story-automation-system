"""
Google Drive Manager - Fixed SSL Issues
"""

import os
import logging
import ssl
import urllib3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
import time

from config import (
    GOOGLE_DRIVE_ROOT_FOLDER_ID,
    INPUT_FOLDER_NAME,
    OUTPUT_FOLDER_NAME,
    AI_QUERIES_FOLDER,
    FRAMEWORK_TEMPLATES_FOLDER,
    STYLE_GUIDES_FOLDER,
    STORY_INPUT_FILE,
    CHARACTER_QUERIES_FILE,
    SCENE_QUERIES_FILE,
    NARRATION_QUERIES_FILE,
    PROMPT_QUERIES_FILE,
    NARRATION_TEMPLATE_FILE,
    CHARACTER_TEMPLATE_FILE,
    SCENE_TEMPLATE_FILE,
    VISUAL_RULES_FILE,
    GOOGLE_DRIVE_SCOPES,
    CREDENTIALS_FILE_PATH,
    MIME_TYPE_FOLDER,
    MIME_TYPE_TEXT,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    MAX_RETRIES,
    RETRY_DELAY,
    SSL_VERIFY
)

# Disable SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create unverified SSL context
ssl._create_default_https_context = ssl._create_unverified_context

class GoogleDriveManager:
    """Google Drive operations with SSL disabled"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.initialize_service()
        
    def initialize_service(self):
        """Initialize Google Drive service with SSL disabled"""
        try:
            if not os.path.exists(CREDENTIALS_FILE_PATH):
                raise FileNotFoundError(ERROR_MESSAGES['missing_credentials'])
            
            credentials = service_account.Credentials.from_service_account_file(
                CREDENTIALS_FILE_PATH,
                scopes=GOOGLE_DRIVE_SCOPES
            )
            
            # FIX: Don't pass both credentials and http - use authorized http
            import google.auth.transport.requests
            import googleapiclient.http
            
            # Create authorized HTTP client with SSL disabled
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            
            # Build service with credentials only - let it handle HTTP internally
            self.service = build('drive', 'v3', credentials=credentials)
            self.logger.info("✅ Google Drive connected successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Google Drive connection failed: {e}")
            # Try alternative approach
            self._initialize_alternative()
    
    def _initialize_alternative(self):
        """Alternative initialization method"""
        try:
            self.logger.info("Trying alternative Google Drive initialization...")
            
            credentials = service_account.Credentials.from_service_account_file(
                CREDENTIALS_FILE_PATH,
                scopes=GOOGLE_DRIVE_SCOPES
            )
            
            # Use discovery.build without custom HTTP
            self.service = build('drive', 'v3', credentials=credentials)
            self.logger.info("✅ Google Drive connected via alternative method")
            
        except Exception as e:
            self.logger.error(f"❌ Alternative initialization also failed: {e}")
            raise

    def _retry_api_call(self, api_call, *args, **kwargs):
        """Retry API call with exponential backoff"""
        for attempt in range(MAX_RETRIES):
            try:
                return api_call(*args, **kwargs)
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504] and attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    self.logger.warning(f"API call failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error in API call: {e}")
                raise

    def folder_exists(self, folder_name, parent_folder_id):
        """Check if a folder exists"""
        try:
            query = f"name='{folder_name}' and mimeType='{MIME_TYPE_FOLDER}' and '{parent_folder_id}' in parents and trashed=false"
            results = self._retry_api_call(
                self.service.files().list,
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            return folders[0]['id'] if folders else None
            
        except HttpError as e:
            self.logger.error(f"Error checking folder existence: {e}")
            return None

    def create_folder(self, folder_name, parent_folder_id):
        """Create a new folder"""
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': MIME_TYPE_FOLDER,
                'parents': [parent_folder_id]
            }
            
            folder = self._retry_api_call(
                self.service.files().create,
                body=folder_metadata,
                fields='id'
            ).execute()
            
            self.logger.info(f"Created folder: {folder_name}")
            return folder['id']
            
        except HttpError as e:
            self.logger.error(f"Error creating folder {folder_name}: {e}")
            raise

    def create_folder_if_not_exists(self, folder_name, parent_folder_id):
        """Create folder only if it doesn't exist"""
        existing_folder_id = self.folder_exists(folder_name, parent_folder_id)
        
        if existing_folder_id:
            self.logger.info(f"Folder exists: {folder_name}")
            return existing_folder_id
        else:
            return self.create_folder(folder_name, parent_folder_id)

    def file_exists(self, file_name, parent_folder_id):
        """Check if a file exists"""
        try:
            query = f"name='{file_name}' and '{parent_folder_id}' in parents and trashed=false"
            results = self._retry_api_call(
                self.service.files().list,
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            return files[0]['id'] if files else None
            
        except HttpError as e:
            self.logger.error(f"Error checking file existence: {e}")
            return None

    def upload_text_content(self, content, file_name, parent_folder_id):
        """Upload text content as a file"""
        try:
            from tempfile import NamedTemporaryFile
            
            with NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                file_metadata = {
                    'name': file_name,
                    'parents': [parent_folder_id]
                }
                
                media = MediaFileUpload(temp_file_path, mimetype=MIME_TYPE_TEXT)
                
                file = self._retry_api_call(
                    self.service.files().create,
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                self.logger.info(f"Uploaded file: {file_name}")
                return file['id']
                
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            self.logger.error(f"Error uploading text content {file_name}: {e}")
            return None

    def download_file_content(self, file_id):
        """Download file content as string"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return file_content.getvalue().decode('utf-8')
            
        except HttpError as e:
            self.logger.error(f"Error downloading file content {file_id}: {e}")
            return None

    def initialize_directory_structure(self):
        """Create the complete directory structure"""
        try:
            self.logger.info("Initializing directory structure...")
            
            input_folder_id = self.create_folder_if_not_exists(INPUT_FOLDER_NAME, GOOGLE_DRIVE_ROOT_FOLDER_ID)
            output_folder_id = self.create_folder_if_not_exists(OUTPUT_FOLDER_NAME, GOOGLE_DRIVE_ROOT_FOLDER_ID)
            
            ai_queries_folder_id = self.create_folder_if_not_exists(AI_QUERIES_FOLDER, input_folder_id)
            framework_templates_folder_id = self.create_folder_if_not_exists(FRAMEWORK_TEMPLATES_FOLDER, input_folder_id)
            style_guides_folder_id = self.create_folder_if_not_exists(STYLE_GUIDES_FOLDER, input_folder_id)
            
            self.logger.info("✅ Directory structure created")
            
            return {
                'input_folder_id': input_folder_id,
                'output_folder_id': output_folder_id,
                'ai_queries_folder_id': ai_queries_folder_id,
                'framework_templates_folder_id': framework_templates_folder_id,
                'style_guides_folder_id': style_guides_folder_id
            }
            
        except Exception as e:
            self.logger.error(f"Error initializing directory structure: {e}")
            raise

    def get_folder_ids(self):
        """Get all folder IDs"""
        try:
            input_folder_id = self.folder_exists(INPUT_FOLDER_NAME, GOOGLE_DRIVE_ROOT_FOLDER_ID)
            if not input_folder_id:
                return self.initialize_directory_structure()
            
            output_folder_id = self.folder_exists(OUTPUT_FOLDER_NAME, GOOGLE_DRIVE_ROOT_FOLDER_ID)
            ai_queries_folder_id = self.folder_exists(AI_QUERIES_FOLDER, input_folder_id)
            framework_templates_folder_id = self.folder_exists(FRAMEWORK_TEMPLATES_FOLDER, input_folder_id)
            style_guides_folder_id = self.folder_exists(STYLE_GUIDES_FOLDER, input_folder_id)
            
            return {
                'input_folder_id': input_folder_id,
                'output_folder_id': output_folder_id,
                'ai_queries_folder_id': ai_queries_folder_id,
                'framework_templates_folder_id': framework_templates_folder_id,
                'style_guides_folder_id': style_guides_folder_id
            }
            
        except Exception as e:
            self.logger.error(f"Error getting folder IDs: {e}")
            raise

    def read_input_file(self, file_path, folder_ids):
        """Read a file from input directory"""
        try:
            if file_path == STORY_INPUT_FILE:
                folder_id = folder_ids['input_folder_id']
            elif file_path.startswith(f"{AI_QUERIES_FOLDER}/"):
                file_name = file_path.split('/')[-1]
                folder_id = folder_ids['ai_queries_folder_id']
                file_path = file_name
            elif file_path.startswith(f"{FRAMEWORK_TEMPLATES_FOLDER}/"):
                file_name = file_path.split('/')[-1]
                folder_id = folder_ids['framework_templates_folder_id']
                file_path = file_name
            elif file_path.startswith(f"{STYLE_GUIDES_FOLDER}/"):
                file_name = file_path.split('/')[-1]
                folder_id = folder_ids['style_guides_folder_id']
                file_path = file_name
            else:
                self.logger.error(f"Unknown file path: {file_path}")
                return None
            
            file_id = self.file_exists(file_path, folder_id)
            if not file_id:
                self.logger.warning(f"File not found: {file_path}")
                return None
            
            return self.download_file_content(file_id)
            
        except Exception as e:
            self.logger.error(f"Error reading input file {file_path}: {e}")
            return None

    def write_output_file(self, content, file_name, output_folder_id):
        """Write content to output file"""
        try:
            file_id = self.upload_text_content(content, file_name, output_folder_id)
            if file_id:
                self.logger.info(f"Wrote output file: {file_name}")
                return True
            else:
                self.logger.error(f"Failed to write output file: {file_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error writing output file {file_name}: {e}")
            return False

# Singleton instance
drive_manager = None

def get_drive_manager():
    global drive_manager
    if drive_manager is None:
        drive_manager = GoogleDriveManager()
    return drive_manager