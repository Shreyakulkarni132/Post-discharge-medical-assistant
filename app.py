from flask import Flask, render_template_string, request, redirect, url_for
from datetime import datetime
import sys
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

# Add src folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Try importing crew logic
try:
    from agent_folder.crew import run_post_discharge_workflow # type: ignore
except Exception as e:
    print(f"[Warning] Could not import crew workflow: {e}")
    run_post_discharge_workflow = None

try:
    from logs import log_conversation # type: ignore
except:
    log_conversation = None

# Import LLM for response formatting
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    formatting_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.3,
    )
    print("Response formatting LLM initialized")
except Exception as e:
    print(f"Could not initialize formatting LLM: {e}")
    formatting_llm = None

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Store results
responses = {}

def extract_message_from_json(raw_text: str) -> str:
    """Extract actual messages from JSON log structure"""
    import re
    import json
    
    # Try to parse as JSON first
    try:
        # Remove markdown code blocks
        cleaned = raw_text.strip()
        if cleaned.startswith('```'):
            cleaned = re.sub(r'^```json\s*', '', cleaned)
            cleaned = re.sub(r'```\s*$', '', cleaned)
            cleaned = cleaned.strip()
        
        data = json.loads(cleaned)
        
        messages = []
        
        # Handle different JSON structures
        if isinstance(data, dict):
            if 'interaction_log' in data:
                for entry in data['interaction_log']:
                    if isinstance(entry, dict) and 'message' in entry:
                        msg = entry['message']
                        if len(msg) > 50 and 'fever' in msg.lower():  # Substantial medical content
                            messages.append(msg)
            elif 'log_entries' in data:
                for entry in data['log_entries']:
                    if isinstance(entry, dict) and 'content' in entry:
                        msg = entry['content']
                        if isinstance(msg, str) and len(msg) > 50:
                            messages.append(msg)
        elif isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    if 'message' in entry:
                        msg = entry['message']
                        if len(msg) > 50:
                            messages.append(msg)
                    elif 'content' in entry:
                        msg = entry['content']
                        if isinstance(msg, str) and len(msg) > 50:
                            messages.append(msg)
        
        # Return the longest/most substantial message
        if messages:
            return max(messages, key=len)
            
    except json.JSONDecodeError:
        pass
    
    return raw_text


def format_agent_response(raw_response: str, patient_name: str, user_query: str) -> str:
    """
    Use LLM to clean up and format the agent's raw output.
    """
    # First, try to extract meaningful content from JSON
    extracted = extract_message_from_json(raw_response)
    
    print(f"\n=== EXTRACTED FROM JSON ===")
    print(extracted[:300])
    print(f"===========================\n")
    
    if not formatting_llm:
        return extracted
    
    try:
        formatting_prompt = f"""You are a medical assistant. A patient asked a question and received this response. Rewrite it to be clear and direct.

Patient: {patient_name}
Question: {user_query}

Response to clean up:
{extracted}

Your task:
1. Remove any JSON artifacts, timestamps, or technical references
2. Write as if YOU are directly answering the patient
3. Keep all medical information (symptoms, medications, instructions)
4. Use clear paragraphs
5. Be professional and empathetic
6. Do NOT add information not in the original response

Write the cleaned response now (NO preamble, NO explanations, just the direct answer to the patient):"""

        result = formatting_llm.invoke(formatting_prompt)
        
        # Extract content
        if hasattr(result, 'content'):
            formatted = result.content.strip()
        else:
            formatted = str(result).strip()
        
        # Remove any remaining JSON markers
        formatted = formatted.replace('```json', '').replace('```', '').strip()
        
        print(f"\n=== FINAL FORMATTED OUTPUT ===")
        print(formatted[:500])
        print(f"==============================\n")
        
        # If formatted response still looks like JSON, use extracted version
        if formatted.startswith('{') or formatted.startswith('['):
            print("Warning: LLM returned JSON, using extracted version")
            return extracted
        
        return formatted
            
    except Exception as e:
        print(f"Error formatting response: {e}")
        traceback.print_exc()
        return extracted


