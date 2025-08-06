import argparse
from supabase_utils import add_task, complete_task_by_id, search_tasks

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--action", type=str, required=True, choices=["add_task", "complete_task", "search_tasks", "search_task"])
parser.add_argument("-s", "--search_term", type=str, required=False)
parser.add_argument("-i", "--task_id", type=str, required=False)
args = parser.parse_args()

if args.action == "add_task":
    print(f"adding task: {args.search_term}")
    #add_task("Test Task", "Test Description", "LOW")
elif args.action == "complete_task":
    print(f"completing task: {args.task_id}")
    #complete_task_by_id(args.task_id)
elif args.action == "search_tasks" or args.action == "search_task":
    print(f"searching tasks: {args.search_term}")
    #search_tasks(args.search_term)
else:
    print(f"Invalid action: {args.action}")
    exit(1)