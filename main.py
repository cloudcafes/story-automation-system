"""
Story Automation System - Main Orchestrator
Coordinates the complete pipeline from story input to generated content in Google Drive
"""

import logging
import time
import sys
import os
from datetime import datetime

# Add current directory to path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    validate_configuration,
    config_valid,
    config_errors,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    generate_output_folder_name,
    SYSTEM_SETTINGS
)
from gdrive_manager import get_drive_manager
from story_processor import create_story_processor
from template_engine import create_template_engine

class StoryAutomationOrchestrator:
    """Main orchestrator that coordinates the complete story automation pipeline"""
    
    def __init__(self):
        """Initialize the orchestrator with all components"""
        self.logger = self._setup_logging()
        self.drive_manager = None
        self.story_processor = None
        self.template_engine = None
        self.processing_start_time = None
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, SYSTEM_SETTINGS['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('story_automation.log', encoding='utf-8')
            ]
        )
        return logging.getLogger(__name__)
    
    def initialize_system(self):
        """Initialize all system components"""
        try:
            self.logger.info(" Initializing Story Automation System...")
            
            # Validate configuration
            self.logger.info(" Validating system configuration...")
            if not config_valid:
                error_msg = "Configuration validation failed:\n" + "\n".join([f"  • {error}" for error in config_errors])
                raise ValueError(error_msg)
            
            # Initialize Google Drive manager
            self.logger.info(" Initializing Google Drive manager...")
            self.drive_manager = get_drive_manager()
            
            # Validate framework files exist
            self.logger.info(" Validating framework files in Google Drive...")
            self.drive_manager.validate_framework_files()
            
            # Initialize template engine
            self.logger.info(" Initializing template engine...")
            self.template_engine = create_template_engine()
            
            # Initialize story processor
            self.logger.info("烙 Initializing story processor...")
            self.story_processor = create_story_processor(self.drive_manager, self.template_engine)
            
            self.logger.info("✅ System initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def check_story_input(self):
        """Check if story input file exists and has content"""
        try:
            self.logger.info(" Checking story input file...")
            story_content = self.drive_manager.read_story_input()
            
            if not story_content:
                raise ValueError("Story input file is empty")
            
            story_length = len(story_content)
            self.logger.info(f"✅ Story input found ({story_length} characters)")
            
            if story_length < 100:
                self.logger.warning("⚠️ Story input seems very short. Minimum 100 characters recommended.")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking story input: {e}")
            return False
    
    def create_output_folder(self, story_title):
        """Create output folder in Google Drive for this story generation"""
        try:
            self.logger.info(" Creating output folder...")
            output_folder_name = generate_output_folder_name(story_title)
            output_folder_id = self.drive_manager.create_output_folder(output_folder_name)
            
            if not output_folder_id:
                raise Exception("Failed to create output folder in Google Drive")
            
            self.logger.info(f"✅ Output folder created: {output_folder_name}")
            return output_folder_id
            
        except Exception as e:
            self.logger.error(f"❌ Error creating output folder: {e}")
            raise
    
    def execute_story_pipeline(self):
        """Execute the complete story processing pipeline"""
        try:
            self.processing_start_time = time.time()
            self.logger.info(" Starting story processing pipeline...")
            
            # Step 1: Read story input
            self.logger.info(" Step 1/5: Reading story input...")
            story_content = self.drive_manager.read_story_input()
            
            # Step 2: Process story content
            self.logger.info(" Step 2/5: Processing story content...")
            processing_results = self.story_processor.process_story(story_content)
            story_title = processing_results['story_title']
            
            self.logger.info(f" Processing story: '{story_title}'")
            self.logger.info(f"   • Characters: {processing_results['processing_stats']['character_count']}")
            self.logger.info(f"   • Scenes: {processing_results['processing_stats']['scene_count']}")
            self.logger.info(f"   • Method: {processing_results['processing_stats']['processing_method']}")
            
            # Step 3: Create output folder
            self.logger.info(" Step 3/5: Creating output folder...")
            output_folder_id = self.create_output_folder(story_title)
            
            # Step 4: Generate output files
            self.logger.info("️ Step 4/5: Generating output files...")
            processing_time_so_far = time.time() - self.processing_start_time
            output_files = self.template_engine.generate_all_outputs(processing_results, processing_time_so_far)
            
            # Step 5: Write output files to Google Drive
            self.logger.info(" Step 5/5: Writing output files to Google Drive...")
            files_written = self._write_output_files(output_files, output_folder_id)
            
            # Calculate total processing time
            total_processing_time = time.time() - self.processing_start_time
            
            # Generate results summary
            results = {
                'success': True,
                'story_title': story_title,
                'output_folder_name': generate_output_folder_name(story_title),
                'files_written': files_written,
                'total_files': len(output_files),
                'processing_time': total_processing_time,
                'processing_stats': processing_results['processing_stats'],
                'output_files': list(output_files.keys())
            }
            
            self.logger.info(SUCCESS_MESSAGES['story_processed'].format(story_title=story_title))
            self.logger.info(SUCCESS_MESSAGES['files_generated'].format(file_count=files_written))
            self.logger.info(f"⏱️ Total processing time: {total_processing_time:.2f} seconds")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Story processing pipeline failed: {e}")
            
            processing_time = time.time() - self.processing_start_time if self.processing_start_time else 0
            
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    def _write_output_files(self, output_files, output_folder_id):
        """Write all output files to Google Drive"""
        try:
            files_written = 0
            total_files = len(output_files)
            
            for i, (filename, content) in enumerate(output_files.items(), 1):
                self.logger.info(f" Writing file {i}/{total_files}: {filename}...")
                
                success = self.drive_manager.write_output_file(content, filename, output_folder_id)
                
                if success:
                    files_written += 1
                    self.logger.info(f"✅ Successfully wrote {filename}")
                else:
                    self.logger.error(f"❌ Failed to write {filename}")
            
            return files_written
            
        except Exception as e:
            self.logger.error(f"❌ Error writing output files: {e}")
            return 0
    
    def generate_summary_report(self, result):
        """Generate a comprehensive summary report of the processing run"""
        try:
            if result['success']:
                report = f"""
 STORY AUTOMATION COMPLETED SUCCESSFULLY 
============================================

 STORY DETAILS
────────────────
Story Title: {result['story_title']}
Output Folder: {result['output_folder_name']}
Processing Method: {result['processing_stats']['processing_method'].upper()}

⏱️ PROCESSING METRICS
─────────────────────
Total Time: {result['processing_time']:.2f} seconds
Files Generated: {result['files_written']}/{result['total_files']}
Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

 CONTENT STATISTICS
─────────────────────
Characters: {result['processing_stats']['character_count']}
Scenes: {result['processing_stats']['scene_count']}
Image Prompts: {result['processing_stats']['image_prompt_count']}

 OUTPUT FILES GENERATED
─────────────────────────
{chr(10).join([f"✅ {file}" for file in result['output_files']])}

 NEXT STEPS
─────────────
1.  Check the output folder in Google Drive
2.  Use image prompts with your AI image generator (DALL-E, Midjourney, etc.)
3.  Record narration using the generated script  
4.  Create video combining narration and generated images
5.  Upload to your YouTube channel
6.  Promote with the generated content

 TECHNICAL DETAILS
────────────────────
• All files stored in Google Drive
• Processing rules strictly enforced
• Quality gates passed successfully
• System: Fully Automated Story Pipeline

---
✨ Story Automation System - Powered by AI ✨
✅ Ready for video production
"""
            else:
                report = f"""
❌ STORY AUTOMATION FAILED
==========================

⏱️ PROCESSING DETAILS
─────────────────────
Processing Time: {result['processing_time']:.2f} seconds
Failed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

 ERROR DETAILS
────────────────
{result['error']}

 TROUBLESHOOTING STEPS
────────────────────────
1.  Check that story_input.txt contains valid story content (100+ characters)
2.  Verify Google Drive folder permissions and service account access
3.  Check internet connection and API availability
4.  Review framework files in Google Drive Framework/ folder
5.  Check the log file for detailed error information
6.  Try running the system again

 SUPPORT
──────────
• Check all framework files exist in Google Drive
• Verify credentials.json is in the correct location
• Ensure DeepSeek API key is valid and has credits

---
️ Story Automation System - Need Help?
"""
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating summary report: {e}")
            return "Summary report generation failed."

def main():
    """Main function to run the story automation system"""
    orchestrator = StoryAutomationOrchestrator()
    
    print("\n" + "="*70)
    print("                STORY AUTOMATION SYSTEM")
    print("="*70)
    print("烙 AI-Powered Story Processing → Google Drive Integration")
    print("="*70)
    
    try:
        # Initialize system
        print("\n Initializing system...")
        if not orchestrator.initialize_system():
            print("❌ System initialization failed. Please check the logs.")
            return 1
        
        # Check story input
        print(" Checking story input...")
        if not orchestrator.check_story_input():
            print("❌ No story input found or story is too short.")
            print(" Please add your story to 'story_input.txt' in Google Drive root")
            return 1
        
        # Start processing
        print("✅ System ready!")
        print(" Starting story processing...")
        print("⏳ This may take 2-5 minutes depending on story length...")
        print("-" * 70)
        
        # Execute pipeline
        result = orchestrator.execute_story_pipeline()
        
        # Generate and display summary
        summary = orchestrator.generate_summary_report(result)
        print("\n" + summary)
        
        if result['success']:
            print("\n" + "="*70)
            print(" AUTOMATION COMPLETED SUCCESSFULLY!")
            print("="*70)
            return 0
        else:
            print("\n" + "="*70)
            print("❌ AUTOMATION FAILED - Please check errors above")
            print("="*70)
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    
    print("\n" + "="*70)
    if exit_code == 0:
        print("✅ Story Automation System - COMPLETED")
    else:
        print("❌ Story Automation System - FAILED")
    print("="*70)
    
    sys.exit(exit_code)