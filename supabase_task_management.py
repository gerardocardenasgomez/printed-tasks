import argparse
from utils.supabase_utils import add_task, complete_task_by_id, search_tasks, init_supabase_config
from utils.utils import get_config
import os

config_path = os.path.join(os.path.dirname(__file__), "config.ini")
try:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=str, required=True, choices=["add_task", "complete_task", "search_tasks", "search_task"])
    parser.add_argument("-s", "--search_term", type=str, required=False)
    parser.add_argument("-i", "--task_id", type=str, required=False)
    args = parser.parse_args()
except Exception as e:
    print(f"Options: ")
    print(f"  -a <action> -- Actions are: add_task, complete_task, search_tasks, search_task")
    print(f"  -s <search_term> -- Search term for search_tasks | search_task")
    print(f"  -i <task_id> -- Task ID for complete_task")

config = get_config(config_path)

if (config.has_section("SUPABASE")):
    supabase_url = config.get("SUPABASE", "SUPABASE_URL")
    supabase_key = config.get("SUPABASE", "SUPABASE_API_KEY")
    user_email = config.get("SUPABASE", "SUPABASE_USER_EMAIL")
    user_password = config.get("SUPABASE", "SUPABASE_USER_PASSWORD")

    init_supabase_config(supabase_url, supabase_key, user_email, user_password)
else:
    raise Exception("No Supabase configuration found in config.ini")


if args.action == "add_task":
    print(f"Adding task: {args.search_term}")
    # We might add this later or maybe remove it I have not decided yet!
    # If we add it we need to get task_name, task_desc, and task_priority
    # but then what about ai_response?~
    # Maybe this can be the non_ai_response method idk yet
    #add_task("Test Task", "Test Description", "LOW")
elif args.action == "complete_task":
    print(f"Completing task: {args.task_id}")
    complete_task_by_id(args.task_id)
elif args.action == "search_tasks" or args.action == "search_task":
    print(f"searching tasks: {args.search_term}")
    result = search_tasks(args.search_term)
    # Example result: result: [{'id': '8450304c-539b-46e6-beab-81e009edcf47', 'task_printed_on': '2025-08-06T20:03:53.189277+00:00', 'task_header': None, 'task_name': 'Test Task Delete this', 'task_description': 'This is a test task to delete', 'task_priority': 'LOW', 'task_ai_response': 'I am ChatGPT and I will be the best AI ever', 'user_id': '<USER_ID>', 'task_completed_on': None, 'task_completed': False}]
    if result is not None:
        for task in result:
            print(f"Task ID: {task['id']}")
            print(f"Task Name: {task['task_name']}")
            print(f"Task Description: {task['task_description']}")
            print(f"Task Priority: {task['task_priority']}")
            print(f"Task AI Response: {task['task_ai_response']}")
            print(f"Task Completed: {task['task_completed']}")
            print(f"Task Completed On: {task['task_completed_on']}")
            print(f"Task Printed On: {task['task_printed_on']}")
            print(f"Task Header: {task['task_header']}")
            print(f"User ID: {task['user_id']}")
            # Real ones know this is printed on the receipt!
            print("*** ~*~ ***")
    else:
        print(f"No tasks found for search term: {args.search_term}")
else:
    print(f"Invalid action: {args.action}")
    exit(1)