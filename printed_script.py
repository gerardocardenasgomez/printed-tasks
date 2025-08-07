from utils.ascii_art import RANDOM_RECEIPT_ART
import random
from datetime import datetime
from utils.supabase_utils import add_task, init_supabase_config
import requests
import argparse
import os
from utils.utils import get_config, printer_word_wrap, get_barcode
from utils.ai_utils import get_ai_response
import time

SLEEP_DELAY = 0.5
ai_enabled = False
supabase_enabled = False
task_id = None

config_path = os.path.join(os.path.dirname(__file__), "config.ini")
config = get_config(config_path)

try:
    if (config.has_section("GOOGLE")):
        google_api_key = config.get("GOOGLE", "GOOGLE_API_KEY")
        ai_enabled = True

    if (config.has_section("SUPABASE")):
        supabase_enabled = True
        supabase_url = config.get("SUPABASE", "SUPABASE_URL")
        supabase_key = config.get("SUPABASE", "SUPABASE_API_KEY")
        user_email = config.get("SUPABASE", "SUPABASE_USER_EMAIL")
        user_password = config.get("SUPABASE", "SUPABASE_USER_PASSWORD")
except Exception as e:
    print(f"Error getting config: {e}")
    raise e

parser = argparse.ArgumentParser()
parser.add_argument('-n', "--task_name", type=str, help="The name of the task to run", required=True)
parser.add_argument('-d', "--task_description", type=str, help="The description of the task to run", required=True)
parser.add_argument('-p', "--task_priority", type=str, help="The priority of the task", required=True)

args = parser.parse_args()

print("Getting Ready to Print Task")

# Task header will act as versioning basically
task_header = "ADVANCED TASK MANAGEMENT SYSTEM V1.0"
task_printed_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
task_name = args.task_name
task_description = args.task_description
task_priority = args.task_priority

if ai_enabled:
    ai_message = get_ai_response(task_description, google_api_key)

print_url = config.get("API", "URL") + "/print"
cut_url = config.get("API", "URL") + "/cut"

if supabase_enabled:
    init_supabase_config(supabase_url, supabase_key, user_email, user_password)
    task_id = add_task(task_name, task_description, task_priority, task_header, ai_message)

# First print header
# We do not need to wrap this because look how many new lines we have!
header_text = f"{task_header}\nTASK: {task_name}\nTASK_DESC: {task_description}\n\nPRIORITY: {task_priority}\nPRINTED_ON: {task_printed_on}\n\n"
wrapped_header_text = printer_word_wrap(header_text)

response = requests.get(print_url, params={"text": wrapped_header_text})
print(f"Header print response: {response.text}")
time.sleep(SLEEP_DELAY)

ascii_art = random.choice(RANDOM_RECEIPT_ART)
response = requests.get(print_url, params={"text": ascii_art + "\n\n"})
print(f"ASCII art print response: {response.text}")
time.sleep(SLEEP_DELAY)

# Print AI message if enabled
if ai_enabled and ai_message:
    wrapped_message = printer_word_wrap(ai_message)
    
    # Split along newlines to avoid buffer overflow on printer
    line_count = wrapped_message.count('\n')
    
    if line_count > 1:
        lines = wrapped_message.split('\n')
        mid_point = len(lines) // 2
        
        first_half = '\n'.join(lines[:mid_point]) + '\n'
        second_half = '\n'.join(lines[mid_point:])
        
        response = requests.get(print_url, params={"text": first_half})
        print(f"AI message first half print response: {response.text}")
        time.sleep(SLEEP_DELAY)
        
        response = requests.get(print_url, params={"text": second_half})
        print(f"AI message second half print response: {response.text}")
        time.sleep(SLEEP_DELAY)
    else:
        # Single line, print as-is
        response = requests.get(print_url, params={"text": wrapped_message})
        print(f"AI message print response: {response.text}")
        time.sleep(SLEEP_DELAY)

# Print BARCODE
#if task_id:
#    # Debug by sending more simple text
#    #barcode_cmd = get_barcode(task_id)
#    debug_barcode_cmd = get_barcode("ABCD123DEF456")
#    response = requests.get(print_url, params={"text": debug_barcode_cmd})
#    print(f"Barcode print response: {response.text}")
#    time.sleep(SLEEP_DELAY)

if task_id:
    # if we printed a barcode, we need a bit of space before the cut
    # we should print the task_id bare
    response = requests.get(print_url, params={"text": "\n\n" + task_id + "\n\n"})

# Cut the paper
response = requests.get(cut_url)
print(f"Cut response: {response.text}")
