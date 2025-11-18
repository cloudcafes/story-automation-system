"""
Story Processor - SSL Verification Disabled
"""

import os
import time
import json
import datetime
import requests
import httpx
import glob
import logging
import re
import urllib3
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from openai import OpenAI

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    DEEPSEEK_MAX_TOKENS,
    DEEPSEEK_TEMPERATURE,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_VERIFY_SSL,
    MAX_RETRIES,
    RETRY_DELAY,
    ERROR_MESSAGES,
    REQUIRED_INPUT_FILES
)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NiftyAIAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.client = None
        self.history_file = "analysis_history.txt"
        self.is_available = False
        self.initialize_client()

    def initialize_client(self) -> bool:
        """Initialize DeepSeek API client with SSL disabled"""
        try:
            if not self.api_key:
                raise RuntimeError("DeepSeek API key not found.")

            # SSL verification disabled
            http_client = httpx.Client(verify=False, timeout=30.0)
            
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com",
                http_client=http_client,
                max_retries=2
            )
            
            # Test connection
            _ = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                temperature=0
            )
            
            print("✅ DeepSeek AI client initialized (SSL disabled)")
            self.is_available = True
            return True
            
        except Exception as e:
            print(f"❌ DeepSeek client failed: {e}")
            self.client = None
            self.is_available = False
            return False

    def analyze_with_retry(self, prompt: str, system_message: Optional[str] = None, max_tokens: Optional[int] = None) -> Optional[str]:
        """Analyze with retry logic"""
        if not self.is_available or not self.client:
            return None
            
        for attempt in range(MAX_RETRIES):
            try:
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    max_tokens=max_tokens or DEEPSEEK_MAX_TOKENS,
                    temperature=DEEPSEEK_TEMPERATURE
                )
                
                result = response.choices[0].message.content.strip()
                self._log_analysis(prompt, result)
                return result
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    print(f"⚠️ API call failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ API call failed after {MAX_RETRIES} attempts: {e}")
                    return None

    def _log_analysis(self, prompt: str, result: str):
        """Log analysis history"""
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Time: {datetime.datetime.now().isoformat()}\n")
                f.write(f"Prompt: {prompt}\n")
                f.write(f"Result: {result}\n")
        except Exception as e:
            print(f"⚠️ Failed to log analysis: {e}")

# ... [rest of story_processor.py remains the same with OfflineFallbackProcessor and StoryProcessor] ...

class OfflineFallbackProcessor:
    """Offline fallback when DeepSeek is unavailable"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_story_title(self, story_content):
        """Extract story title from content"""
        lines = story_content.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and not line.startswith((' ', '\t')) and len(line) < 100:
                title = re.sub(r'[^\w\s-]', '', line).strip()
                if title and len(title) > 3:
                    return title
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                words = line.split()[:5]
                return ' '.join(words) + " Story"
        
        return "My Wonderful Story"
    
    def analyze_characters(self, story_content):
        """Basic character analysis"""
        characters = []
        
        # Look for proper nouns as potential character names
        words = story_content.split()
        for i, word in enumerate(words):
            if (word.istitle() and len(word) > 2 and 
                word not in ['The', 'And', 'But', 'For', 'With'] and
                i + 1 < len(words) and words[i + 1].istitle()):
                
                character_name = word
                if i + 2 < len(words) and words[i + 2].istitle():
                    character_name = f"{word} {words[i + 1]} {words[i + 2]}"
                elif i + 1 < len(words) and words[i + 1].istitle():
                    character_name = f"{word} {words[i + 1]}"
                
                if character_name not in [c['name'] for c in characters]:
                    characters.append({
                        'name': character_name,
                        'role': 'character',
                        'description': f'A brave character from our story'
                    })
        
        if not characters:
            characters = [
                {
                    'name': 'Adventure Hero',
                    'role': 'protagonist',
                    'description': 'The brave main character of our story'
                },
                {
                    'name': 'Magical Friend', 
                    'role': 'companion',
                    'description': 'A wonderful friend who helps on the adventure'
                }
            ]
        
        return characters[:4]
    
    def analyze_scenes(self, story_content, characters):
        """Basic scene analysis"""
        scenes = []
        paragraphs = [p.strip() for p in story_content.split('\n\n') if p.strip()]
        
        scene_templates = [
            "The Beginning - Where our adventure starts",
            "The Journey - Traveling to new places", 
            "The Discovery - Finding something wonderful",
            "The Challenge - Overcoming obstacles",
            "The Celebration - A happy ending"
        ]
        
        for i, paragraph in enumerate(paragraphs[:5]):
            if paragraph:
                scenes.append({
                    'title': scene_templates[i] if i < len(scene_templates) else f"Scene {i+1}",
                    'description': paragraph[:150] + ('...' if len(paragraph) > 150 else ''),
                    'location': 'Magical Story World',
                    'emotion': ['happy', 'excited', 'curious', 'brave', 'joyful'][i % 5]
                })
        
        if not scenes:
            scenes = [{
                'title': 'Our Magical Adventure',
                'description': story_content[:200] + '...',
                'location': 'Story World',
                'emotion': 'happy'
            }]
        
        return scenes
    
    def generate_narration(self, story_content, characters, scenes):
        """Generate basic narration"""
        character_names = ', '.join([char['name'] for char in characters[:2]])
        
        narration = f"""Welcome to our wonderful story time! 

