from crewai import Task
from agents import receptionist_agent, clinical_agent


# RECEPTIONIST AGENT TASKS

fetch_patient_discharge_task = Task(
    name="Fetch Patient Discharge Report",
    description=(
        "You will take the patient name as input, Fetch the discharge report for patient: {patient_name}."
        "The input 'patient_name' is passed from inputs, do not use {patient_name} literally. "
        "Retrieve the discharge summary for the patient whose name is provided as input. Use the variable 'patient_name' passed from inputs, do not use {patient_name} literally."
        "and ensure the correct patient data is fetched. Handle cases where multiple or no matches are found."
    ),
    agent=receptionist_agent,
    expected_output=(
        "A structured discharge summary containing patient name, admission details, diagnosis, treatment, "
        "and discharge recommendations retrieved from the database."
    ),
)

followup_questionnaire_task = Task(
    name="Post-Discharge Follow-up Questionnaire",
    description=(
        "Using the discharge report, ask relevant follow-up questions related to the patient's current health status, "
        "medication adherence, vital signs, and any complications post-discharge. Route clinical queries to the "
        "Clinical AI Agent as needed."
    ),
    agent=receptionist_agent,
    expected_output=(
        "A structured record of follow-up responses and observations, with any medical questions redirected "
        "to the Clinical AI Agent for detailed guidance."
    ),
    context=[fetch_patient_discharge_task]
)


# CLINICAL AI AGENT TASKS

clinical_query_task = Task(
    name="Clinical Question Answering",
    description="""
    Answer the patient's question: {user_query}
    "To give a summary of all all the data you retieved while searching the results, in a consise manner."
    Use the indexed discharge report and medical records for patient {patient_name}.
    Provide accurate, personalized medical guidance based on their specific condition.
    Do not return {user_query} and {patient_name} literally; use the actual inputs provided.
    """,
    expected_output="""
    A clear, accurate answer to the patient's question with:
    - Direct response to their query
    - Relevant information from their discharge report
    - Any important safety warnings or follow-up recommendations
    - Suggested tablets/medications/treatements/things to do it feel better
    (ALL IN A CONCISE MANNER, BRIEF AND QUICK)
    """,
    agent=clinical_agent,  # This should be defined in agents.py
    context=[followup_questionnaire_task, fetch_patient_discharge_task]
)

rag_indexing_task = Task(
    name="Build RAG Knowledge Base",
    description=(
        "Process nephrology reference materials, chunk them, generate embeddings, and store them in a vector database. "
        "Implement semantic retrieval for clinical question answering. Include citations in all responses."
    ),
    agent=clinical_agent,
    expected_output=(
        "A functional RAG pipeline capable of retrieving and generating nephrology-based answers."
    ),
    context=[clinical_query_task]
)

logging_task = Task(
    name="System Interaction Logging",
    description=(
        "Log all interactions between agents and patients, including queries, retrieved information, agent handoffs, "
        "and web search invocations. Store logs with timestamps and agent identifiers."
    ),
    agent=receptionist_agent,
    expected_output=(
        "A detailed interaction log (JSON or database entry) containing timestamps, query types, agent responses, "
        "and any system actions taken during the workflow."
    ),
)

__all__ = [
    "fetch_patient_discharge_task",
    "followup_questionnaire_task",
    "clinical_query_task",
    "rag_indexing_task",
    "logging_task",
]
