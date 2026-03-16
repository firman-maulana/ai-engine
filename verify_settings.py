import requests
import json

def test_generate_video():
    url = "http://localhost:9000/generate-video"
    payload = {
        "prompt": "A futuristic city at sunset, cinematic lighting",
        "duration": 5,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        "model": "minimax"
    }
    
    print(f"Testing /generate-video with payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Note: This might fail if Replicate is not actually running or if there are no credits,
        # but we want to see if the AI Engine handles the parameters correctly.
        # We'll use a short timeout to see if it starts processing.
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.Timeout:
        print("Request timed out as expected (generation takes time)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_generate_video()
