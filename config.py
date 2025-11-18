"""
Story Automation System - Centralized Configuration
Everything configurable in one place - No code modifications needed for changes
"""

import os
from datetime import datetime

# =============================================================================
# GOOGLE DRIVE CONFIGURATION
# =============================================================================
GOOGLE_DRIVE_ROOT_FOLDER_ID = "1vWhSS20YjkFNitEZI14c8C1uEt12puLE"

# Folder Structure in Google Drive
DRIVE_FOLDER_STRUCTURE = {
    'framework_root': 'Framework',
    'ai_queries_folder': 'Framework/ai_queries',
    'framework_templates_folder': 'Framework/framework_templates', 
    'style_guides_folder': 'Framework/style_guides',
    'input_folder': '',  # Root level
    'output_folder': ''   # Root level for generated folders
}

# Framework Files - All 8 required files with exact paths
FRAMEWORK_FILES = {
    # AI Query Files
    'character_queries': 'Framework/ai_queries/character_queries.txt',
    'scene_queries': 'Framework/ai_queries/scene_queries.txt',
    'narration_queries': 'Framework/ai_queries/narration_queries.txt',
    'prompt_queries': 'Framework/ai_queries/prompt_queries.txt',
    
    # Framework Template Files
    'narration_template': 'Framework/framework_templates/narration_template.txt',
    'character_template': 'Framework/framework_templates/character_template.txt', 
    'scene_template': 'Framework/framework_templates/scene_template.txt',
    
    # Style Guide Files
    'visual_rules': 'Framework/style_guides/visual_rules.txt'
}

# Input/Output Files
INPUT_OUTPUT_FILES = {
    'story_input': 'story_input.txt',  # At root level
    
    # Generated Output Files (in timestamped folders)
    'output_story': '1-Story.txt',
    'output_narration': '2-Narration.txt', 
    'output_character_sheet': '3-Character-Sheet.txt',
    'output_scenes': '4-Scenes.txt',
    'output_image_prompts': '5-Image-Prompts.txt',
    'output_processing_report': 'processing-report.txt'
}

# =============================================================================
# AI PROCESSING RULES - ENFORCED LIMITS
# =============================================================================
PROCESSING_RULES = {
    'character_limits': {
        'min_characters': 2,
        'max_characters': 6,
        'required_fields': ['name', 'role', 'personality', 'appearance', 'motivation', 'emotional_traits', 'description']
    },
    
    'scene_limits': {
        'min_scenes': 4,
        'max_scenes': 8,
        'required_fields': ['title', 'location', 'emotion', 'characters', 'action', 'description']
    },
    
    'narration_limits': {
        'min_words': 900,
        'max_words': 1200,
        'target_age': '4-6 years',
        'duration_minutes': '8-10',
        'required_elements': ['audience_questions', 'sensory_descriptions', 'emotional_shifts', 'positive_ending']
    },
    
    'prompt_limits': {
        'prompts_per_scene': 1,
        'required_elements': ['art_style', 'lighting', 'colors', 'character_consistency', 'aspect_ratio']
    }
}

# =============================================================================
# AI CONFIGURATION - DeepSeek API
# =============================================================================
AI_CONFIG = {
    'api_key': os.getenv('DEEPSEEK_API_KEY', 'sk-df60b28326444de6859976f6e603fd9c'),
    'base_url': 'https://api.deepseek.com',
    'model': 'deepseek-chat',
    'max_tokens': 4000,
    'temperature': 0.7,
    'timeout': 30.0,
    
    # SSL Configuration - Keep disabled as requested
    'verify_ssl': False
}

# =============================================================================
# PARSING RULES - STRICT FORMAT ENFORCEMENT
# =============================================================================
PARSING_RULES = {
    'character_format': {
        'start_marker': 'Character:',
        'field_markers': {
            'name': 'Character:',
            'role': 'Role:',
            'personality': 'Personality:',
            'appearance': 'Appearance:', 
            'motivation': 'Motivation:',
            'emotional_traits': 'Emotional Traits:',
            'description': 'Description:'
        },
        'separator': '\n\n'  # Empty line between characters
    },
    
    'scene_format': {
        'start_marker': 'Scene:',
        'field_markers': {
            'title': 'Scene:',
            'location': 'Location:',
            'emotion': 'Emotion:',
            'characters': 'Characters:',
            'action': 'Action:', 
            'description': 'Description:'
        },
        'separator': '\n\n'  # Empty line between scenes
    },
    
    'prompt_format': {
        'start_marker': 'Prompt for',
        'field_markers': {
            'scene_title': 'Prompt for',
            'prompt_text': 'Children\'s storybook illustration'
        }
    }
}