# Minimal HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>After Doctor - Post Discharge Assistant</title>
    <meta charset="UTF-8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            background: white;
        }
        
        .header {
            background: #ff8c42;
            color: white;
            padding: 20px;
            text-align: center;
            width: 100%;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: normal;
        }
        
        .container {
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .info-text {
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: bold;
        }
        
        input[type="text"],
        textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            font-size: 14px;
            font-family: Arial, sans-serif;
        }
        
        input[type="text"]:focus,
        textarea:focus {
            outline: none;
            border-color: #ff8c42;
        }
        
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .hint {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        
        button {
            background: #ff8c42;
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            cursor: pointer;
        }
        
        button:hover {
            background: #ff7a29;
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #ff8c42;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .result-section {
            margin-top: 30px;
        }
        
        .result-header {
            border-bottom: 2px solid #ff8c42;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .result-header strong {
            color: #333;
        }
        
        .result-header .date {
            color: #999;
            font-size: 14px;
            float: right;
        }
        
        .query-box {
            background: #f9f9f9;
            padding: 15px;
            margin-bottom: 20px;
            border-left: 3px solid #ff8c42;
        }
        
        .query-box h3 {
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
            font-weight: bold;
        }
        
        .response-box {
            background: #f9f9f9;
            padding: 20px;
            line-height: 1.8;
            white-space: pre-wrap;
            border-left: 3px solid #4caf50;
        }
        
        .response-box h3 {
            font-size: 14px;
            color: #4caf50;
            margin-bottom: 15px;
            font-weight: bold;
        }
        
        .error-box {
            background: #fff5f5;
            border: 1px solid #f44336;
            padding: 15px;
            color: #d32f2f;
        }
        
        .btn-new {
            margin-top: 20px;
            background: #666;
        }
        
        .btn-new:hover {
            background: #555;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>After Doctor - Your Post Discharge Assistant</h1>
    </div>

    <div class="container">
        {% if not result %}
            <p class="info-text">
                Enter your full name and ask any question about your post-discharge care. 
                Our AI will retrieve your medical records and provide personalized guidance.
            </p>
            
            <form method="post" action="{{ url_for('process') }}" id="mainForm">
                <div class="form-group">
                    <label for="patient_name">Patient Full Name</label>
                    <input type="text" 
                           id="patient_name" 
                           name="patient_name" 
                           placeholder="Enter your complete name as in medical records"
                           required 
                           autofocus>
                    <div class="hint">Use your full name exactly as it appears in your discharge documents</div>
                </div>
                
                <div class="form-group">
                    <label for="user_query">Your Question</label>
                    <textarea id="user_query" 
                              name="user_query" 
                              placeholder="Example: What medications should I take? When is my follow-up appointment?"
                              required></textarea>
                </div>
                
                <button type="submit" id="submitBtn">Get Medical Guidance</button>
            </form>
            
            <div class="loading" id="loadingDiv">
                <div class="spinner"></div>
                <p>Fetching your medical records and generating response...</p>
                <p style="font-size: 14px; color: #999; margin-top: 10px;">This may take 30-60 seconds</p>
            </div>
        {% else %}
            <div class="result-section">
                <div class="result-header">
                    <strong>Patient: {{ result.patient_name }}</strong>
                    <span class="date">{{ result.timestamp }}</span>
                    <div style="clear: both;"></div>
                </div>
                
                <div class="query-box">
                    <h3>Your Question:</h3>
                    <p>{{ result.query }}</p>
                </div>
                
                {% if result.success %}
                    <div class="response-box">
                        <h3>Medical Guidance:</h3>
                        <div>{{ result.response }}</div>
                    </div>
                {% else %}
                    <div class="error-box">
                        <strong>Error:</strong> {{ result.error }}
                    </div>
                {% endif %}
                
                <form method="post" action="{{ url_for('reset') }}">
                    <button type="submit" class="btn-new">Ask Another Question</button>
                </form>
            </div>
        {% endif %}
    </div>

    <footer style="background-color:#f8f9fa; padding:15px 0; text-align:center; font-size:14px; color:#555; border-top:1px solid #ddd; margin-top:30px;">
        <p><strong>Medical Disclaimer:</strong> This is an AI assistant for educational purposes only.</p>
        <p>Always consult healthcare professionals for medical advice.</p>
    </footer>


    <script>
        const form = document.getElementById('mainForm');
        if (form) {
            form.addEventListener('submit', function(e) {
                const name = document.getElementById('patient_name').value.trim();
                const query = document.getElementById('user_query').value.trim();
                
                if (!name || !query) {
                    e.preventDefault();
                    alert('Please fill in both fields');
                    return;
                }
                
                form.style.display = 'none';
                document.querySelector('.info-text').style.display = 'none';
                document.getElementById('loadingDiv').classList.add('active');
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    result = request.args.get('result_id')
    result_data = None
    
    if result and result in responses:
        result_data = responses[result]
    
    return render_template_string(HTML_TEMPLATE, result=result_data)


@app.route("/process", methods=["POST"])
def process():
    patient_name = request.form.get("patient_name", "").strip()
    user_query = request.form.get("user_query", "").strip()
    
    if not patient_name or not user_query:
        return redirect(url_for("home"))
    
    result_data = {
        "patient_name": patient_name,
        "query": user_query,
        "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "success": False,
        "response": "",
        "error": ""
    }
    
    if run_post_discharge_workflow:
        try:
            print(f"\n{'='*60}")
            print(f"Processing request for: {patient_name}")
            print(f"Query: {user_query}")
            print(f"{'='*60}\n")
            
            crew_result = run_post_discharge_workflow(
                patient_name=patient_name,
                user_query=user_query
            )
            
            print(f"\nCrew result success: {crew_result.get('success')}")
            
            if crew_result and crew_result.get("success"):
                raw_response = crew_result.get("message", "") or crew_result.get("raw", "")
                
                print(f"\n=== RAW RESPONSE ===")
                print(raw_response[:500])
                print(f"====================\n")
                
                if raw_response and len(raw_response.strip()) > 0:
                    # Format the response using LLM
                    print("Formatting response with LLM...")
                    formatted_response = format_agent_response(
                        raw_response=raw_response,
                        patient_name=patient_name,
                        user_query=user_query
                    )
                    
                    result_data["success"] = True
                    result_data["response"] = formatted_response
                else:
                    result_data["error"] = "No response generated. Please try rephrasing your question."
            else:
                error_msg = crew_result.get("error", "Unknown error")
                print(f"Crew execution failed: {error_msg}")
                
                if "No record found" in error_msg or "not found" in error_msg.lower():
                    result_data["error"] = f"Patient record not found for '{patient_name}'. Please verify your complete name matches your discharge documents."
                else:
                    result_data["error"] = f"Processing failed: {error_msg}"
                
        except Exception as e:
            print(f"Error during processing:")
            traceback.print_exc()
            result_data["error"] = f"System error: {str(e)}"
    else:
        result_data["error"] = "AI system not available. Please check configuration."
    
    # Store result
    result_id = f"{patient_name.replace(' ', '_')}_{int(datetime.now().timestamp())}"
    responses[result_id] = result_data
    
    # Log conversation
    if log_conversation and result_data["success"]:
        try:
            chat_log = [
                {"role": "user", "content": user_query, "timestamp": result_data["timestamp"]},
                {"role": "assistant", "content": result_data["response"], "timestamp": result_data["timestamp"]}
            ]
            log_conversation(patient_name, chat_log)
            print(f"Conversation logged for {patient_name}")
        except Exception as e:
            print(f"Failed to log conversation: {e}")
    
    return redirect(url_for("home", result_id=result_id))


@app.route("/reset", methods=["POST"])
def reset():
    return redirect(url_for("home"))


if __name__ == "__main__":
    print("\n" + "="*60)
    print("After Doctor - Post Discharge Assistant Starting...")
    print("="*60)
    print(f"Access at: http://localhost:5001")
    print("="*60 + "\n")
    
    app.run(port=5001, debug=True, use_reloader=False)