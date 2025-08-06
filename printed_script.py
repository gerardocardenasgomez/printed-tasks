from ascii_art import RANDOM_RECEIPT_ART
import random
from datetime import datetime
import requests
from typing import List, Dict, Any
import argparse
from supabase_utils import add_task, search_tasks, complete_task_by_id
from utils.utils import get_config
import os
ai_enabled = False

config_path = os.path.join(os.path.dirname(__file__), "config.ini")
config = get_config(config_path)

if (config.has_section("GOOGLE")):
    google_api_key = config.get("GOOGLE", "GOOGLE_API_KEY")
    ai_enabled = True

parser = argparse.ArgumentParser()
parser.add_argument('-n', "--task_name", type=str, help="The name of the task to run", required=True)
parser.add_argument('-d', "--task_description", type=str, help="The description of the task to run", required=True)
parser.add_argument('-p', "--task_priority", type=str, help="The priority of the task", required=True)

args = parser.parse_args()

print("Getting Ready to Print Task")

task_header = "ADVANCED TASK MANAGEMENT SYSTEM V0.2"
task_pinted_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
task_name = args.task_name
task_description = args.task_description
task_priority = args.task_priority


if ai_enabled:
    try:
        ai_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
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
                "maxOutputTokens": 150,
                "temperature": 0.7
            }
        }
        response = requests.post(ai_url, headers=ai_headers, json=ai_payload)
        response_data = response.json()
        
        # Debug: print the response structure
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response_data}")
        
        # Handle potential errors in response
        if "error" in response_data:
            print(f"Google API error: {response_data['error']}")
            ai_message = "Keep up the great work on your tasks!"
        elif "candidates" in response_data and len(response_data["candidates"]) > 0:
            ai_message = response_data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"AI message: {ai_message}")
            
            # If message is still too long, split it into multiple print calls
            if len(ai_message) > 150:
                print(f"Message is long ({len(ai_message)} chars), splitting into chunks...")
                # Split into chunks of ~100 characters, trying to break at word boundaries
                chunks = []
                current_chunk = ""
                words = ai_message.split()
                
                for word in words:
                    if len(current_chunk + " " + word) <= 100:
                        current_chunk += (" " + word) if current_chunk else word
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = word
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                print(f"Split into {len(chunks)} chunks: {chunks}")
                ai_message = chunks  # Store as list for later processing
            else:
                ai_message = [ai_message]  # Keep as single-item list for consistent processing
        else:
            print(f"Unexpected response structure: {response_data}")
            ai_message = ["Keep up the great work on your tasks!"]
    except Exception as e:
        print(f"Google text generation failed: {e}")
        ai_message = "Keep up the great work on your tasks!"

print_url = config.get("API", "URL") + "/print"
cut_url = config.get("API", "URL") + "/cut"

# First print header
header_text = f"{task_header}\nTASK: {task_name}\nTASK_DESC: {task_description}\n\nPRIORITY: {task_priority}\nPRINTED_ON: {task_pinted_on}\n\n"

response = requests.get(print_url, params={"text": header_text})
print(f"Header print response: {response.text}")

ascii_art = random.choice(RANDOM_RECEIPT_ART)
response = requests.get(print_url, params={"text": ascii_art})
print(f"ASCII art print response: {response.text}")

# Print AI message if enabled
if ai_enabled and ai_message:
    # Print each chunk separately
    for i, chunk in enumerate(ai_message):
        if i == 0:  # First chunk
            message_text = f"{chunk}"
        elif i == len(ai_message) - 1:  # Last chunk
            message_text = f"{chunk}\n\n\n*** ~*~ ***\n"
        else:  # Middle chunks
            message_text = f"{chunk}"
        
        response = requests.get(print_url, params={"text": message_text})
        print(f"Message chunk {i+1}/{len(ai_message)} print response: {response.text}")

# Cut the paper
response = requests.get(cut_url)
print(f"Cut response: {response.text}")
