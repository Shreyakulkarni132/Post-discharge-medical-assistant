from crewai import Crew
import os
import sys
from dotenv import load_dotenv
import json

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from agents import receptionist_agent, clinical_agent
from tasks import (
    fetch_patient_discharge_task,
    followup_questionnaire_task,  # Re-added for initialization
    clinical_query_task, 
    rag_indexing_task
)

def extract_crew_output(result):
    """Extract meaningful text from CrewAI result"""
    try:
        if hasattr(result, 'output'):
            return str(result.output)
        if hasattr(result, 'raw'):
            return str(result.raw)
        if isinstance(result, dict):
            if 'output' in result:
                return str(result['output'])
            if 'raw' in result:
                return str(result['raw'])
        if hasattr(result, 'tasks_output') and result.tasks_output:
            # For init: get the followup_questionnaire_task output (index -2)
            # For chat: get the clinical_query_task output (index -1)
            outputs = []
            for task_output in result.tasks_output:
                if hasattr(task_output, 'raw'):
                    raw = str(task_output.raw).strip()
                    # Skip empty or system messages
                    if raw and len(raw) > 10 and not raw.startswith("Logged"):
                        outputs.append(raw)
            if outputs:
                # Return the last meaningful output
                return outputs[-1]
        return str(result)
    except Exception as e:
        print(f"⚠️ Error extracting output: {e}")
        return str(result)


def create_initialization_crew():
    """Crew for initial setup: fetch records, ask follow-up questions, index RAG"""
    crew = Crew(
        agents=[receptionist_agent, clinical_agent],
        tasks=[
            fetch_patient_discharge_task,
            followup_questionnaire_task,  # Asks questions ONCE
            rag_indexing_task
        ],
        verbose=False
    )
    return crew


def create_chat_crew():
    """Crew for answering user questions using RAG"""
    crew = Crew(
        agents=[clinical_agent],
        tasks=[clinical_query_task],
        verbose=False  # Disable verbose
    )
    return crew


def run_post_discharge_workflow(patient_name: str, user_query: str = None):
    """
    Main workflow function:
    - If user_query is None → Initialization (fetch records)
    - If user_query is provided → Answer the query
    """
    try:
        if not patient_name or not isinstance(patient_name, str):
            return {"success": False, "error": "Invalid patient name"}

        if user_query:
            # ===== CHAT MODE - Answer user's question =====
            print(f"\n💬 Answering: {user_query[:50]}...")
            
            crew = create_chat_crew()
            result = crew.kickoff(inputs={
                "patient_name": patient_name,
                "user_query": user_query
            })
            
            response_text = extract_crew_output(result)
            
            return {
                "success": True,
                "message": response_text,
                "patient_name": patient_name,
                "mode": "chat"
            }
        
        else:
            # ===== INITIALIZATION MODE - Load patient + Ask follow-up questions =====
            print(f"\n🚀 Initializing session for: {patient_name}")
            
            crew = create_initialization_crew()
            result = crew.kickoff(inputs={
                "patient_name": patient_name,
                "context": f"Patient {patient_name} just started consultation. Fetch discharge summary and conduct initial follow-up assessment."
            })
            
            response_text = extract_crew_output(result)
            
            # The response should contain the follow-up questions and assessment
            return {
                "success": True,
                "message": response_text,
                "patient_name": patient_name,
                "mode": "init"
            }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test
    test_name = "Ram Ban"
    
    print("=" * 60)
    print("TEST 1: Initialize")
    print("=" * 60)
    result = run_post_discharge_workflow(test_name)
    print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 60)
    print("TEST 2: Ask Question")
    print("=" * 60)
    result = run_post_discharge_workflow(test_name, "What medications should I take?")
    print(json.dumps(result, indent=2))