# =============================================================================
# TEMPLATE VARIABLE MAPPING
# =============================================================================
TEMPLATE_VARIABLES = {
    'character_queries': ['story_text'],
    'scene_queries': ['story_text', 'characters'],
    'narration_queries': ['story_text', 'characters', 'scenes', 'visual_style'],
    'prompt_queries': ['scenes', 'characters', 'visual_rules'],
    
    'narration_template': ['story_title', 'character_list', 'scene_list', 'narration_content'],
    'character_template': ['story_title', 'character_count', 'character_sections'],
    'scene_template': ['story_title', 'scene_count', 'scene_sections']
}

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================
def generate_output_folder_name(story_title="story"):
    """Generate unique output folder name - Configurable format"""
    sanitized_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).strip()
    sanitized_title = sanitized_title.replace(' ', '-').lower()[:30]  # Limit length
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{sanitized_title}_{timestamp}"

# =============================================================================
# VALIDATION CONFIGURATION
# =============================================================================
VALIDATION_RULES = {
    'required_framework_files': list(FRAMEWORK_FILES.keys()),
    'min_story_length': 100,  # characters
    'max_story_length': 10000, # characters
    'quality_thresholds': {
        'character_completeness': 0.8,  # 80% of required fields filled
        'scene_coherence': 0.7,
        'narration_quality': 0.8
    }
}

# =============================================================================
# ERROR HANDLING & MESSAGES
# =============================================================================
ERROR_MESSAGES = {
    'missing_credentials': "Google Drive credentials file not found.",
    'drive_connection_failed': "Failed to connect to Google Drive.",
    'missing_framework_file': "Required framework file not found: {file_path}",
    'ai_api_error': "DeepSeek API error: {error}",
    'processing_failed': "Story processing failed: {error}",
    'validation_failed': "Validation failed: {rule} - {details}"
}

SUCCESS_MESSAGES = {
    'drive_connected': "✅ Connected to Google Drive successfully",
    'framework_loaded': "✅ All framework files loaded",
    'story_processed': "✅ Story processed successfully: {story_title}",
    'files_generated': "✅ Generated {file_count} output files"
}

# =============================================================================
# SYSTEM SETTINGS
# =============================================================================
SYSTEM_SETTINGS = {
    'max_retries': 3,
    'retry_delay': 2,
    'log_level': 'INFO',
    'timeout': 30.0
}

# =============================================================================
# GOOGLE DRIVE API SETTINGS
# =============================================================================
GOOGLE_DRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.appdata'
]

# Local credentials file path (only local file needed)
CREDENTIALS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'credentials.json')

# MIME Types
MIME_TYPE_FOLDER = 'application/vnd.google-apps.folder'
MIME_TYPE_TEXT = 'text/plain'

# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================
def validate_configuration():
    """Validate that all required configuration is present and valid"""
    errors = []
    
    # Check credentials file exists
    if not os.path.exists(CREDENTIALS_FILE_PATH):
        errors.append(ERROR_MESSAGES['missing_credentials'])
    
    # Check AI API key
    if not AI_CONFIG['api_key']:
        errors.append("DEEPSEEK_API_KEY not configured")
    elif AI_CONFIG['api_key'] == 'sk-df60b28326444de6859976f6e603fd9c':
        print("⚠️  Using default DeepSeek API key - replace with your actual key for production")
    
    # Check processing rules are valid
    if PROCESSING_RULES['character_limits']['min_characters'] > PROCESSING_RULES['character_limits']['max_characters']:
        errors.append("Character limits are invalid (min > max)")
    
    if PROCESSING_RULES['scene_limits']['min_scenes'] > PROCESSING_RULES['scene_limits']['max_scenes']:
        errors.append("Scene limits are invalid (min > max)")
    
    return len(errors) == 0, errors

# Validate on import
config_valid, config_errors = validate_configuration()
if not config_valid:
    print("⚠️ Configuration Warnings:")
    for error in config_errors:
        print(f"   - {error}")