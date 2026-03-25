import os
import time
from typing import Optional, Dict, Any
from runwayml import RunwayML
from dotenv import load_dotenv

load_dotenv()

class RunwayMLClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RUNWAYML_API_KEY")
        if not self.api_key:
            raise ValueError("RUNWAYML_API_KEY not found in environment variables")
        
        self.client = RunwayML(api_key=self.api_key)
        print("✅ RunwayML client initialized")

    def generate_video(
        self,
        prompt: str,
        model: str = "veo3.1", # default to veo3.1 as gen3a_turbo is 403
        duration: int = 5,
        aspect_ratio: str = "1280:720",
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Generate video using Runway Gen-3 Alpha Turbo.
        """
        try:
            print(f"🚀 Creating Runway Gen-3 task: {prompt[:50]}...")
            
            # Map duration to Runway format (5 or 10)
            runway_duration = 10 if duration > 5 else 5
            
            # Create task using text_to_video
            # Note: veo3.1 was found to be available on the user's account.
            task = self.client.text_to_video.create(
                model=model,
                prompt_text=prompt,
                duration=runway_duration if model == "veo3.1" else None, # Let SDK handle defaults if not veo3.1
                ratio=aspect_ratio
            )
            
            task_id = task.id
            print(f"⏳ Task created with ID: {task_id}")
            
            if not wait_for_completion:
                return {
                    "status": "processing",
                    "task_id": task_id
                }
            
            # Polling for completion
            max_retries = 60 # 5 minutes with 5s sleep
            retry_count = 0
            
            while retry_count < max_retries:
                task = self.client.tasks.retrieve(task_id)
                status = task.status
                
                print(f"📊 Task {task_id} status: {status}")
                
                if status == "SUCCEEDED":
                    video_url = task.output[0] if task.output else None
                    print(f"✅ Runway Video Generated: {video_url}")
                    return {
                        "status": "completed",
                        "video_url": video_url,
                        "task_id": task_id,
                        "model": model,
                        "prompt": prompt
                    }
                elif status == "FAILED":
                    error_msg = getattr(task, "failure", "Unknown error")
                    print(f"❌ Runway Task Failed: {error_msg}")
                    raise Exception(f"Runway task failed: {error_msg}")
                
                retry_count += 1
                time.sleep(5)
            
            raise Exception("Runway task timed out after 5 minutes")
            
        except Exception as e:
            err_msg = str(e)
            if "403" in err_msg:
                print(f"❌ Runway Permission Error: {err_msg}")
                raise Exception(f"Model {model} tidah tersedia untuk akun Runway Anda (Error 403).")
            elif "400" in err_msg and "credits" in err_msg:
                print(f"❌ Runway Credit Error: {err_msg}")
                raise Exception("Kredit Runway Anda habis. Silakan top up di dashboard RunwayML.")
            
            print(f"❌ Runway Error: {err_msg}")
            raise e

    def text_to_video(self, prompt: str, duration: int = 5) -> Dict[str, Any]:
        # Helper for backward compatibility with existing main.py logic
        return self.generate_video(prompt=prompt, duration=duration)
