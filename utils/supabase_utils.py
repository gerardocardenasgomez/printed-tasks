from supabase import create_client, Client
from datetime import datetime, timezone

# Cache supabase client and user_id
_cached_supabase_client = None
_cached_user_id = None
# Cache config
_supabase_url = None
_supabase_key = None
_user_email = None
_user_password = None

def init_supabase_config(supabase_url: str, supabase_key: str, user_email: str, user_password: str):
    global _supabase_url, _supabase_key, _user_email, _user_password

    _supabase_url = supabase_url
    _supabase_key = supabase_key
    _user_email = user_email
    _user_password = user_password

def get_supabase_client():
    global _cached_supabase_client, _cached_user_id

    if _cached_supabase_client is not None and _cached_user_id is not None:
        return (_cached_supabase_client, _cached_user_id)

    supabase_url = _supabase_url
    supabase_key = _supabase_key

    supabase: Client = create_client(supabase_url, supabase_key)

    auth_response = supabase.auth.sign_in_with_password({
        "email": _user_email,
        "password": _user_password
    })

    if hasattr(auth_response, "error") and auth_response.error:
        print(f"Error signing in: {auth_response.error}")
        raise Exception("Error signing in")

    if not hasattr(auth_response, 'user') or not auth_response.user:
        print(f"Error signing in: {auth_response}")
        raise Exception("Error signing in")

    return (supabase, auth_response.user.id)

def add_task(task_name, task_description, task_priority, task_ai_response=None):
    supabase, user_id = get_supabase_client()
    task = {
        "user_id": user_id,
        "task_name": task_name,
        "task_description": task_description,
        "task_priority": task_priority,
        # We do not set printed_on because the DB will generate this
    }
    
    if task_ai_response:
        task["task_ai_response"] = task_ai_response

    response = supabase.table("tasks").insert(task).execute()
    print(response)
    return response.data[0]["id"]

def complete_task_by_id(id):
    if id is None:
        print("Task ID Cannot be None")
        raise Exception("ID is None")

    supabase, user_id = get_supabase_client()

    utc_now = datetime.now(timezone.utc)

    response = supabase.table("tasks").update({
        "task_completed_on": utc_now.isoformat(),
        "task_completed": True,
    }).eq("id", id).eq("user_id", user_id).execute()

    print(response)

def search_tasks(search_term):
    supabase, user_id = get_supabase_client()

    response = supabase.table("tasks").select("*").eq("user_id", user_id).ilike("task_name", f"%{search_term}%").execute()
    # Example response:
    # [{'id': '8450304c-539b-46e6-beab-81e009edcf47', 'task_printed_on': '2025-08-06T20:03:53.189277+00:00', 'task_header': None, 'task_name': 'Test Task Delete this', 'task_description': 'This is a test task to delete', 'task_priority': 'LOW', 'task_ai_response': 'I am ChatGPT and I will be the best AI ever', 'user_id': '1e56f7e0-fcce-42ae-b8d7-7d9367f8cd51', 'task_completed_on': None, 'task_completed': False}]

    if len(response.data) == 0:
        return None

    return response.data 