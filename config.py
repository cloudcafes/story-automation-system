"""
Google Drive Story Automation - Configuration File
SSL Verification Disabled
"""

import os
from datetime import datetime

# =============================================================================
# SSL CONFIGURATION - DISABLED FOR CORPORATE NETWORKS
# =============================================================================

# Disable SSL verification completely
SSL_VERIFY = False
DEEPSEEK_VERIFY_SSL = False

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================================================================
# DEEPSEEK API CONFIGURATION
# =============================================================================

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-df60b28326444de6859976f6e603fd9c')
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_MAX_TOKENS = 4000
DEEPSEEK_TEMPERATURE = 0.7

# =============================================================================
# GOOGLE DRIVE CONFIGURATION
# =============================================================================

GOOGLE_DRIVE_ROOT_FOLDER_ID = "1vWhSS20YjkFNitEZI14c8C1uEt12puLE"
INPUT_FOLDER_NAME = "(in)"
OUTPUT_FOLDER_NAME = "(out)"

# Subfolder names within input directory
AI_QUERIES_FOLDER = "ai_queries"
FRAMEWORK_TEMPLATES_FOLDER = "framework_templates"
STYLE_GUIDES_FOLDER = "style_guides"

# =============================================================================
# FILE NAMES CONFIGURATION
# =============================================================================

# Input file names
STORY_INPUT_FILE = "story_input.txt"

# AI query file names
CHARACTER_QUERIES_FILE = "character_queries.txt"
SCENE_QUERIES_FILE = "scene_queries.txt"
NARRATION_QUERIES_FILE = "narration_queries.txt"
PROMPT_QUERIES_FILE = "prompt_queries.txt"

# Template file names
NARRATION_TEMPLATE_FILE = "narration_template.txt"
CHARACTER_TEMPLATE_FILE = "character_template.txt"
SCENE_TEMPLATE_FILE = "scene_template.txt"

# Style guide file names
VISUAL_RULES_FILE = "visual_rules.txt"

# Output file names
OUTPUT_STORY_FILE = "1-Story.txt"
OUTPUT_NARRATION_FILE = "2-Narration.txt"
OUTPUT_CHARACTER_SHEET_FILE = "3-Character-Sheet.txt"
OUTPUT_SCENES_FILE = "4-Scenes.txt"
OUTPUT_IMAGE_PROMPTS_FILE = "5-Image-Prompts.txt"
OUTPUT_PROCESSING_REPORT_FILE = "processing-report.txt"

# =============================================================================
# PROCESSING SETTINGS
# =============================================================================

MAX_RETRIES = 3
RETRY_DELAY = 2
API_TIMEOUT = 30.0
MINIMUM_QUALITY_SCORE = 0.7
MAXIMUM_ERROR_COUNT = 5

# =============================================================================
# OUTPUT GENERATION SETTINGS
# =============================================================================

def generate_output_folder_name(story_title="story"):
    """Generate a unique folder name for output"""
    sanitized_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).strip()
    sanitized_title = sanitized_title.replace(' ', '-').lower()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{sanitized_title}-{timestamp}"

def get_input_folder_path():
    """Get the full path for input folder"""
    return f"{INPUT_FOLDER_NAME}"

def get_output_folder_path(story_title="story"):
    """Get the full path for output folder"""
    folder_name = generate_output_folder_name(story_title)
    return f"{OUTPUT_FOLDER_NAME}/{folder_name}"

def get_ai_queries_folder_path():
    """Get the full path for AI queries folder"""
    return f"{INPUT_FOLDER_NAME}/{AI_QUERIES_FOLDER}"

def get_framework_templates_folder_path():
    """Get the full path for framework templates folder"""
    return f"{INPUT_FOLDER_NAME}/{FRAMEWORK_TEMPLATES_FOLDER}"

def get_style_guides_folder_path():
    """Get the full path for style guides folder"""
    return f"{INPUT_FOLDER_NAME}/{STYLE_GUIDES_FOLDER}"

# =============================================================================
# VALIDATION SETTINGS
# =============================================================================

REQUIRED_INPUT_FILES = [
    STORY_INPUT_FILE,
    f"{AI_QUERIES_FOLDER}/{CHARACTER_QUERIES_FILE}",
    f"{AI_QUERIES_FOLDER}/{SCENE_QUERIES_FILE}",
    f"{AI_QUERIES_FOLDER}/{NARRATION_QUERIES_FILE}",
    f"{AI_QUERIES_FOLDER}/{PROMPT_QUERIES_FILE}",
    f"{FRAMEWORK_TEMPLATES_FOLDER}/{NARRATION_TEMPLATE_FILE}",
    f"{FRAMEWORK_TEMPLATES_FOLDER}/{CHARACTER_TEMPLATE_FILE}",
    f"{FRAMEWORK_TEMPLATES_FOLDER}/{SCENE_TEMPLATE_FILE}",
    f"{STYLE_GUIDES_FOLDER}/{VISUAL_RULES_FILE}"
]

EXPECTED_OUTPUT_FILES = [
    OUTPUT_STORY_FILE,
    OUTPUT_NARRATION_FILE,
    OUTPUT_CHARACTER_SHEET_FILE,
    OUTPUT_SCENES_FILE,
    OUTPUT_IMAGE_PROMPTS_FILE,
    OUTPUT_PROCESSING_REPORT_FILE
]

# =============================================================================
# GOOGLE DRIVE API SETTINGS
# =============================================================================

GOOGLE_DRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.appdata'
]

CREDENTIALS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'credentials.json')
MIME_TYPE_FOLDER = 'application/vnd.google-apps.folder'
MIME_TYPE_TEXT = 'text/plain'

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# =============================================================================
# ERROR MESSAGES
# =============================================================================

ERROR_MESSAGES = {
    'missing_credentials': "Credentials file not found.",
    'drive_api_error': "Google Drive API error: {error}",
    'missing_input_file': "Required input file not found: {file_path}",
    'ai_api_error': "DeepSeek API error: {error}",
    'processing_error': "Processing error: {error}"
}

SUCCESS_MESSAGES = {
    'drive_connected': "Connected to Google Drive",
    'folders_created': "Directory structure created",
    'story_processed': "Story processed: {story_title}",
    'files_generated': "Generated {file_count} files"
}

# =============================================================================
# VALIDATION
# =============================================================================

def validate_config():
    """Validate that all required configuration is present"""
    if not os.path.exists(CREDENTIALS_FILE_PATH):
        return False, ERROR_MESSAGES['missing_credentials']
    
    if not DEEPSEEK_API_KEY:
        return False, "DEEPSEEK_API_KEY not set."
    
    if not GOOGLE_DRIVE_ROOT_FOLDER_ID:
        return False, "GOOGLE_DRIVE_ROOT_FOLDER_ID not configured."
    
    return True, "Configuration valid"

# Run configuration validation
config_valid, config_error = validate_config()
if not config_valid:
    print(f"⚠️ Configuration Warning: {config_error}")