Today we're going on a magical adventure with {character_names}.

{story_content[:300]}...

What an amazing journey! I wonder what your favorite part was?

Remember, every story is a new adventure waiting to be discovered!"""
        
        return narration
    
    def generate_image_prompts(self, scenes, characters):
        """Generate basic image prompts"""
        prompts = []
        
        for i, scene in enumerate(scenes):
            prompt = f"""Beautiful children's storybook illustration of {scene['title']}. 
Magical, colorful, warm lighting, storybook style, child-friendly, 
detailed, 4K resolution, happy children's story, enchanting atmosphere"""
            
            prompts.append({
                'scene': scene['title'],
                'prompt': prompt
            })
        
        return prompts

class StoryProcessor:
    """Processes stories using your NiftyAIAnalyzer with fallback support"""
    
    def __init__(self, drive_manager, template_engine):
        self.logger = logging.getLogger(__name__)
        self.drive_manager = drive_manager
        self.template_engine = template_engine
        self.ai_analyzer = NiftyAIAnalyzer()
        self.offline_processor = OfflineFallbackProcessor()
        self.ai_queries = {}
        self.framework_templates = {}
        self.style_guides = {}
    
    def load_required_files(self, folder_ids):
        """Load all required input files from Google Drive"""
        try:
            self.logger.info("Loading required input files...")
            
            # Load AI queries
            self.ai_queries = {
                'character': self.drive_manager.read_input_file(
                    f"ai_queries/character_queries.txt", folder_ids
                ),
                'scene': self.drive_manager.read_input_file(
                    f"ai_queries/scene_queries.txt", folder_ids
                ),
                'narration': self.drive_manager.read_input_file(
                    f"ai_queries/narration_queries.txt", folder_ids
                ),
                'prompt': self.drive_manager.read_input_file(
                    f"ai_queries/prompt_queries.txt", folder_ids
                )
            }
            
            # Load framework templates
            self.framework_templates = {
                'narration': self.drive_manager.read_input_file(
                    f"framework_templates/narration_template.txt", folder_ids
                ),
                'character': self.drive_manager.read_input_file(
                    f"framework_templates/character_template.txt", folder_ids
                ),
                'scene': self.drive_manager.read_input_file(
                    f"framework_templates/scene_template.txt", folder_ids
                )
            }
            
            # Load style guides
            self.style_guides['visual'] = self.drive_manager.read_input_file(
                f"style_guides/visual_rules.txt", folder_ids
            )
            
            # Load story input
            self.story_content = self.drive_manager.read_input_file(
                "story_input.txt", folder_ids
            )
            
            # Validate all files were loaded
            missing_files = []
            for key, content in self.ai_queries.items():
                if not content:
                    missing_files.append(f"ai_queries/{key}_queries.txt")
            
            for key, content in self.framework_templates.items():
                if not content:
                    missing_files.append(f"framework_templates/{key}_template.txt")
            
            if not self.style_guides.get('visual'):
                missing_files.append("style_guides/visual_rules.txt")
            
            if not self.story_content:
                missing_files.append("story_input.txt")
            
            if missing_files:
                raise ValueError(f"Missing required files: {', '.join(missing_files)}")
            
            self.logger.info("✅ All required files loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading required files: {e}")
            raise
    
    def process_story(self, folder_ids):
        """Main method to process story with AI or fallback"""
        try:
            self.logger.info("Starting story processing pipeline...")
            
            # Load all required files
            self.load_required_files(folder_ids)
            
            # Try AI processing first, then fallback
            if self.ai_analyzer.is_available:
                self.logger.info(" Using NiftyAIAnalyzer for processing...")
                results = self._process_with_ai()
            else:
                self.logger.warning(" NiftyAIAnalyzer unavailable, using offline processing...")
                results = self._process_offline()
            
            self.logger.info("✅ Story processing completed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in story processing pipeline: {e}")
            raise
    
    def _process_with_ai(self):
        """Process story using NiftyAIAnalyzer"""
        try:
            # Analyze characters
            character_analysis = self.ai_analyzer.analyze_with_retry(
                self.ai_queries['character'].format(story_text=self.story_content),
                "You are a character analysis expert. Extract and describe characters from stories accurately."
            )
            characters = self._parse_character_analysis(character_analysis) if character_analysis else []
            
            # Analyze scenes
            character_list = "\n".join([f"- {char['name']}: {char.get('role', 'unknown')}" for char in characters])
            scene_analysis = self.ai_analyzer.analyze_with_retry(
                self.ai_queries['scene'].format(story_text=self.story_content, characters=character_list),
                "You are a story analysis expert. Break down stories into meaningful scenes with emotional arcs."
            )
            scenes = self._parse_scene_analysis(scene_analysis) if scene_analysis else []
            
            # Generate narration
            character_summary = "\n".join([f"- {char['name']}: {char.get('description', 'No description')}" for char in characters])
            scene_summary = "\n".join([f"- {scene['title']}: {scene.get('description', 'No description')}" for scene in scenes])
            
            narration = self.ai_analyzer.analyze_with_retry(
                self.ai_queries['narration'].format(
                    story_text=self.story_content,
                    characters=character_summary,
                    scenes=scene_summary,
                    visual_style=self.style_guides['visual']
                ),
                "You are a professional children's story narrator. Create engaging, age-appropriate narration."
            )
            
            # Generate image prompts
            character_descriptions = {char['name']: char.get('description', 'Unknown') for char in characters}
            image_prompts_text = self.ai_analyzer.analyze_with_retry(
                self.ai_queries['prompt'].format(
                    scenes=json.dumps(scenes, indent=2),
                    characters=json.dumps(character_descriptions, indent=2),
                    visual_rules=self.style_guides['visual']
                ),
                "You are an expert AI image prompt engineer. Create detailed, consistent image prompts."
            )
            image_prompts = self._parse_image_prompts(image_prompts_text) if image_prompts_text else []
            
            return {
                'story_title': self.offline_processor.extract_story_title(self.story_content),
                'original_story': self.story_content,
                'characters': characters,
                'scenes': scenes,
                'narration': narration or "AI narration generation failed.",
                'image_prompts': image_prompts,
                'processing_stats': {
                    'character_count': len(characters),
                    'scene_count': len(scenes),
                    'image_prompt_count': len(image_prompts)
                },
                'processing_method': 'ai'
            }
            
        except Exception as e:
            self.logger.error(f"AI processing failed, falling back to offline: {e}")
            return self._process_offline()
    
    def _process_offline(self):
        """Process story using offline methods"""
        characters = self.offline_processor.analyze_characters(self.story_content)
        scenes = self.offline_processor.analyze_scenes(self.story_content, characters)
        narration = self.offline_processor.generate_narration(self.story_content, characters, scenes)
        image_prompts = self.offline_processor.generate_image_prompts(scenes, characters)
        
        return {
            'story_title': self.offline_processor.extract_story_title(self.story_content),
            'original_story': self.story_content,
            'characters': characters,
            'scenes': scenes,
            'narration': narration,
            'image_prompts': image_prompts,
            'processing_stats': {
                'character_count': len(characters),
                'scene_count': len(scenes),
                'image_prompt_count': len(image_prompts)
            },
            'processing_method': 'offline'
        }
    
    def _parse_character_analysis(self, analysis_text):
        """Parse character analysis into structured data"""
        characters = []
        lines = analysis_text.split('\n')
        
        current_character = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ['name', 'character']:
                    if current_character:
                        characters.append(current_character)
                    current_character = {'name': value}
                elif current_character:
                    current_character[key] = value
        
        if current_character:
            characters.append(current_character)
        
        if not characters:
            characters = [{'name': 'Main Character', 'role': 'protagonist', 'description': 'Main story character'}]
        
        return characters
    
    def _parse_scene_analysis(self, analysis_text):
        """Parse scene analysis into structured data"""
        scenes = []
        lines = analysis_text.split('\n')
        
        current_scene = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.lower().startswith('scene') or line.lower().startswith('part'):
                if current_scene:
                    scenes.append(current_scene)
                current_scene = {'title': line, 'description': ''}
            elif ':' in line and current_scene:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ['location', 'emotion', 'characters', 'action']:
                    current_scene[key] = value
                else:
                    current_scene['description'] += line + ' '
            elif current_scene:
                current_scene['description'] += line + ' '
        
        if current_scene:
            scenes.append(current_scene)
        
        if not scenes:
            scenes = [{'title': 'Story Scene', 'description': 'Main story sequence', 'location': 'unknown', 'emotion': 'neutral'}]
        
        return scenes
    
    def _parse_image_prompts(self, prompts_text):
        """Parse image prompts into structured data"""
        prompts = []
        lines = prompts_text.split('\n')
        
        current_prompt = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.lower().startswith('scene') or line.lower().startswith('prompt'):
                if current_prompt:
                    prompts.append(current_prompt)
                current_prompt = {'scene': line, 'prompt': ''}
            elif current_prompt:
                current_prompt['prompt'] += line + ' '
        
        if current_prompt:
            prompts.append(current_prompt)
        
        return prompts

# Factory function
def create_story_processor(drive_manager, template_engine):
    return StoryProcessor(drive_manager, template_engine)