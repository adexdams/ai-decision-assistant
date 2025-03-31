from backend.database import save_expert_selection

def log_interaction(session_id, user_input, experts_selected):
    """Logs user interactions by saving them in the database."""
    save_expert_selection(session_id, user_input, experts_selected)