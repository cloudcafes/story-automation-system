"""
Google Drive Manager - Pure Google Drive Operations
Handles all file I/O with Google Drive - No local file storage
"""

import os
import logging
import time
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import tempfile
import ssl
import urllib3

# Disable SSL verification at the beginning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

from config import (
    GOOGLE_DRIVE_ROOT_FOLDER_ID,
    DRIVE_FOLDER_STRUCTURE,
    FRAMEWORK_FILES,
    INPUT_OUTPUT_FILES,
    SYSTEM_SETTINGS,
    GOOGLE_DRIVE_SCOPES,
    CREDENTIALS_FILE_PATH,
    MIME_TYPE_FOLDER,
    MIME_TYPE_TEXT,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES
)

class GoogleDriveManager:
    """Manages all Google Drive operations for the story automation system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.folder_cache = {}  # Cache folder IDs for performance
        self.initialize_service()
    
    def initialize_service(self):
        """Initialize Google Drive service with service account"""
        try:
            self.logger.info(" Initializing Google Drive service...")
            
            if not os.path.exists(CREDENTIALS_FILE_PATH):
                raise FileNotFoundError(ERROR_MESSAGES['missing_credentials'])
            
            # Create credentials from service account file
            credentials = service_account.Credentials.from_service_account_file(
                CREDENTIALS_FILE_PATH, 
                scopes=GOOGLE_DRIVE_SCOPES
            )
            
            # Build the Drive service
            self.service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
            
            # Test connection
            self._test_connection()
            self.logger.info(SUCCESS_MESSAGES['drive_connected'])
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Google Drive: {e}")
            raise
    
    def _test_connection(self):
        """Test Google Drive connection by listing root folder"""
        try:
            results = self.service.files().list(
                q=f"'{GOOGLE_DRIVE_ROOT_FOLDER_ID}' in parents and trashed=false",
                pageSize=1,
                fields="files(id, name)"
            ).execute()
            return True
        except Exception as e:
            raise ConnectionError(f"Google Drive connection test failed: {e}")
    
    def _retry_api_call(self, api_call, *args, **kwargs):
        """Retry API call with exponential backoff"""
        for attempt in range(SYSTEM_SETTINGS['max_retries']):
            try:
                return api_call(*args, **kwargs)
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504] and attempt < SYSTEM_SETTINGS['max_retries'] - 1:
                    wait_time = SYSTEM_SETTINGS['retry_delay'] * (2 ** attempt)
                    self.logger.warning(f" API call failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            except Exception as e:
                self.logger.error(f"❌ Unexpected error in API call: {e}")
                raise
    
    def _get_folder_id(self, folder_path, parent_folder_id=None):
        """Get or create folder ID for a given path"""
        if folder_path in self.folder_cache:
            return self.folder_cache[folder_path]
        
        if not folder_path or folder_path == '':
            return GOOGLE_DRIVE_ROOT_FOLDER_ID
        
        try:
            # Split path and navigate/create folders recursively
            parts = folder_path.split('/')
            current_folder_id = parent_folder_id or GOOGLE_DRIVE_ROOT_FOLDER_ID
            
            for part in parts:
                if not part:  # Skip empty parts
                    continue
                    
                # Check if folder exists
                query = f"name='{part}' and mimeType='{MIME_TYPE_FOLDER}' and '{current_folder_id}' in parents and trashed=false"
                results = self._retry_api_call(
                    self.service.files().list,
                    q=query,
                    spaces='drive',
                    fields='files(id, name)'
                ).execute()
                
                folders = results.get('files', [])
                
                if folders:
                    current_folder_id = folders[0]['id']
                else:
                    # Create folder
                    folder_metadata = {
                        'name': part,
                        'mimeType': MIME_TYPE_FOLDER,
                        'parents': [current_folder_id]
                    }
                    folder = self._retry_api_call(
                        self.service.files().create,
                        body=folder_metadata,
                        fields='id'
                    ).execute()
                    current_folder_id = folder['id']
                    self.logger.info(f" Created folder: {part}")
            
            self.folder_cache[folder_path] = current_folder_id
            return current_folder_id
            
        except Exception as e:
            self.logger.error(f"❌ Error getting folder ID for {folder_path}: {e}")
            raise
    
    def _get_file_id(self, file_name, folder_id):
        """Get file ID by name and parent folder"""
        try:
            query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
            results = self._retry_api_call(
                self.service.files().list,
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            return files[0]['id'] if files else None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting file ID for {file_name}: {e}")
            return None
    
    def read_framework_file(self, file_key):
        """Read a framework file from Google Drive"""
        try:
            if file_key not in FRAMEWORK_FILES:
                raise ValueError(f"Unknown framework file key: {file_key}")
            
            file_path = FRAMEWORK_FILES[file_key]
            folder_path = '/'.join(file_path.split('/')[:-1])  # Get folder path
            file_name = file_path.split('/')[-1]  # Get file name
            
            folder_id = self._get_folder_id(folder_path)
            file_id = self._get_file_id(file_name, folder_id)
            
            if not file_id:
                raise FileNotFoundError(f"Framework file not found: {file_path}")
            
            return self._download_file_content(file_id)
            
        except Exception as e:
            self.logger.error(f"❌ Error reading framework file {file_key}: {e}")
            raise
    
    def read_story_input(self):
        """Read story input file from root of Google Drive"""
        try:
            file_name = INPUT_OUTPUT_FILES['story_input']
            file_id = self._get_file_id(file_name, GOOGLE_DRIVE_ROOT_FOLDER_ID)
            
            if not file_id:
                raise FileNotFoundError(f"Story input file not found: {file_name}")
            
            content = self._download_file_content(file_id)
            
            if not content or len(content.strip()) < 100:
                raise ValueError("Story input is too short or empty (minimum 100 characters required)")
            
            self.logger.info(f" Read story input ({len(content)} characters)")
            return content
            
        except Exception as e:
            self.logger.error(f"❌ Error reading story input: {e}")
            raise
    
    def _download_file_content(self, file_id):
        """Download file content as string"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return file_content.getvalue().decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"❌ Error downloading file content {file_id}: {e}")
            raise
    
    def create_output_folder(self, folder_name):
        """Create output folder in Google Drive"""
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': MIME_TYPE_FOLDER,
                'parents': [GOOGLE_DRIVE_ROOT_FOLDER_ID]
            }
            
            folder = self._retry_api_call(
                self.service.files().create,
                body=folder_metadata,
                fields='id'
            ).execute()
            
            self.logger.info(f" Created output folder: {folder_name}")
            return folder['id']
            
        except Exception as e:
            self.logger.error(f"❌ Error creating output folder {folder_name}: {e}")
            raise
    
    def write_output_file(self, content, file_name, folder_id):
        """Write content to a file in Google Drive"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Upload to Google Drive
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]
                }
                
                media = MediaFileUpload(temp_file_path, mimetype=MIME_TYPE_TEXT)
                file = self._retry_api_call(
                    self.service.files().create,
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                self.logger.info(f" Written output file: {file_name}")
                return file['id']
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            self.logger.error(f"❌ Error writing output file {file_name}: {e}")
            return None
    
    def validate_framework_files(self):
        """Validate that all required framework files exist"""
        try:
            self.logger.info(" Validating framework files...")
            missing_files = []
            
            for file_key, file_path in FRAMEWORK_FILES.items():
                try:
                    folder_path = '/'.join(file_path.split('/')[:-1])
                    file_name = file_path.split('/')[-1]
                    
                    folder_id = self._get_folder_id(folder_path)
                    file_id = self._get_file_id(file_name, folder_id)
                    
                    if not file_id:
                        missing_files.append(file_path)
                    else:
                        # Test reading the file
                        content = self._download_file_content(file_id)
                        if not content:
                            missing_files.append(file_path)
                            
                except Exception:
                    missing_files.append(file_path)
            
            if missing_files:
                raise FileNotFoundError(
                    f"Missing or empty framework files: {', '.join(missing_files)}"
                )
            
            self.logger.info("✅ All framework files validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Framework validation failed: {e}")
            raise
    
    def get_folder_structure(self):
        """Get the complete folder structure for debugging"""
        try:
            structure = {
                'root_folder_id': GOOGLE_DRIVE_ROOT_FOLDER_ID,
                'framework_files': {},
                'story_input_exists': False
            }
            
            # Check framework files
            for file_key, file_path in FRAMEWORK_FILES.items():
                folder_path = '/'.join(file_path.split('/')[:-1])
                file_name = file_path.split('/')[-1]
                
                folder_id = self._get_folder_id(folder_path)
                file_id = self._get_file_id(file_name, folder_id)
                
                structure['framework_files'][file_key] = {
                    'path': file_path,
                    'folder_id': folder_id,
                    'file_id': file_id,
                    'exists': file_id is not None
                }
            
            # Check story input
            story_file_id = self._get_file_id(
                INPUT_OUTPUT_FILES['story_input'], 
                GOOGLE_DRIVE_ROOT_FOLDER_ID
            )
            structure['story_input_exists'] = story_file_id is not None
            
            return structure
            
        except Exception as e:
            self.logger.error(f"❌ Error getting folder structure: {e}")
            return {}


# Global instance for easy access
_drive_manager_instance = None

def get_drive_manager():
    """Get or create global Google Drive manager instance"""
    global _drive_manager_instance
    if _drive_manager_instance is None:
        _drive_manager_instance = GoogleDriveManager()
    return _drive_manager_instance


if __name__ == "__main__":
    # Test the drive manager
    logging.basicConfig(level=logging.INFO)
    manager = GoogleDriveManager()
    
    try:
        structure = manager.get_folder_structure()
        print("✅ Google Drive Manager test completed successfully")
        print(f" Root folder ID: {structure['root_folder_id']}")
        print(f" Story input exists: {structure['story_input_exists']}")
        
        framework_status = {k: v['exists'] for k, v in structure['framework_files'].items()}
        print(f" Framework files: {framework_status}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")