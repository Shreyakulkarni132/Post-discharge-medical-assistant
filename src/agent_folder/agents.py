from crewai import Agent
from dotenv import load_dotenv
load_dotenv()
import os
import sys 
'''
import asyncio
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
'''
from langchain_google_genai import ChatGoogleGenerativeAI

from tools import (
    database_tool,
    web_search_tool,
    rag_tool
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    verbose=True,
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY"),
    max_retries=3,  # Retry 3 times
    timeout=60,  # 60 second timeout
    # Add rate limiting
    request_timeout=30
)

receptionist_agent = Agent(
    role="Receptionist agent for post-discharge patient intake",
    goal=(
        "Collect patient identity, fetch the patient's discharge report from the database, "
        "ask relevant clarifying follow-up questions based on the discharge information, "
        "and route clinical medical queries to the Clinical AI Agent."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a friendly, empathetic medical receptionist agent. Your job is to gather the "
        "patient's name (or ID), retrieve their discharge summary using the database tool, "
        "ask follow-up questions that help the Clinical Agent (for example: current symptoms, "
        "medication adherence, allergies, vital signs if available), and then delegate clinical "
        "questions to the Clinical AI Agent. Always log interactions using the logger tool."
    ),
    llm=llm,
    tools=[database_tool],
    concurrent=False,  # Changed: Avoid concurrent calls
    allow_delegation=True,
    max_iter=10  # Limit iterations to avoid loops
)

clinical_agent = Agent(
    role="Clinical AI Agent specializing in post-discharge care using RAG and web search",
    goal=(
        "Answer clinical questions using RAG over the nephrology reference index. "
        "If the answer is not covered by the reference materials, use a web search tool to fetch "
        "Have a proper back and forth conversation with the patient, think of yourself as a real life medical assistant."
        "trusted sources. Provide concise answers, include citations to the reference materials or web sources, "
        "and log the full interaction. DO NOT provide definitive diagnoses; instead give guidance, recommended follow-ups, "
        "and emergency instructions when necessary."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a clinical support agent. You must base clinical advice on the provided nephrology textbook index (RAG). "
        "When outside the indexed content, you may perform a limited web search via SerpAPI and cite sources. "
        "Always include citations and a short reminder to contact a licensed clinician for definitive care. "
        "Log the question and the final answer. Never make ungrounded diagnostic claims."
    ),
    tools=[web_search_tool, rag_tool],
    llm=llm,
    concurrent=False,  # Changed: Avoid concurrent calls
    allow_delegation=True,
    max_iter=10  # Limit iterations
)


__all__ = ["receptionist_agent", "clinical_agent"]
