"""
Main Orchestrator - Story Automation System
Coordinates the entire pipeline from story input to generated content
"""

import logging
import time
import sys
import os
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add the current directory to Python path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    validate_config,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    generate_output_folder_name,
    get_output_folder_path
)
from gdrive_manager import get_drive_manager
from story_processor import create_story_processor
from template_engine import create_template_engine

class StoryAutomationOrchestrator:
    """Main orchestrator that coordinates the entire story automation pipeline"""
    
    def __init__(self):
        """Initialize the orchestrator with all components"""
        self.logger = self._setup_logging()
        self.drive_manager = None
        self.story_processor = None
        self.template_engine = None
        self.folder_ids = None
        self.processing_start_time = None
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
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
            self.logger.info(" Initializing Story Automation System...")
            
            # Validate configuration first
            self.logger.info(" Validating configuration...")
            config_valid, config_error = validate_config()
            if not config_valid:
                raise ValueError(f"Configuration error: {config_error}")
            
            # Initialize Google Drive manager
            self.logger.info(" Initializing Google Drive manager...")
            self.drive_manager = get_drive_manager()
            
            # Initialize template engine
            self.logger.info(" Initializing template engine...")
            self.template_engine = create_template_engine()
            
            # Initialize story processor
            self.logger.info("烙 Initializing story processor...")
            self.story_processor = create_story_processor(
                self.drive_manager, 
                self.template_engine
            )
            
            # Get or create folder structure
            self.logger.info(" Setting up directory structure...")
            self.folder_ids = self.drive_manager.get_folder_ids()
            
            self.logger.info("✅ System initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def check_story_input(self):
        """Check if story input file exists and has content"""
        try:
            self.logger.info(" Checking story input file...")
            
            story_content = self.drive_manager.read_input_file(
                "story_input.txt", 
                self.folder_ids
            )
            
            if not story_content:
                self.logger.error("❌ Story input file is empty or not found")
                return False
            
            # Basic validation - at least 100 characters
            if len(story_content.strip()) < 100:
                self.logger.warning("⚠️ Story input seems very short. Minimum 100 characters recommended.")
            
            self.logger.info(f"✅ Story input found ({len(story_content)} characters)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking story input: {e}")
            return False
    
    def create_output_folder(self, story_title):
        """Create output folder for this story generation"""
        try:
            self.logger.info(" Creating output folder...")
            
            output_folder_name = generate_output_folder_name(story_title)
            output_folder_id = self.drive_manager.create_folder(
                output_folder_name,
                self.folder_ids['output_folder_id']
            )
            
            if not output_folder_id:
                raise Exception("Failed to create output folder")
            
            self.logger.info(f"✅ Output folder created: {output_folder_name}")
            return output_folder_id
            
        except Exception as e:
            self.logger.error(f"❌ Error creating output folder: {e}")
            raise
    
    def process_story_pipeline(self):
        """Execute the complete story processing pipeline"""
        try:
            self.processing_start_time = time.time()
            self.logger.info(" Starting story processing pipeline...")
            
            # Step 1: Process story and generate content
            self.logger.info(" Step 1/4: Processing story content...")
            processing_results = self.story_processor.process_story(self.folder_ids)
            
            story_title = processing_results['story_title']
            self.logger.info(f" Processing story: '{story_title}'")
            
            # Step 2: Create output folder
            self.logger.info(" Step 2/4: Creating output folder...")
            output_folder_id = self.create_output_folder(story_title)
            
            # Step 3: Generate formatted outputs
            self.logger.info(" Step 3/4: Generating output files...")
            processing_time = time.time() - self.processing_start_time
            output_files = self.template_engine.generate_all_outputs(
                processing_results, 
                processing_time
            )
            
            # Step 4: Write output files to Google Drive
            self.logger.info(" Step 4/4: Writing output files...")
            files_written = self.write_output_files(output_files, output_folder_id)
            
            # Calculate final processing time
            total_processing_time = time.time() - self.processing_start_time
            
            self.logger.info(SUCCESS_MESSAGES['pipeline_complete'])
            self.logger.info(f"⏱️ Total processing time: {total_processing_time:.2f} seconds")
            self.logger.info(f" Files generated: {files_written}/{len(output_files)}")
            
            return {
                'success': True,
                'story_title': story_title,
                'output_folder_id': output_folder_id,
                'files_written': files_written,
                'total_files': len(output_files),
                'processing_time': total_processing_time,
                'output_files': list(output_files.keys())
            }
            
        except Exception as e:
            self.logger.error(f"❌ Story processing pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - self.processing_start_time if self.processing_start_time else 0
            }
    
    def write_output_files(self, output_files, output_folder_id):
        """Write all output files to Google Drive"""
        try:
            files_written = 0
            
            for filename, content in output_files.items():
                self.logger.info(f" Writing {filename}...")
                
                success = self.drive_manager.write_output_file(
                    content,
                    filename,
                    output_folder_id
                )
                
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
        """Generate a summary report of the processing run"""
        try:
            if result['success']:
                report = f"""
 STORY AUTOMATION COMPLETED SUCCESSFULLY 
============================================

 Story: {result['story_title']}
⏱️ Processing Time: {result['processing_time']:.2f} seconds
 Files Generated: {result['files_written']}/{result['total_files']}
 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

 OUTPUT FILES:
----------------
{chr(10).join([f"✅ {file}" for file in result['output_files']])}

 NEXT STEPS:
--------------
1. Check the output folder in Google Drive
2. Use image prompts with your AI image generator
3. Create video with the generated narration
4. Upload to your YouTube channel

 Output Folder: Look for the new folder in your Google Drive '(out)' directory

---
Story Automation System - Powered by AI
"""
            else:
                report = f"""
❌ STORY AUTOMATION FAILED
=========================

⏱️ Processing Time: {result['processing_time']:.2f} seconds
 Failed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

 ERROR:
---------
{result['error']}

 TROUBLESHOOTING:
-------------------
1. Check that story_input.txt contains valid story content
2. Verify Google Drive folder permissions
3. Check internet connection
4. Review the log file for detailed errors

---
Story Automation System - Need Help?
"""
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating summary report: {e}")
            return "Summary report generation failed."

def main():
    """Main function to run the story automation system"""
    orchestrator = StoryAutomationOrchestrator()
    
    print("\n" + "="*60)
    print("        STORY AUTOMATION SYSTEM")
    print("="*60)
    
    try:
        # Initialize system
        if not orchestrator.initialize_system():
            print("❌ System initialization failed. Please check the logs.")
            return 1
        
        # Check story input
        if not orchestrator.check_story_input():
            print("❌ No story input found. Please add your story to story_input.txt in Google Drive.")
            return 1
        
        print("✅ System ready! Starting story processing...")
        print("⏳ This may take a few minutes...")
        
        # Run the pipeline
        result = orchestrator.process_story_pipeline()
        
        # Display results
        summary = orchestrator.generate_summary_report(result)
        print(summary)
        
        if result['success']:
            print(" Story automation completed successfully!")
            return 0
        else:
            print("❌ Story automation failed. Please check the logs for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    # Run the main function and exit with appropriate code
    exit_code = main()
    
    print("\n" + "="*60)
    if exit_code == 0:
        print("✅ Story Automation System - COMPLETED")
    else:
        print("❌ Story Automation System - FAILED")
    print("="*60)
    
    sys.exit(exit_code)