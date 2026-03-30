from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from replicate_client import ReplicateVideoClient
from fal_client_manager import FalClientManager
import os

from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client (GRATIS & CEPAT!)
try:
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        client = Groq(api_key=api_key)
        print(f"✅ Groq client initialized")
    else:
        client = None
        print("⚠️  GROQ_API_KEY not found - using mock responses")
except ImportError:
    client = None
    print("⚠️  Groq not installed. Run: pip install groq")

# Initialize Replicate client
try:
    video_client = ReplicateVideoClient()
    print(f"✅ Replicate video client initialized")
except Exception as e:
    video_client = None
    print(f"⚠️  Replicate initialization error: {e}")

# Initialize Fal client
try:
    fal_client = FalClientManager()
except Exception as e:
    fal_client = None
    print(f"⚠️  Fal initialization error: {e}")

class PromptRequest(BaseModel):
    prompt: str
    model: str = "minimax"

class ClassifyRequest(BaseModel):
    prompt: str

class ChatRequest(BaseModel):
    prompt: str
    history: list = []

class VideoGenerationRequest(BaseModel):
    prompt: str
    duration: int = 5
    image_url: str = None
    input_video_url: str = None
    reference_image_url: str = None # Added for VidEdit
    style: str = None
    negative_prompt: str = None
    motion_strength: float = 0.5
    wait_for_completion: bool = False
    model: str = "minimax"  # minimax, replicate/video-01, or fal-ai/wan

@app.get("/")
def root():
    return {
        "message": "AI Engine API with Replicate Video Generation (FREE TIER!)",
        "status": "running",
        "models": {
            "text": "llama-3.3-70b-versatile (FREE)",
            "video": "Replicate (MiniMax) - $10-25 FREE CREDIT!",
            "image": "description only"
        },
        "replicate_status": "active" if video_client else "not configured",
        "free_credit": "$10-25 for new accounts"
    }

@app.post("/generate")
def generate(request: PromptRequest):
    """Generate AI response using Groq (FREE & FAST)"""
    try:
        print(f"🤖 Generating with Groq: {request.prompt[:50]}...")
        
        if not client:
            return {
                "result": f"⚠️ Groq API belum dikonfigurasi. Dapatkan API key gratis di: https://console.groq.com/keys\n\nPrompt Anda: {request.prompt}",
                "model": "mock",
                "type": "text"
            }
        
        # Call Groq API (GRATIS!)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative AI assistant that generates detailed video descriptions. Describe visuals, scenes, camera movements, and atmosphere."
                },
                {
                    "role": "user",
                    "content": request.prompt
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        result = response.choices[0].message.content
        print(f"✅ Generated: {result[:100]}...")
        
        return {
            "result": result,
            "model": "llama-3.3-70b-versatile",
            "type": "text"
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "result": f"Error: {str(e)}\n\nCara fix:\n1. Dapatkan API key gratis: https://console.groq.com/keys\n2. Tambahkan ke .env: GROQ_API_KEY=your-key\n3. Restart server",
            "model": "error",
            "type": "text"
        }

@app.post("/classify")
def classify(request: ClassifyRequest):
    """Determine if user wants to generate a video or just chat"""
    try:
        print(f"🔍 Classifying prompt: {request.prompt[:50]}...")
        
        if not client:
            # Fallback jika Groq tidak ada
            prompt_lower = request.prompt.lower()
            if any(word in prompt_lower for word in ["video", "buatkan", "generate", "bikin", "film", "movie"]):
                return {"intent": "video"}
            return {"intent": "chat"}

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an intent classifier. Your task is to determine if a user wants to generate a video or just engage in general chat/conversation. Respond ONLY with the word 'video' if they want to generate a video, or 'chat' if they just want to talk. If it's ambiguous, prefer 'chat'."
                },
                {
                    "role": "user",
                    "content": request.prompt
                }
            ],
            max_tokens=10,
            temperature=0
        )
        
        intent = response.choices[0].message.content.strip().lower()
        if "video" in intent:
            intent = "video"
        else:
            intent = "chat"
            
        print(f"✅ Classified as: {intent}")
        return {"intent": intent}
        
    except Exception as e:
        print(f"❌ Classification error: {e}")
        return {"intent": "chat"} # Fallback to chat

@app.post("/chat")
def chat(request: ChatRequest):
    """General conversation using Groq"""
    try:
        print(f"💬 Chatting with Groq: {request.prompt[:50]}...")
        
        if not client:
            return {
                "result": "Halo! Saya asisten AI Anda. Groq belum dikonfigurasi, jadi saya hanya bisa merespon secara terbatas.",
                "model": "mock",
                "type": "chat"
            }
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful and friendly AI assistant. You don't have a specific name yet. Your primary purpose is to help users generate high-quality videos.\n\nSTRICT FORMATTING RULES:\n1. Use clean, professional Indonesian (or the user's language).\n2. NEVER use double asterisks (**) or any markdown bolding.\n3. For subheadings or points, use plain text with a colon (:) or a simple dash (-).\n4. Ensure the output is purely text-based and easy to read.\n5. Do NOT include any markdown symbols like # or **."
            }
        ]
        
        # Add history if provided
        for msg in request.history:
            # Map 'ai' to 'assistant' just in case
            role = msg.get("role", "user")
            if role == "ai":
                role = "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})
            
        messages.append({"role": "user", "content": request.prompt})
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        result = response.choices[0].message.content
        
        # Post-processing to force remove any double asterisks
        result = result.replace("**", "")
        
        print(f"✅ Chat response: {result[:100]}...")
        
        return {
            "result": result,
            "model": "llama-3.3-70b-versatile",
            "type": "chat"
        }
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return {
            "result": f"Maaf, saya sedang mengalami kendala teknis: {str(e)}",
            "model": "error",
            "type": "chat"
        }

