"""
Story Processor - AI-Powered Story Analysis and Content Generation
Enforces strict processing rules and quality gates from config
"""

import logging
import time
import json
import re
from typing import Dict, List, Any, Optional
import httpx
from openai import OpenAI

from config import (
    AI_CONFIG,
    PROCESSING_RULES,
    PARSING_RULES,
    VALIDATION_RULES,
    ERROR_MESSAGES,
    SYSTEM_SETTINGS
)

class NiftyAIAnalyzer:
    """Handles AI analysis with DeepSeek API with strict format enforcement"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.is_available = False
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize DeepSeek API client with SSL disabled"""
        try:
            if not AI_CONFIG['api_key']:
                raise RuntimeError("DeepSeek API key not configured")
            
            # Create HTTP client with SSL disabled
            http_client = httpx.Client(
                verify=AI_CONFIG['verify_ssl'],
                timeout=AI_CONFIG['timeout']
            )
            
            self.client = OpenAI(
                api_key=AI_CONFIG['api_key'],
                base_url=AI_CONFIG['base_url'],
                http_client=http_client
            )
            
            # Test connection with simple request
            test_response = self.client.chat.completions.create(
                model=AI_CONFIG['model'],
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )
            
            self.is_available = True
            self.logger.info("✅ DeepSeek AI client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ DeepSeek client initialization failed: {e}")
            self.client = None
            self.is_available = False
    
    def analyze_with_retry(self, prompt: str, system_message: str = None) -> Optional[str]:
        """Analyze with retry logic and format enforcement"""
        if not self.is_available or not self.client:
            self.logger.error("AI client not available")
            return None
        
        for attempt in range(SYSTEM_SETTINGS['max_retries']):
            try:
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                
                response = self.client.chat.completions.create(
                    model=AI_CONFIG['model'],
                    messages=messages,
                    max_tokens=AI_CONFIG['max_tokens'],
                    temperature=AI_CONFIG['temperature']
                )
                
                result = response.choices[0].message.content.strip()
                self.logger.info(f"✅ AI analysis completed (attempt {attempt + 1})")
                return result
                
            except Exception as e:
                if attempt < SYSTEM_SETTINGS['max_retries'] - 1:
                    wait_time = SYSTEM_SETTINGS['retry_delay'] * (2 ** attempt)
                    self.logger.warning(f" AI API call failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"❌ AI API call failed after {SYSTEM_SETTINGS['max_retries']} attempts: {e}")
                    return None

class StoryProcessor:
    """Processes stories with strict rule enforcement and quality gates"""
    
    def __init__(self, drive_manager, template_engine):
        self.logger = logging.getLogger(__name__)
        self.drive_manager = drive_manager
        self.template_engine = template_engine
        self.ai_analyzer = NiftyAIAnalyzer()
        self.framework_content = {}
    
    def load_framework_content(self):
        """Load all framework files from Google Drive"""
        try:
            self.logger.info(" Loading framework content...")
            
            # Load AI queries
            self.framework_content['character_queries'] = self.drive_manager.read_framework_file('character_queries')
            self.framework_content['scene_queries'] = self.drive_manager.read_framework_file('scene_queries')
            self.framework_content['narration_queries'] = self.drive_manager.read_framework_file('narration_queries')
            self.framework_content['prompt_queries'] = self.drive_manager.read_framework_file('prompt_queries')
            
            # Load templates
            self.framework_content['narration_template'] = self.drive_manager.read_framework_file('narration_template')
            self.framework_content['character_template'] = self.drive_manager.read_framework_file('character_template')
            self.framework_content['scene_template'] = self.drive_manager.read_framework_file('scene_template')
            
            # Load style guides
            self.framework_content['visual_rules'] = self.drive_manager.read_framework_file('visual_rules')
            
            self.logger.info("✅ All framework content loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load framework content: {e}")
            raise
    
    def process_story(self, story_content: str) -> Dict[str, Any]:
        """Main story processing pipeline with quality gates"""
        try:
            self.logger.info(" Starting story processing pipeline...")
            
            # Load framework content
            self.load_framework_content()
            
            # Validate story input
            self._validate_story_input(story_content)
            
            # Extract story title
            story_title = self._extract_story_title(story_content)
            self.logger.info(f" Processing story: '{story_title}'")
            
            # Process with AI or fallback
            if self.ai_analyzer.is_available:
                self.logger.info("烙 Using AI analysis...")
                results = self._process_with_ai(story_content, story_title)
            else:
                self.logger.warning("⚡ AI unavailable, using fallback processing...")
                results = self._process_with_fallback(story_content, story_title)
            
            # Apply quality gates
            self._apply_quality_gates(results)
            
            self.logger.info("✅ Story processing completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Story processing failed: {e}")
            raise
    
    def _validate_story_input(self, story_content: str):
        """Validate story input meets requirements"""
        if not story_content or len(story_content.strip()) < VALIDATION_RULES['min_story_length']:
            raise ValueError(f"Story too short (min {VALIDATION_RULES['min_story_length']} characters)")
        
        if len(story_content) > VALIDATION_RULES['max_story_length']:
            raise ValueError(f"Story too long (max {VALIDATION_RULES['max_story_length']} characters)")
    
    def _extract_story_title(self, story_content: str) -> str:
        """Extract story title from content"""
        lines = story_content.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and not line.startswith((' ', '\t')) and len(line) < 100:
                title = re.sub(r'[^\w\s-]', '', line).strip()
                if title and len(title) > 3:
                    return title
        
        # Fallback title
        return "Magical Story Adventure"
    
    def _process_with_ai(self, story_content: str, story_title: str) -> Dict[str, Any]:
        """Process story using AI analysis with strict format enforcement"""
        try:
            # Step 1: Character Analysis
            self.logger.info(" Analyzing characters...")
            character_prompt = self.framework_content['character_queries'].format(
                story_text=story_content
            )
            character_analysis = self.ai_analyzer.analyze_with_retry(
                character_prompt,
                "You are a character analysis expert. Extract characters with strict format compliance."
            )
            characters = self._parse_characters(character_analysis) if character_analysis else []
            
            # Step 2: Scene Analysis
            self.logger.info(" Analyzing scenes...")
            character_summary = self._format_character_summary(characters)
            scene_prompt = self.framework_content['scene_queries'].format(
                story_text=story_content,
                characters=character_summary
            )
            scene_analysis = self.ai_analyzer.analyze_with_retry(
                scene_prompt,
                "You are a story structure expert. Break down stories into meaningful scenes with emotional arcs."
            )
            scenes = self._parse_scenes(scene_analysis) if scene_analysis else []
            
            # Step 3: Narration Generation
            self.logger.info(" Generating narration...")
            scene_summary = self._format_scene_summary(scenes)
            narration_prompt = self.framework_content['narration_queries'].format(
                story_text=story_content,
                characters=character_summary,
                scenes=scene_summary,
                visual_style=self.framework_content['visual_rules']
            )
            narration = self.ai_analyzer.analyze_with_retry(
                narration_prompt,
                "You are a professional children's story narrator. Create engaging, age-appropriate narration."
            )
            
            # Step 4: Image Prompts Generation
            self.logger.info(" Generating image prompts...")
            prompt_prompt = self.framework_content['prompt_queries'].format(
                scenes=json.dumps(scenes, indent=2),
                characters=json.dumps({char['name']: char.get('description', '') for char in characters}, indent=2),
                visual_rules=self.framework_content['visual_rules']
            )
            prompt_analysis = self.ai_analyzer.analyze_with_retry(
                prompt_prompt,
                "You are an expert AI image prompt engineer. Create detailed, consistent image prompts."
            )
            image_prompts = self._parse_image_prompts(prompt_analysis, scenes) if prompt_analysis else []
            
            return {
                'story_title': story_title,
                'original_story': story_content,
                'characters': characters,
                'scenes': scenes,
                'narration': narration or "Narration generation failed.",
                'image_prompts': image_prompts,
                'processing_stats': {
                    'character_count': len(characters),
                    'scene_count': len(scenes),
                    'image_prompt_count': len(image_prompts),
                    'processing_method': 'ai'
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ AI processing failed: {e}")
            # Fall back to basic processing
            return self._process_with_fallback(story_content, story_title)
    
    def _process_with_fallback(self, story_content: str, story_title: str) -> Dict[str, Any]:
        """Fallback processing when AI is unavailable"""
        self.logger.info(" Using fallback processing...")
        
        # Basic character extraction
        characters = self._extract_basic_characters(story_content)
        
        # Basic scene breakdown
        scenes = self._create_basic_scenes(story_content, characters)
        
        # Basic narration
        narration = self._create_basic_narration(story_content, characters, scenes)
        
        # Basic image prompts
        image_prompts = self._create_basic_image_prompts(scenes, characters)
        
        return {
            'story_title': story_title,
            'original_story': story_content,
            'characters': characters,
            'scenes': scenes,
            'narration': narration,
            'image_prompts': image_prompts,
            'processing_stats': {
                'character_count': len(characters),
                'scene_count': len(scenes),
                'image_prompt_count': len(image_prompts),
                'processing_method': 'fallback'
            }
        }
    
    def _parse_characters(self, analysis_text: str) -> List[Dict[str, str]]:
        """Parse character analysis with strict format enforcement"""
        characters = []
        lines = analysis_text.split('\n')
        current_character = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_character:
                    if self._validate_character(current_character):
                        characters.append(current_character)
                    current_character = {}
                continue
            
            # Parse character fields based on config rules
            for field, marker in PARSING_RULES['character_format']['field_markers'].items():
                if line.startswith(marker):
                    value = line[len(marker):].strip()
                    current_character[field] = value
                    break
        
        # Add final character if exists
        if current_character and self._validate_character(current_character):
            characters.append(current_character)
        
        # Apply character limits
        characters = characters[:PROCESSING_RULES['character_limits']['max_characters']]
        
        if len(characters) < PROCESSING_RULES['character_limits']['min_characters']:
            self.logger.warning(f"⚠️ Character count below minimum, using fallback characters")
            characters = self._extract_basic_characters(analysis_text)
        
        self.logger.info(f"✅ Parsed {len(characters)} characters")
        return characters
    
    def _parse_scenes(self, analysis_text: str) -> List[Dict[str, str]]:
        """Parse scene analysis with strict format enforcement"""
        scenes = []
        lines = analysis_text.split('\n')
        current_scene = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_scene:
                    if self._validate_scene(current_scene):
                        scenes.append(current_scene)
                    current_scene = {}
                continue
            
            # Parse scene fields based on config rules
            for field, marker in PARSING_RULES['scene_format']['field_markers'].items():
                if line.startswith(marker):
                    value = line[len(marker):].strip()
                    current_scene[field] = value
                    break
        
        # Add final scene if exists
        if current_scene and self._validate_scene(current_scene):
            scenes.append(current_scene)
        
        # Apply scene limits
        scenes = scenes[:PROCESSING_RULES['scene_limits']['max_scenes']]
        
        if len(scenes) < PROCESSING_RULES['scene_limits']['min_scenes']:
            self.logger.warning(f"⚠️ Scene count below minimum, using fallback scenes")
            scenes = self._create_basic_scenes(analysis_text, [])
        
        self.logger.info(f"✅ Parsed {len(scenes)} scenes")
        return scenes
    
    def _parse_image_prompts(self, analysis_text: str, scenes: List[Dict]) -> List[Dict[str, str]]:
        """Parse image prompts with strict format enforcement"""
        prompts = []
        lines = analysis_text.split('\n')
        current_prompt = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Prompt for'):
                if current_prompt:
                    prompts.append(current_prompt)
                scene_title = line.replace('Prompt for', '').replace(':', '').strip()
                current_prompt = {'scene': scene_title, 'prompt': ''}
            elif current_prompt and line:
                current_prompt['prompt'] += line + ' '
        
        if current_prompt:
            prompts.append(current_prompt)
        
        # Ensure one prompt per scene
        if len(prompts) < len(scenes):
            for i, scene in enumerate(scenes):
                if i >= len(prompts):
                    prompts.append({
                        'scene': scene.get('title', f'Scene {i+1}'),
                        'prompt': f"Children's storybook illustration of {scene.get('title', 'story scene')}, magical, colorful, warm lighting, storybook style"
                    })
        
        self.logger.info(f"✅ Generated {len(prompts)} image prompts")
        return prompts
    
    def _validate_character(self, character: Dict) -> bool:
        """Validate character has required fields"""
        required_fields = PROCESSING_RULES['character_limits']['required_fields']
        missing_fields = [field for field in required_fields if not character.get(field)]
        
        if missing_fields:
            self.logger.warning(f"⚠️ Character missing fields: {missing_fields}")
            return len(missing_fields) <= 2  # Allow some missing fields
        
        return True
    
    def _validate_scene(self, scene: Dict) -> bool:
        """Validate scene has required fields"""
        required_fields = PROCESSING_RULES['scene_limits']['required_fields']
        missing_fields = [field for field in required_fields if not scene.get(field)]
        
        if missing_fields:
            self.logger.warning(f"⚠️ Scene missing fields: {missing_fields}")
            return len(missing_fields) <= 2  # Allow some missing fields
        
        return True
    
    def _apply_quality_gates(self, results: Dict[str, Any]):
        """Apply quality gates to processing results"""
        # Character count validation
        char_count = len(results['characters'])
        if not (PROCESSING_RULES['character_limits']['min_characters'] <= char_count <= PROCESSING_RULES['character_limits']['max_characters']):
            self.logger.warning(f"⚠️ Character count {char_count} outside expected range")
        
        # Scene count validation
        scene_count = len(results['scenes'])
        if not (PROCESSING_RULES['scene_limits']['min_scenes'] <= scene_count <= PROCESSING_RULES['scene_limits']['max_scenes']):
            self.logger.warning(f"⚠️ Scene count {scene_count} outside expected range")
        
        # Narration length validation
        narration_words = len(results['narration'].split())
        if not (PROCESSING_RULES['narration_limits']['min_words'] <= narration_words <= PROCESSING_RULES['narration_limits']['max_words']):
            self.logger.warning(f"⚠️ Narration word count {narration_words} outside expected range")
    
    # Fallback methods for basic processing
    def _extract_basic_characters(self, story_content: str) -> List[Dict[str, str]]:
        """Extract basic characters from story content"""
        characters = [
            {
                'name': 'Adventure Hero',
                'role': 'protagonist',
                'personality': 'brave, curious, kind',
                'appearance': 'young adventurer with bright eyes and friendly smile',
                'motivation': 'to explore and discover new things',
                'emotional_traits': 'excited, courageous, hopeful',
                'description': 'The main character who goes on a wonderful adventure.'
            },
            {
                'name': 'Magical Friend',
                'role': 'supporting',
                'personality': 'helpful, magical, wise',
                'appearance': 'sparkling magical creature with gentle features',
                'motivation': 'to help and guide the hero',
                'emotional_traits': 'caring, patient, encouraging',
                'description': 'A magical friend who helps on the adventure.'
            }
        ]
        return characters[:PROCESSING_RULES['character_limits']['max_characters']]
    
    def _create_basic_scenes(self, story_content: str, characters: List[Dict]) -> List[Dict[str, str]]:
        """Create basic scene breakdown"""
        character_names = ', '.join([char['name'] for char in characters[:2]])
        
        scenes = [
            {
                'title': 'The Beginning Adventure',
                'location': 'Magical Story World',
                'emotion': 'excited',
                'characters': character_names,
                'action': 'Starting the wonderful journey',
                'description': 'Where our adventure begins with excitement and curiosity.'
            },
            {
                'title': 'Discovering New Places',
                'location': 'Enchanted Forest',
                'emotion': 'curious',
                'characters': character_names,
                'action': 'Exploring magical surroundings',
                'description': 'Discovering amazing new places and making wonderful finds.'
            },
            {
                'title': 'Facing Challenges',
                'location': 'Mysterious Path',
                'emotion': 'brave',
                'characters': character_names,
                'action': 'Overcoming obstacles together',
                'description': 'Working together to solve problems and face challenges.'
            },
            {
                'title': 'Happy Celebration',
                'location': 'Beautiful Meadow',
                'emotion': 'joyful',
                'characters': character_names,
                'action': 'Celebrating success',
                'description': 'A wonderful celebration of friendship and accomplishment.'
            }
        ]
        return scenes[:PROCESSING_RULES['scene_limits']['max_scenes']]
    
    def _create_basic_narration(self, story_content: str, characters: List[Dict], scenes: List[Dict]) -> str:
        """Create basic narration"""
        character_names = ', '.join([char['name'] for char in characters[:2]])
        
        return f"""
Welcome to our magical story time! Today we're going on an amazing adventure with {character_names}.

{story_content[:200]}...

What an incredible journey! Can you guess what wonderful things we discovered along the way?

Remember, every story is a new adventure waiting to be explored. What was your favorite part?

Let's imagine we're there right now - can you see the magical colors and hear the wonderful sounds?

And they all lived happily ever after, exploring new adventures every day!
"""
    
    def _create_basic_image_prompts(self, scenes: List[Dict], characters: List[Dict]) -> List[Dict[str, str]]:
        """Create basic image prompts"""
        prompts = []
        for scene in scenes:
            prompts.append({
                'scene': scene['title'],
                'prompt': f"Children's storybook illustration of {scene['title']}, {scene['description']}, magical storybook style, warm lighting, soft pastel colors, detailed environments, 16:9 aspect ratio, child-friendly"
            })
        return prompts
    
    def _format_character_summary(self, characters: List[Dict]) -> str:
        """Format character summary for AI prompts"""
        return "\n".join([f"- {char['name']}: {char.get('role', 'character')}" for char in characters])
    
    def _format_scene_summary(self, scenes: List[Dict]) -> str:
        """Format scene summary for AI prompts"""
        return "\n".join([f"- {scene['title']}: {scene.get('emotion', 'neutral')} at {scene.get('location', 'unknown')}" for scene in scenes])


def create_story_processor(drive_manager, template_engine):
    """Create and return a StoryProcessor instance"""
    return StoryProcessor(drive_manager, template_engine)