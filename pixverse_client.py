"""
PixVerse API Client
Dokumentasi: https://docs.platform.pixverse.ai/
"""
import httpx
import time
import os
import uuid
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class PixVerseClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PIXVERSE_API_KEY")
        
        # Real PixVerse API endpoint
        self.base_url = "https://app-api.pixverse.ai/openapi/v2"
        
        if not self.api_key:
            raise ValueError("PIXVERSE_API_KEY not found in environment variables")
        
        print(f"✅ PixVerse client initialized with real API")
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate headers with unique trace ID for each request"""
        return {
            "API-KEY": self.api_key,  # PixVerse menggunakan API-KEY, bukan Authorization
            "Content-Type": "application/json",
            "Ai-trace-id": str(uuid.uuid4())  # Unique ID untuk setiap request
        }
    
    def text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        model: str = "v5.5",
        quality: str = "720p",
        motion_mode: str = "normal"
    ) -> Dict[str, Any]:
        """
        Generate video dari text prompt menggunakan PixVerse API
        
        Args:
            prompt: Deskripsi video (max 2048 characters)
            duration: Durasi video (5 atau 8 detik)
            aspect_ratio: "16:9", "9:16", "1:1", "3:4", "4:3"
            style: "anime", "3d_animation", "day", "cyberpunk", "comic" (optional)
            negative_prompt: Hal yang ingin dihindari (optional)
            seed: Random seed 0-2147483647 (optional)
            model: "v3.5", "v4", "v4.5", "v5", "v5.5"
            quality: "360p", "540p", "720p", "1080p"
            motion_mode: "normal" atau "fast" (fast hanya 5 detik)
        
        Returns:
            Dict dengan video_id untuk tracking
        """
        # Validate duration
        if duration not in [5, 8]:
            print(f"⚠️  Duration {duration} not supported, using 5 seconds")
            duration = 5
        
        # 1080p doesn't support 8 seconds or fast mode
        if quality == "1080p":
            if duration == 8:
                duration = 5
                print(f"⚠️  1080p doesn't support 8 seconds, using 5 seconds")
            if motion_mode == "fast":
                motion_mode = "normal"
                print(f"⚠️  1080p doesn't support fast mode, using normal")
        
        payload = {
            "model": model,
            "prompt": prompt[:2048],  # Max 2048 characters
            "aspect_ratio": aspect_ratio,
            "duration": duration,
            "quality": quality,
            "motion_mode": motion_mode
        }
        
        if style:
            payload["style"] = style
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt[:2048]
        if seed is not None:
            payload["seed"] = seed
        
        try:
            print(f"🎬 Sending text-to-video request to PixVerse...")
            print(f"📝 Prompt: {prompt[:100]}...")
            print(f"⚙️  Model: {model}, Quality: {quality}, Duration: {duration}s")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/video/text/generate",
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("ErrCode") == 0:
                    video_id = result.get("Resp", {}).get("video_id")
                    print(f"✅ Task created: video_id={video_id}")
                    return {
                        "task_id": str(video_id),
                        "video_id": video_id,
                        "status": "processing"
                    }
                else:
                    error_msg = result.get("ErrMsg", "Unknown error")
                    print(f"❌ PixVerse API Error: {error_msg}")
                    raise Exception(f"PixVerse API Error: {error_msg}")
                    
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            raise Exception(f"PixVerse API HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"❌ Request Error: {str(e)}")
            raise
    
    def upload_image(self, image_path: str) -> Dict[str, Any]:
        """
        Upload image ke PixVerse untuk mendapatkan img_id
        
        Args:
            image_path: Path ke file gambar lokal
        
        Returns:
            Dict dengan img_id dan img_url
        """
        try:
            print(f"📤 Uploading image to PixVerse: {image_path}")
            
            # Baca file gambar
            with open(image_path, 'rb') as f:
                files = {
                    'image': (os.path.basename(image_path), f, 'image/jpeg')
                }
                
                # Headers tanpa Content-Type (akan di-set otomatis oleh httpx untuk multipart)
                headers = {
                    "API-KEY": self.api_key,
                    "Ai-trace-id": str(uuid.uuid4())
                }
                
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        f"{self.base_url}/image/upload",
                        files=files,
                        headers=headers
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    if result.get("ErrCode") == 0:
                        resp = result.get("Resp", {})
                        img_id = resp.get("img_id")
                        img_url = resp.get("img_url")
                        print(f"✅ Image uploaded: img_id={img_id}")
                        return {
                            "img_id": img_id,
                            "img_url": img_url
                        }
                    else:
                        error_msg = result.get("ErrMsg", "Unknown error")
                        print(f"❌ Upload error: {error_msg}")
                        raise Exception(f"PixVerse upload error: {error_msg}")
                        
        except Exception as e:
            print(f"❌ Error uploading image: {str(e)}")
            raise
    
    def image_to_video(
        self,
        img_id: int,
        prompt: str,
        duration: int = 5,
        model: str = "v5.5",
        quality: str = "720p",
        motion_mode: str = "normal",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate video dari gambar menggunakan PixVerse API
        
        Args:
            img_id: Image ID dari upload_image()
            prompt: Deskripsi gerakan/animasi
            duration: Durasi video (5 atau 8 detik)
            model: "v3.5", "v4", "v4.5", "v5", "v5.5"
            quality: "360p", "540p", "720p", "1080p"
            motion_mode: "normal" atau "fast"
            style: "anime", "3d_animation", dll (optional)
            negative_prompt: Hal yang ingin dihindari (optional)
            seed: Random seed (optional)
        
        Returns:
            Dict dengan video_id untuk tracking
        """
        # Validate duration
        if duration not in [5, 8]:
            print(f"⚠️  Duration {duration} not supported, using 5 seconds")
            duration = 5
        
        # 1080p doesn't support 8 seconds or fast mode
        if quality == "1080p":
            if duration == 8:
                duration = 5
                print(f"⚠️  1080p doesn't support 8 seconds, using 5 seconds")
            if motion_mode == "fast":
                motion_mode = "normal"
                print(f"⚠️  1080p doesn't support fast mode, using normal")
        
        payload = {
            "model": model,
            "img_id": img_id,
            "prompt": prompt[:2048],
            "duration": duration,
            "quality": quality,
            "motion_mode": motion_mode
        }
        
        if style:
            payload["style"] = style
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt[:2048]
        if seed is not None:
            payload["seed"] = seed
        
        try:
            print(f"🎬 Sending image-to-video request to PixVerse...")
            print(f"📝 Prompt: {prompt[:100]}...")
            print(f"🖼️  Image ID: {img_id}")
            print(f"⚙️  Model: {model}, Quality: {quality}, Duration: {duration}s")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/video/img/generate",
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("ErrCode") == 0:
                    video_id = result.get("Resp", {}).get("video_id")
                    print(f"✅ Task created: video_id={video_id}")
                    return {
                        "task_id": str(video_id),
                        "video_id": video_id,
                        "status": "processing"
                    }
                else:
                    error_msg = result.get("ErrMsg", "Unknown error")
                    print(f"❌ PixVerse API Error: {error_msg}")
                    raise Exception(f"PixVerse API Error: {error_msg}")
                    
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            raise Exception(f"PixVerse API HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"❌ Request Error: {str(e)}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Cek status task video generation menggunakan video_id
        
        Args:
            task_id: video_id dari text_to_video atau image_to_video
        
        Returns:
            Dict dengan status dan video_url (jika selesai)
            Status codes:
            - 1: Generation successful
            - 5: Waiting for generation
            - 7: Content moderation failure
            - 8: Generation failed
        """
        try:
            print(f"🔍 Checking status for video_id: {task_id}")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/video/status",
                    params={"video_id": task_id},
                    headers=self._get_headers()
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("ErrCode") == 0:
                    resp = result.get("Resp", {})
                    status_code = resp.get("status")
                    
                    # Map status codes
                    status_map = {
                        1: "completed",
                        5: "processing",
                        7: "failed",  # Content moderation failure
                        8: "failed"   # Generation failed
                    }
                    
                    status = status_map.get(status_code, "unknown")
                    video_url = resp.get("url") if status_code == 1 else None
                    
                    if status_code == 1:
                        print(f"✅ Video completed: {video_url}")
                    elif status_code == 5:
                        print(f"⏳ Video still processing...")
                    elif status_code in [7, 8]:
                        print(f"❌ Video generation failed (status: {status_code})")
                    
                    return {
                        "task_id": task_id,
                        "video_id": task_id,
                        "status": status,
                        "video_url": video_url,
                        "raw_status": status_code,
                        "prompt": resp.get("prompt"),
                        "create_time": resp.get("create_time"),
                        "modify_time": resp.get("modify_time")
                    }
                else:
                    error_msg = result.get("ErrMsg", "Unknown error")
                    print(f"❌ Error checking status: {error_msg}")
                    return {
                        "task_id": task_id,
                        "status": "error",
                        "error": error_msg
                    }
                    
        except Exception as e:
            print(f"❌ Error checking task status: {str(e)}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
    
    def wait_for_completion(
        self,
        task_id: str,
        max_wait: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Tunggu sampai video selesai di-generate
        
        Args:
            task_id: video_id dari PixVerse
            max_wait: Maksimal waktu tunggu dalam detik (default: 300 = 5 menit)
            poll_interval: Interval pengecekan dalam detik (default: 5)
        
        Returns:
            Dict dengan status final dan video_url
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_result = self.get_task_status(task_id)
            
            state = status_result.get("status", "unknown")
            
            if state == "completed":
                print(f"✅ Video generation completed!")
                return status_result
            elif state == "failed":
                print(f"❌ Video generation failed!")
                return status_result
            elif state == "error":
                print(f"❌ Error checking status!")
                return status_result
            
            # Still processing, wait and try again
            time.sleep(poll_interval)
        
        print(f"⏰ Timeout waiting for task {task_id}")
        return {"status": "timeout", "task_id": task_id}
