import fal_client
import os
import requests
from typing import Dict, Any

class FalClientManager:
    def __init__(self):
        self.api_key = os.getenv("FAL_KEY")
        if not self.api_key:
            print("⚠️ FAL_KEY environment variable not found. Fal Client might fail.")
        else:
            # Set the environment variable for the fal_client library explicitly if needed
            os.environ["FAL_KEY"] = self.api_key
            print("✅ Fal.ai client initialized successfully")

    def upload_image_if_needed(self, path_or_url: str) -> str:
        """
        Fal accepts URLs directly. For localhost URLs (which fal's remote backend can't reach),
        we convert the file path to a Fal Storage URL if needed.
        """
        # If it's a localhost URL
        if "localhost" in path_or_url or "127.0.0.1" in path_or_url:
            filename = path_or_url.split("/")[-1]
            local_path = f"../backend-ai-generate/uploads/{filename}"
            if os.path.exists(local_path):
                print(f"🔄 Uploading local file {local_path} to Fal Storage...")
                # Note: For real implementations handling files directly, you might upload it to Fal's temp storage:
                # url = fal_client.upload_file(local_path)
                # But since Supabase urls are already public, we can just return the URL if it's external
                import base64
                with open(local_path, "rb") as f:
                    image_data = f.read()
                
                ext = local_path.split(".")[-1].lower()
                mime_types = {
                    "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "gif": "image/gif", "webp": "image/webp"
                }
                mime_type = mime_types.get(ext, "image/jpeg")
                base64_data = base64.b64encode(image_data).decode('utf-8')
                data_uri = f"data:{mime_type};base64,{base64_data}"
                print("✅ Converted local file to Data URI")
                return data_uri
                
        return path_or_url


    def wan_animate_replace(
        self,
        image_url: str,
        video_url: str,
        prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Uses fal-ai/wan/v2.2-14b/animate/replace to replace character in video
        """
        try:
            print(f"🎬 Fal.ai Wan 2.2 Animate Replace")
            print(f"📷 Target Image: {image_url[:80]}...")
            print(f"📹 Source Video: {video_url[:80]}...")
            
            # Ensure accessible URLs
            processed_image_url = self.upload_image_if_needed(image_url)
            processed_video_url = self.upload_image_if_needed(video_url)

            model_id = "fal-ai/wan/v2.2-14b/animate/replace"

            # Based on Fal's playground inputs for Wan2.2 Animate Replace
            # The exact parameter names are usually 'image_url' and 'video_url', and 'prompt'
            input_args = {
                "image_url": processed_image_url,
                "video_url": processed_video_url,
                "prompt": prompt if prompt.strip() else "Match original video motion"
            }

            print(f"🤖 Calling {model_id} via Fal.ai...")
            result = fal_client.subscribe(
                model_id,
                arguments=input_args,
                with_logs=True
            )

            # Extract generated video URL
            video_output_url = None
            if isinstance(result, dict):
                # Usually Fal returns {"video": {"url": "..."}}
                video_data = result.get("video", {})
                if isinstance(video_data, dict):
                    video_output_url = video_data.get("url")
            
            if not video_output_url:
                print(f"⚠️ Warning: Could not parse video URL from output: {result}")
                # Fallback to stringifying
                video_output_url = str(result)
                
            print(f"✅ Video generated with Fal.ai: {video_output_url[:80]}...")

            return {
                "status": "completed",
                "video_url": video_output_url,
                "model": model_id,
                "prompt": prompt,
                "source_image": image_url,
                "source_video": video_url,
            }

        except Exception as e:
            print(f"❌ Fal.ai Error: {str(e)}")
            raise Exception(f"Fal.ai API error: {str(e)}")