@app.post("/generate-video")
def generate_video(request: VideoGenerationRequest):
    """
    Generate video menggunakan Replicate API (FREE $10-25 CREDIT!)
    - Text-to-Video: Kirim prompt
    - Image-to-Video: Kirim prompt + image_url
    """
    try:
        # Advanced Video-to-Video Editing (Wan2.2 Animate Replace using Fal.ai)
        if request.input_video_url and request.image_url:
            if not fal_client:
                raise HTTPException(
                    status_code=503,
                    detail="Fal.ai API not configured. Check FAL_KEY in .env."
                )
            print(f"🎨 Using Wan2.2 Animate Replace for Template Editing (Fal.ai)...")
            result = fal_client.wan_animate_replace(
                image_url=request.image_url,
                video_url=request.input_video_url,
                prompt=request.prompt
            )

        # Image-to-Video (using Replicate)
        elif request.image_url:
            if not video_client:
                raise HTTPException(
                    status_code=503,
                    detail="Replicate API not configured. Check REPLICATE_API_TOKEN in .env. Get free $10-25 credit at https://replicate.com/"
                )
            print(f"🖼️  Image-to-Video mode")
            print(f"📷 Image URL: {request.image_url}")
            
            result = video_client.image_to_video(
                image_url=request.image_url,
                prompt=request.prompt or "Animate this image with natural motion",
                duration=request.duration,
                model=request.model
            )
        
        # Text-to-Video
        else:
            print(f"🎬 Text-to-Video mode")
            print(f"📝 Prompt: {request.prompt[:100]}...")
            
            result = video_client.text_to_video(
                prompt=request.prompt,
                duration=request.duration,
                model=request.model
            )
        
        print(f"✅ Video generated successfully!")
        
        # Generate dynamic response text using Groq - ALWAYS use AI, no fallback template
        response_text = ""
        if client:
            try:
                chat_completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a friendly AI video generator assistant. Respond in 1-2 short, engaging Indonesian sentences based on their prompt. Tell them their video is ready in a natural, conversational way. Be creative and specific to their prompt. Do not use generic templates."
                        },
                        {
                            "role": "user",
                            "content": f"User requested a video with this prompt: {request.prompt}"
                        }
                    ],
                    max_tokens=150,
                    temperature=0.8
                )
                response_text = chat_completion.choices[0].message.content.strip()
                print(f"✅ Generated AI response: {response_text}")
            except Exception as e:
                print(f"⚠️ Groq text generation failed: {e}")
                # Fallback hanya jika Groq gagal
                response_text = f"Video Anda sudah siap! 🎬"
        else:
            # Fallback jika Groq tidak tersedia
            response_text = f"Video berhasil dibuat untuk prompt: \"{request.prompt}\" 🎬"

        # Replicate langsung return video URL (tidak perlu polling)
        return {
            "result": response_text,
            "video_url": result.get("video_url"),
            "status": "completed",
            "model": "llama-3.3-70b-versatile" if client else f"Replicate ({request.model})",
            "prompt": request.prompt,
            "duration": request.duration,
            "note": "Replicate provides instant results - no polling needed!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        error_detail = str(e)
        
        # Berikan pesan error yang lebih informatif
        if "REPLICATE_API_TOKEN" in error_detail or "not found" in error_detail:
            error_detail = "API token tidak valid. Dapatkan free credit $10-25 di https://replicate.com/ lalu set REPLICATE_API_TOKEN di .env"
        elif "429" in error_detail or "rate limit" in error_detail.lower():
            error_detail = "Rate limit Replicate tercapai (429). Tunggu beberapa menit atau tambahkan metode pembayaran di Replicate."
        elif "402" in error_detail or "insufficient" in error_detail.lower() or "credit" in error_detail.lower():
            error_detail = "Credit Replicate habis atau trial berakhir (402). Silakan top up di https://replicate.com/account/billing"
        
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

@app.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    """
    Replicate tidak perlu polling - video langsung tersedia
    Endpoint ini untuk backward compatibility
    """
    return {
        "task_id": task_id,
        "status": "completed",
        "note": "Replicate provides instant results - no polling needed"
    }

@app.post("/generate-image")
def generate_image(request: PromptRequest):
    """Generate image description (actual image generation requires paid API)"""
    try:
        print(f"🎨 Image description: {request.prompt[:50]}...")
        
        if not client:
            return {
                "result": f"🖼️ Image Description:\n\n{request.prompt}\n\n⚠️ Untuk generate gambar real, gunakan:\n- DALL-E (berbayar)\n- Stable Diffusion (gratis via Hugging Face)\n- Midjourney (berbayar)",
                "image_url": "https://via.placeholder.com/1024x1024.png?text=Setup+API+Key",
                "model": "mock",
                "type": "image"
            }
        
        # Generate detailed image description
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Describe in detail what this image would look like: composition, colors, lighting, style, mood."
                },
                {
                    "role": "user",
                    "content": request.prompt
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        description = response.choices[0].message.content
        
        return {
            "result": f"Image Description:\n\n{description}\n\n💡 Untuk generate gambar real, gunakan Stable Diffusion atau DALL-E",
            "image_url": "https://via.placeholder.com/1024x1024.png?text=Image+Description+Generated",
            "model": "llama-3.3-70b-versatile",
            "type": "image"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "result": f"Error: {str(e)}",
            "image_url": "https://via.placeholder.com/1024x1024.png?text=Error",
            "model": "error",
            "type": "image"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
