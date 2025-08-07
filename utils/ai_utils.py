import requests
ai_model = "gemini-2.0-flash"
ai_url = f"https://generativelanguage.googleapis.com/v1beta/models/{ai_model}:generateContent"

ai_message = "Keep up the great work on your tasks!"

def get_ai_response(task_description: str, google_api_key: str, max_output_tokens: int = 150, temperature: float = 0.7):
    try:
        ai_headers = {
            "X-goog-api-key": f"{google_api_key}",
            "Content-Type": "application/json"
        }

        ai_payload = {
            "contents": [
              {
                "parts": [
                  {
                    "text": f"Write a very short, encouraging message (max 4 sentences) about this TODO task: {task_description}"
                  }
                ]
              }
            ],
            "generationConfig": {
                "maxOutputTokens": max_output_tokens,
                "temperature": temperature
            }
        }
        response = requests.post(ai_url, headers=ai_headers, json=ai_payload)
        response_data = response.json()
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response_data}")
        
        if "error" in response_data:
            print(f"Google API error: {response_data['error']}")
        elif "candidates" in response_data and len(response_data["candidates"]) > 0:
            ai_message = response_data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"AI message: {ai_message}")
        else:
            print(f"Unexpected response structure: {response_data}")
    except Exception as e:
        print(f"Google text generation failed: {e}")

    return ai_message