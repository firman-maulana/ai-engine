"""
Script untuk testing PixVerse API
"""
import requests
import time

BASE_URL = "http://localhost:9000"

def test_text_to_video():
    """Test Text-to-Video"""
    print("\n" + "="*60)
    print("🎬 TEST 1: TEXT-TO-VIDEO")
    print("="*60)
    
    payload = {
        "prompt": "A beautiful sunset over the ocean with waves crashing on the beach",
        "duration": 5,
        "aspect_ratio": "16:9",
        "style": "cinematic",
        "wait_for_completion": False  # Set True untuk tunggu sampai selesai
    }
    
    print(f"📝 Prompt: {payload['prompt']}")
    print(f"⏱️  Duration: {payload['duration']}s")
    print(f"📐 Aspect Ratio: {payload['aspect_ratio']}")
    print(f"🎨 Style: {payload['style']}")
    
    response = requests.post(f"{BASE_URL}/generate-video", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Response:")
        print(f"   Task ID: {result.get('task_id')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('result')}")
        
        # Polling status
        if result.get('task_id'):
            task_id = result['task_id']
            print(f"\n⏳ Checking status...")
            
            for i in range(10):  # Check 10 kali
                time.sleep(5)
                status_response = requests.get(f"{BASE_URL}/task-status/{task_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   [{i+1}] Status: {status_data.get('status')} - Progress: {status_data.get('progress', 0)}%")
                    
                    if status_data.get('status') == 'completed':
                        print(f"\n🎉 Video URL: {status_data.get('video_url')}")
                        break
                    elif status_data.get('status') == 'failed':
                        print(f"\n❌ Failed: {status_data.get('error')}")
                        break
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def test_image_to_video():
    """Test Image-to-Video"""
    print("\n" + "="*60)
    print("🎬 TEST 2: IMAGE-TO-VIDEO")
    print("="*60)
    
    # Gunakan URL gambar yang sudah di-upload
    payload = {
        "prompt": "Make the clouds move slowly across the sky",
        "image_url": "http://localhost:8000/uploads/your-image.jpg",  # Ganti dengan URL gambar Anda
        "duration": 5,
        "motion_strength": 0.7,
        "wait_for_completion": False
    }
    
    print(f"📷 Image URL: {payload['image_url']}")
    print(f"📝 Motion Prompt: {payload['prompt']}")
    print(f"⏱️  Duration: {payload['duration']}s")
    print(f"💪 Motion Strength: {payload['motion_strength']}")
    
    response = requests.post(f"{BASE_URL}/generate-video", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Response:")
        print(f"   Task ID: {result.get('task_id')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('result')}")
        
        if result.get('task_id'):
            print(f"\n💡 Gunakan endpoint ini untuk cek status:")
            print(f"   GET {BASE_URL}/task-status/{result['task_id']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def test_api_status():
    """Test API Status"""
    print("\n" + "="*60)
    print("🔍 CHECKING API STATUS")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Status: {data.get('status')}")
        print(f"📦 Models:")
        for key, value in data.get('models', {}).items():
            print(f"   - {key}: {value}")
        print(f"🎬 PixVerse: {data.get('pixverse_status')}")
    else:
        print(f"❌ API not responding")

if __name__ == "__main__":
    print("\n🚀 PixVerse API Testing")
    print("="*60)
    
    # Test API status
    test_api_status()
    
    # Test text-to-video
    test_text_to_video()
    
    # Test image-to-video (uncomment jika sudah punya image URL)
    # test_image_to_video()
    
    print("\n" + "="*60)
    print("✅ Testing selesai!")
    print("="*60)
