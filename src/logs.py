import json
from datetime import datetime
from pathlib import Path


class ConversationLogger:
    def __init__(self, log_file: str = "conversation_logs.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
    
    def log_session(self, patient_name: str, conversation: list):
        entry = {
            "patient_name": patient_name,
            "session_start": conversation[0]["timestamp"] if conversation else datetime.now().strftime("%H:%M"),
            "session_end": datetime.now().strftime("%H:%M %d-%m-%Y"),
            "messages": conversation
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        print(f" Logged session for {patient_name}")


# Global logger instance
logger = ConversationLogger()

def log_conversation(patient_name: str, conversation: list):
    """Log a conversation."""
    logger.log_session(patient_name, conversation)