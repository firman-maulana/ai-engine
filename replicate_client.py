"""
Replicate API Client untuk Video Generation
Dokumentasi: https://replicate.com/docs
"""
import replicate
import os
import time
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ReplicateVideoClient:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN not found in environment variables")
        
        # Set environment variable untuk replicate library
        os.environ["REPLICATE_API_TOKEN"] = self.api_token
        
        print(f"✅ Replicate client initialized")
    
    def upload_image_to_replicate(self, image_path_or_url: str) -> str:
        """
        Upload image ke Replicate atau convert local path ke data URI
        
        Args:
            image_path_or_url: Local file path atau URL
            
        Returns:
            URL atau data URI yang bisa diakses Replicate
        """
        try:
            # Jika sudah URL dan bukan localhost, return as is
            if image_path_or_url.startswith("http") and "localhost" not in image_path_or_url and "127.0.0.1" not in image_path_or_url:
                print(f"✅ Using existing URL: {image_path_or_url[:80]}...")
                return image_path_or_url
            
            # Jika localhost URL, convert ke file path
            if "localhost" in image_path_or_url or "127.0.0.1" in image_path_or_url:
                # Extract filename dari URL
                filename = image_path_or_url.split("/")[-1]
                # Assume uploads folder di backend
                image_path_or_url = f"../backend-ai-generate/uploads/{filename}"
                print(f"🔄 Converting localhost URL to file path: {image_path_or_url}")
            
            # Jika file path, baca dan convert ke data URI
            if os.path.exists(image_path_or_url):
                import base64
                with open(image_path_or_url, "rb") as f:
                    image_data = f.read()
                    
                # Detect mime type
                ext = image_path_or_url.split(".")[-1].lower()
                mime_types = {
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "gif": "image/gif",
                    "webp": "image/webp"
                }
                mime_type = mime_types.get(ext, "image/jpeg")
                
                # Convert to base64 data URI
                base64_data = base64.b64encode(image_data).decode('utf-8')
                data_uri = f"data:{mime_type};base64,{base64_data}"
                
                print(f"✅ Converted to data URI (size: {len(data_uri)} chars)")
                return data_uri
            
            # Jika tidak bisa diproses, return as is
            print(f"⚠️ Could not process image, using as is: {image_path_or_url[:80]}...")
            return image_path_or_url
            
        except Exception as e:
            print(f"❌ Error processing image: {str(e)}")
            # Return original jika gagal
            return image_path_or_url
    
    def text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        model: str = "minimax",
        fps: int = 25,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate video dari text prompt menggunakan Replicate (MiniMax)
        
        Args:
            prompt: Deskripsi video
            duration: Durasi video dalam detik (default: 5)
            aspect_ratio: "16:9", "9:16", "1:1", "4:3", "3:4" (default: "16:9")
            model: "minimax" (default)
            fps: Frame per second (default: 25)
        
        Returns:
            Dict dengan video_url dan metadata
        """
        try:
            print(f"🎬 Text-to-Video with MiniMax")
            print(f"📝 Prompt: {prompt[:100]}...")
            print(f"⏱️  Duration: {duration}s, Aspect: {aspect_ratio}")
            
            # MiniMax Text-to-Video Model
            model_version = "minimax/video-01"
            
            input_params = {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "prompt_optimizer": True
            }
            
            print(f"🤖 Using model: {model_version}")
            
            # Run model
            output = replicate.run(
                model_version,
                input=input_params
            )
            
            # Output bisa berupa URL string atau FileOutput object
            if isinstance(output, str):
                video_url = output
            elif hasattr(output, 'url'):
                video_url = output.url
            elif isinstance(output, list) and len(output) > 0:
                video_url = output[0] if isinstance(output[0], str) else output[0].url
            else:
                video_url = str(output)
            
            print(f"✅ Video generated: {video_url[:80]}...")
            
            return {
                "status": "completed",
                "video_url": video_url,
                "model": model_version,
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio
            }
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise Exception(f"Replicate API error: {str(e)}")
    
    def image_to_video(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        model: str = "minimax",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate video dari gambar menggunakan Replicate
        
        Args:
            image_url: URL gambar sumber atau local file path
            prompt: Deskripsi gerakan (optional)
            duration: Durasi video dalam detik
            model: "minimax" only (default: "minimax")
        
        Returns:
            Dict dengan video_url dan metadata
        """
        try:
            print(f"🖼️  Image-to-Video with Replicate ({model})")
            print(f"📷 Image: {image_url[:80]}...")
            if prompt:
                print(f"📝 Prompt: {prompt[:100]}...")
            
            # Process image URL (convert localhost to data URI if needed)
            processed_image_url = self.upload_image_to_replicate(image_url)
            
            # MiniMax Image-to-Video only
            model_version = "minimax/video-01"
            input_params = {
                "prompt": prompt or "Animate this image with natural motion",
                "first_frame_image": processed_image_url,
                "aspect_ratio": aspect_ratio,
                "prompt_optimizer": True
            }
            
            print(f"🤖 Using model: {model_version}")
            
            # Run model
            output = replicate.run(
                model_version,
                input=input_params
            )
            
            # Parse output
            if isinstance(output, str):
                video_url = output
            elif hasattr(output, 'url'):
                video_url = output.url
            elif isinstance(output, list) and len(output) > 0:
                video_url = output[0] if isinstance(output[0], str) else output[0].url
            else:
                video_url = str(output)
            
            print(f"✅ Video generated: {video_url[:80]}...")
            
            return {
                "status": "completed",
                "video_url": video_url,
                "model": model_version,
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "source_image": image_url
            }
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise Exception(f"Replicate API error: {str(e)}")
    def wan_animate_replace(
        self,
        image_url: str,
        input_video_url: str,
        prompt: str = "Animate this image to match the video motion",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Replace character in video using Wan2.2 Animate Replace on Replicate
        
        Args:
            image_url: URL gambar karakter baru
            input_video_url: URL video sumber (motion)
            prompt: Text prompt tambahan (opsional)
        """
        try:
            print(f"🎬 Wan2.2 Animate Replace")
            print(f"📷 Target Image: {image_url[:80]}...")
            print(f"📹 Source Video: {input_video_url[:80]}...")
            
            # Convert localhost to base64 data URI for replicate if needed
            processed_image_url = self.upload_image_to_replicate(image_url)
            
            model_version = "wan-video/wan-2.2-animate-replace"
            
            input_params = {
                "image": processed_image_url,
                "video": input_video_url,
                "prompt": prompt
            }
            
            print(f"🤖 Using model: {model_version}")
            
            # Run model
            output = replicate.run(
                model_version,
                input=input_params
            )
            
            # Parse output (Replicate usually returns URL directly or File object)
            if isinstance(output, str):
                video_url = output
            elif hasattr(output, 'url'):
                video_url = output.url
            elif isinstance(output, list) and len(output) > 0:
                video_url = output[0] if isinstance(output[0], str) else output[0].url
            else:
                video_url = str(output)
            
            print(f"✅ Video generated with Wan2.2: {video_url[:80]}...")
            
            return {
                "status": "completed",
                "video_url": video_url,
                "model": model_version,
                "prompt": prompt,
                "source_image": image_url,
                "source_video": input_video_url,
                "duration": 5 # Estimated
            }
            
        except Exception as e:
            print(f"❌ Wan2.2 Error: {str(e)}")
            raise Exception(f"Wan2.2 API error: {str(e)}")
