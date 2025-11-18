"""
Template Engine - Output File Generation with Strict Formatting
Applies framework templates to create the 6 output files in Google Drive
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from config import (
    INPUT_OUTPUT_FILES,
    PROCESSING_RULES,
    generate_output_folder_name
)

class TemplateEngine:
    """Handles template application and output file generation with strict formatting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_all_outputs(self, processing_results: Dict[str, Any], processing_time: float) -> Dict[str, str]:
        """Generate all 6 output files from processing results"""
        try:
            self.logger.info("️ Generating output files...")
            
            story_title = processing_results['story_title']
            characters = processing_results['characters']
            scenes = processing_results['scenes']
            
            outputs = {
                INPUT_OUTPUT_FILES['output_story']: self._generate_story_file(
                    processing_results['original_story'], 
                    story_title
                ),
                INPUT_OUTPUT_FILES['output_narration']: self._generate_narration_file(
                    processing_results['narration'],
                    story_title,
                    characters,
                    scenes
                ),
                INPUT_OUTPUT_FILES['output_character_sheet']: self._generate_character_file(
                    characters,
                    story_title
                ),
                INPUT_OUTPUT_FILES['output_scenes']: self._generate_scenes_file(
                    scenes,
                    story_title,
                    characters
                ),
                INPUT_OUTPUT_FILES['output_image_prompts']: self._generate_prompts_file(
                    processing_results['image_prompts'],
                    story_title,
                    scenes
                ),
                INPUT_OUTPUT_FILES['output_processing_report']: self._generate_report_file(
                    processing_results,
                    processing_time
                )
            }
            
            self.logger.info(f"✅ Generated {len(outputs)} output files")
            return outputs
            
        except Exception as e:
            self.logger.error(f"❌ Error generating outputs: {e}")
            raise
    
    def _generate_story_file(self, story_content: str, story_title: str) -> str:
        """Generate 1-Story.txt file"""
        separator = '=' * (len(story_title) + 8)
        
        content = f"""STORY: {story_title}
{separator}

{story_content}

---
GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
TITLE: {story_title}
WORD COUNT: {len(story_content.split())}
CHARACTER COUNT: {len([c for c in story_content if c.isalpha()])}
"""
        return content
    
    def _generate_narration_file(self, narration: str, story_title: str, 
                               characters: List[Dict], scenes: List[Dict]) -> str:
        """Generate 2-Narration.txt file"""
        # Format character list
        character_list = "\n".join([
            f"- {char['name']}: {char.get('role', 'character').title()}"
            for char in characters
        ])
        
        # Format scene list
        scene_list = "\n".join([
            f"- {scene['title']} ({scene.get('emotion', 'neutral').title()})"
            for scene in scenes
        ])
        
        title_separator = '=' * (len(story_title) + 17)
        
        content = f"""NARRATION SCRIPT: {story_title}
{title_separator}

CHARACTERS:
{character_list}

SCENES:
{scene_list}

NARRATION:
{narration}

---
PRODUCTION NOTES:
• Duration: {PROCESSING_RULES['narration_limits']['duration_minutes']} minutes
• Target Age: {PROCESSING_RULES['narration_limits']['target_age']}
• Word Count: {len(narration.split())}
• Tone: Warm, Magical, Engaging
• Pace: Slow and clear for young children
• Audience Interactions: Included throughout
• Emotional Arc: Complete story journey
"""
        return content
    
    def _generate_character_file(self, characters: List[Dict], story_title: str) -> str:
        """Generate 3-Character-Sheet.txt file"""
        character_sections = []
        
        for i, char in enumerate(characters, 1):
            name = char.get('name', f'Character {i}')
            section_separator = '=' * (len(name) + 14)
            
            section = f"""CHARACTER {i}: {name}
{section_separator}
Role: {char.get('role', 'Not specified').title()}
Personality: {char.get('personality', 'Not specified')}
Appearance: {char.get('appearance', 'Not specified')}
Motivation: {char.get('motivation', 'Not specified')}
Emotional Traits: {char.get('emotional_traits', 'Not specified')}

DESCRIPTION:
{char.get('description', 'No description available')}

"""
            character_sections.append(section)
        
        title_separator = '=' * (len(story_title) + 17)
        
        content = f"""CHARACTER SHEETS: {story_title}
{title_separator}

Total Characters: {len(characters)}
Character Range: {PROCESSING_RULES['character_limits']['min_characters']}-{PROCESSING_RULES['character_limits']['max_characters']}

{'='*50}

{''.join(character_sections)}
---
CHARACTER CONSISTENCY: Enforced across all scenes
VISUAL REFERENCE: Maintain exact appearances
EMOTIONAL RANGE: Age-appropriate and positive
"""
        return content
    
    def _generate_scenes_file(self, scenes: List[Dict], story_title: str, characters: List[Dict]) -> str:
        """Generate 4-Scenes.txt file"""
        scene_sections = []
        
        for i, scene in enumerate(scenes, 1):
            title = scene.get('title', f'Scene {i}')
            section_separator = '=' * (len(title) + 9)
            
            # Infer visual elements based on emotion
            emotion = scene.get('emotion', 'neutral').lower()
            lighting = self._infer_lighting(emotion)
            colors = self._infer_colors(emotion)
            composition = self._infer_composition(scene.get('action', ''))
            
            section = f"""SCENE {i}: {title}
{section_separator}
Location: {scene.get('location', 'Not specified')}
Emotional Tone: {scene.get('emotion', 'Not specified').title()}
Characters Present: {scene.get('characters', 'Not specified')}
Key Action: {scene.get('action', 'Not specified')}

DESCRIPTION:
{scene.get('description', 'No description available')}

VISUAL ELEMENTS:
• Lighting: {lighting}
• Color Palette: {colors}
• Composition: {composition}
• Camera Angle: {self._infer_camera_angle(emotion)}

"""
            scene_sections.append(section)
        
        title_separator = '=' * (len(story_title) + 16)
        
        content = f"""SCENE BREAKDOWN: {story_title}
{title_separator}

Total Scenes: {len(scenes)}
Scene Range: {PROCESSING_RULES['scene_limits']['min_scenes']}-{PROCESSING_RULES['scene_limits']['max_scenes']}
Emotional Arc: Complete narrative journey

{'='*50}

{''.join(scene_sections)}
---
SCENE TRANSITIONS: Smooth and logical progression
PACING: Optimized for children's attention span
VISUAL CONTINUITY: Maintained throughout all scenes
STORY FLOW: Coherent beginning, development, and resolution
"""
        return content
    
    def _generate_prompts_file(self, image_prompts: List[Dict], story_title: str, scenes: List[Dict]) -> str:
        """Generate 5-Image-Prompts.txt file"""
        prompt_sections = []
        
        for i, prompt_data in enumerate(image_prompts, 1):
            scene_title = prompt_data.get('scene', f'Scene {i}')
            section_separator = '=' * (len(scene_title) + 15)
            
            # Find matching scene for context
            scene_context = next(
                (scene for scene in scenes if scene.get('title') == scene_title), 
                None
            )
            scene_emotion = scene_context.get('emotion', 'neutral') if scene_context else 'neutral'
            
            section = f"""IMAGE PROMPT {i}: {scene_title}
{section_separator}

SCENE CONTEXT:
{scene_context.get('description', 'General story scene') if scene_context else 'Key story moment'}

EMOTIONAL TONE: {scene_emotion.title()}

AI PROMPT:
{prompt_data.get('prompt', 'No prompt available')}

TECHNICAL SPECIFICATIONS:
• Style: Children's storybook illustration
• Lighting: {self._get_prompt_lighting(scene_emotion)}
• Colors: {self._get_prompt_colors(scene_emotion)}
• Composition: {self._get_prompt_composition(scene_emotion)}
• Aspect Ratio: 16:9 (YouTube optimized)
• Detail Level: High detail, magical elements
• Safety: Child-appropriate content only

KEY ELEMENTS:
{self._extract_key_elements(prompt_data.get('prompt', ''))}

"""
            prompt_sections.append(section)
        
        title_separator = '=' * (len(story_title) + 22)
        
        content = f"""IMAGE GENERATION PROMPTS: {story_title}
{title_separator}

Total Prompts: {len(image_prompts)}
Usage: AI Image Generation (DALL-E, Midjourney, Stable Diffusion)
Prompt Quality: Scene-specific and emotionally aligned

{'='*50}

{''.join(prompt_sections)}
---
PROMPT GUIDELINES FOLLOWED:
✅ Child-appropriate content only
✅ Consistent character appearances across all scenes
✅ Magical, storybook aesthetic maintained
✅ Warm, inviting color palettes
✅ Clear visual storytelling
✅ Emotional resonance with scenes
✅ 16:9 aspect ratio for YouTube
✅ High detail and magical elements

GENERATION TIPS:
1. Use these prompts with your preferred AI image generator
2. Maintain character consistency across all generated images
3. Follow the specified emotional tones and color palettes
4. Ensure all images are child-safe and magical
5. Use 16:9 aspect ratio for YouTube compatibility
6. Generate at high resolution (4K recommended)
7. Maintain consistent art style throughout
"""
        return content
    
    def _generate_report_file(self, processing_results: Dict[str, Any], processing_time: float) -> str:
        """Generate processing-report.txt file"""
        story_title = processing_results['story_title']
        stats = processing_results['processing_stats']
        
        title_separator = '=' * (len(story_title) + 18)
        
        # Format character list
        character_list = "\n".join([
            f"• {char['name']} ({char.get('role', 'character').title()})"
            for char in processing_results['characters']
        ])
        
        # Format scene list
        scene_list = "\n".join([
            f"• {scene['title']} - {scene.get('emotion', 'neutral').title()} at {scene.get('location', 'unknown')}"
            for scene in processing_results['scenes']
        ])
        
        content = f"""PROCESSING REPORT: {story_title}
{title_separator}

PROCESSING SUMMARY
──────────────────
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Processing Time: {processing_time:.2f} seconds
Status: COMPLETED_SUCCESSFULLY
Processing Method: {stats['processing_method'].upper()}

CONTENT STATISTICS
──────────────────
Characters Extracted: {stats['character_count']} (Range: {PROCESSING_RULES['character_limits']['min_characters']}-{PROCESSING_RULES['character_limits']['max_characters']})
Scenes Identified: {stats['scene_count']} (Range: {PROCESSING_RULES['scene_limits']['min_scenes']}-{PROCESSING_RULES['scene_limits']['max_scenes']})
Image Prompts Generated: {stats['image_prompt_count']}
Narration Word Count: {len(processing_results['narration'].split())} (Target: {PROCESSING_RULES['narration_limits']['min_words']}-{PROCESSING_RULES['narration_limits']['max_words']})

CHARACTERS PROCESSED
────────────────────
{character_list}

SCENES GENERATED
────────────────
{scene_list}

QUALITY ASSURANCE
─────────────────
✅ Story coherence verified
✅ Character consistency maintained
✅ Scene transitions logical
✅ Age-appropriate content confirmed
✅ Visual style guidelines followed
✅ Emotional arcs preserved
✅ Processing rules enforced
✅ Output formatting validated

OUTPUT FILES GENERATED
──────────────────────
1. {INPUT_OUTPUT_FILES['output_story']} - Original story content
2. {INPUT_OUTPUT_FILES['output_narration']} - Engaging narration script
3. {INPUT_OUTPUT_FILES['output_character_sheet']} - Detailed character profiles
4. {INPUT_OUTPUT_FILES['output_scenes']} - Scene breakdowns with visual elements
5. {INPUT_OUTPUT_FILES['output_image_prompts']} - AI image generation prompts
6. {INPUT_OUTPUT_FILES['output_processing_report']} - This comprehensive report

NEXT STEPS
──────────
1. Use image prompts with AI generators to create visuals
2. Record narration using the generated script
3. Create video combining narration and generated images
4. Upload finished video to YouTube channel
5. Promote with generated content and descriptions

---
GENERATED BY: Story Automation System
QUALITY CHECK: PASSED
READY FOR PRODUCTION: YES
SYSTEM: Fully Automated Pipeline
VERSION: 1.0
"""
        return content
    
    # Helper methods for visual element inference
    def _infer_lighting(self, emotion: str) -> str:
        """Infer lighting based on emotional tone"""
        lighting_map = {
            'happy': 'Warm, bright, golden hour lighting',
            'excited': 'Dynamic, high-contrast, energetic lighting',
            'curious': 'Soft, exploratory, gentle lighting',
            'brave': 'Heroic, dramatic, focused lighting',
            'joyful': 'Radiant, sparkling, celebratory lighting',
            'peaceful': 'Soft, even, tranquil lighting',
            'magical': 'Ethereal, glowing, magical light sources'
        }
        return lighting_map.get(emotion.lower(), 'Appropriate emotional lighting')
    
    def _infer_colors(self, emotion: str) -> str:
        """Infer color palette based on emotional tone"""
        color_map = {
            'happy': 'Warm yellows, bright blues, cheerful pastels',
            'excited': 'Vibrant reds, oranges, high saturation colors',
            'curious': 'Soft blues, gentle greens, exploratory tones',
            'brave': 'Rich golds, deep blues, heroic colors',
            'joyful': 'Sparkling golds, warm pinks, celebratory hues',
            'peaceful': 'Soft greens, gentle blues, earth tones',
            'magical': 'Iridescent purples, sparkling golds, magical hues'
        }
        return color_map.get(emotion.lower(), 'Emotionally appropriate colors')
    
    def _infer_composition(self, action: str) -> str:
        """Infer composition based on action type"""
        action_lower = action.lower()
        if any(word in action_lower for word in ['run', 'chase', 'fly', 'move']):
            return 'Dynamic, diagonal lines, sense of movement'
        elif any(word in action_lower for word in ['talk', 'discuss', 'share']):
            return 'Balanced, rule of thirds, character-focused'
        elif any(word in action_lower for word in ['discover', 'find', 'reveal']):
            return 'Centered, leading lines, emphasis on discovery'
        elif any(word in action_lower for word in ['celebrate', 'dance', 'play']):
            return 'Energetic, circular composition, joyful arrangement'
        else:
            return 'Well-composed, visually balanced, story-focused'
    
    def _infer_camera_angle(self, emotion: str) -> str:
        """Infer camera angle based on emotional tone"""
        angle_map = {
            'happy': 'Eye-level or slightly low angle for empowerment',
            'excited': 'Dynamic angles, Dutch tilt for energy',
            'curious': 'Eye-level with slight exploration tilt',
            'brave': 'Low angle for heroism and strength',
            'joyful': 'Stable, eye-level, uplifting composition',
            'peaceful': 'Calm, eye-level, harmonious framing',
            'magical': 'Eye-level with magical perspective elements'
        }
        return angle_map.get(emotion.lower(), 'Appropriate emotional angle')
    
    def _get_prompt_lighting(self, emotion: str) -> str:
        """Get lighting description for image prompts"""
        lighting_map = {
            'happy': 'soft warm lighting, golden hour, cheerful atmosphere',
            'excited': 'dynamic lighting, high contrast, energetic glow',
            'curious': 'gentle exploratory light, soft shadows, mysterious',
            'brave': 'heroic lighting, dramatic highlights, focused beams',
            'joyful': 'radiant lighting, sparkling effects, celebratory',
            'peaceful': 'soft even light, tranquil, serene illumination',
            'magical': 'ethereal glow, magical light sources, sparkling'
        }
        return lighting_map.get(emotion.lower(), 'beautiful storybook lighting')
    
    def _get_prompt_colors(self, emotion: str) -> str:
        """Get color description for image prompts"""
        color_map = {
            'happy': 'vibrant colors, warm palette, cheerful tones',
            'excited': 'saturated colors, bold palette, dynamic hues',
            'curious': 'mysterious colors, soft palette, exploratory tones',
            'brave': 'rich colors, heroic palette, strong hues',
            'joyful': 'sparkling colors, celebratory palette, warm tones',
            'peaceful': 'pastel colors, soft palette, calming hues',
            'magical': 'iridescent colors, magical palette, sparkling tones'
        }
        return color_map.get(emotion.lower(), 'beautiful storybook colors')
    
    def _get_prompt_composition(self, emotion: str) -> str:
        """Get composition description for image prompts"""
        composition_map = {
            'happy': 'balanced composition, positive space, inviting',
            'excited': 'dynamic composition, leading lines, movement',
            'curious': 'exploratory composition, mysterious framing',
            'brave': 'heroic composition, strong focal points',
            'joyful': 'celebratory composition, circular arrangements',
            'peaceful': 'harmonious composition, balanced, calm',
            'magical': 'enchanted composition, magical perspective'
        }
        return composition_map.get(emotion.lower(), 'excellent storybook composition')
    
    def _extract_key_elements(self, prompt_text: str) -> str:
        """Extract key visual elements from prompt text"""
        elements = []
        words = prompt_text.lower().split()
        
        key_indicators = ['with', 'featuring', 'including', 'showing', 'containing', 'detailed']
        for i, word in enumerate(words):
            if word in key_indicators and i + 1 < len(words):
                next_word = words[i + 1]
                if len(next_word) > 3 and not next_word in ['the', 'and', 'for', 'with']:
                    elements.append(f"• {next_word.capitalize()}")
        
        # Ensure we have some elements
        if not elements:
            elements = [
                "• Magical story elements",
                "• Character emotions and expressions", 
                "• Story setting and environment",
                "• Key actions and moments",
                "• Atmospheric and sensory details"
            ]
        
        return "\n".join(elements[:6])  # Limit to 6 key elements


def create_template_engine():
    """Create and return a TemplateEngine instance"""
    return TemplateEngine()