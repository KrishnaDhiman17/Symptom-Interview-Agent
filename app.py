from flask import Flask, request, jsonify, render_template
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get API key from environment variable
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable is not set!")
    print("Please set it using: $env:GEMINI_API_KEY='your-api-key-here' (PowerShell)")
    exit(1)

# Set environment variable for litellm
os.environ["GEMINI_API_KEY"] = api_key

# Import litellm for Gemini access
import litellm
litellm.set_verbose = False

# Import CrewAI
from crewai import Agent, Task, Crew

# --- New Global State for Conversation ---
# Stores the current interview context (questions asked, answers given)
interview_context = {
    "interview_id": 1,
    "conversation_history": [],
    "is_complete": False,
    "initial_symptom": None
}

# Initialize LLM
llm = "gemini/gemini-2.0-flash"
print("Initializing LLM:", llm)

# --- Agent Definitions for Symptom Interview ---
print("Creating Symptom Interview Agents...")

# 1. Interviewer Agent: Drives the conversation
interviewer_agent = Agent(
    role="Conversational Interviewer",
    goal="Guide the user through a non-diagnostic symptom interview by asking one structured, open-ended question at a time. The interview must be structured to gather details on onset, duration, severity, and modifying factors of a symptom. Never provide a diagnosis or medical advice.",
    backstory="You are a meticulous, empathetic medical intake specialist (non-physician) who excels at gathering detailed, relevant information about a patient's symptoms through a structured, safe conversational flow.",
    llm=llm
)

# 2. Report Generator Agent: Creates the final structured report
report_agent = Agent(
    role="Structured Report Generator",
    goal="Compile the full conversation history into a concise, structured non-diagnostic report for a medical professional. The report must be easy to read and only include facts gathered, not any diagnostic opinions.",
    backstory="You are a clinical documentation expert who converts raw interview transcripts into professional, structured SOAP (Subjective, Objective, Assessment, Plan) style reports, focusing only on the Subjective and Objective parts from the user's input.",
    llm=llm,
    verbose=True
)
print("Symptom Interview Agents created.")

def generate_report(context):
    """
    Kicks off the Report Generator Agent to create the final structured report.
    """
    full_history = "\n".join([f"{item['role']}: {item['text']}" for item in context["conversation_history"]])
    
    report_task = Task(
        description=f"""
        Generate a structured, non-diagnostic symptom report based on the following conversation history.
        The report must follow this exact JSON format. Only include information explicitly mentioned in the history.
        
        Conversation History:
        ---
        {full_history}
        ---
        
        Return ONLY the valid JSON structure without any other text or markdown:
        {{
            "report_title": "Symptom Interview Report for [Initial Symptom]",
            "safety_disclaimer": "This is a non-diagnostic, AI-generated intake report and is not a substitute for professional medical evaluation.",
            "sections": [
                {{
                    "heading": "Chief Complaint",
                    "content": "Patient reports: [Initial Symptom]"
                }},
                {{
                    "heading": "History of Present Illness (HPI)",
                    "content": "Organize the patient's answers into a clear narrative covering: Onset, Location/Quality, Severity, Duration, Modifying Factors (what makes it better/worse), and Associated Symptoms."
                }},
                {{
                    "heading": "Review of Systems (ROS)",
                    "content": "List any other systems/symptoms mentioned by the patient."
                }}
            ]
        }}
        """,
        expected_output="Valid JSON object containing the structured, non-diagnostic symptom report.",
        agent=report_agent
    )
    
    report_crew = Crew(agents=[report_agent], tasks=[report_task])
    try:
        report_result = report_crew.kickoff()
        # Clean up result if it's wrapped in markdown
        report_text = str(report_result).strip()
        if report_text.startswith('```') and report_text.endswith('```'):
            report_text = report_text.split('\n', 1)[1].rsplit('\n', 1)[0].strip()
        return json.loads(report_text)
    except Exception as e:
        print(f"Error generating report: {e}")
        return {"error": f"Failed to generate structured report: {str(e)}"}


def get_next_question(history, initial_symptom):
    """
    Kicks off the Interviewer Agent to generate the next question.
    """
    formatted_history = "\n".join([f"{item['role']}: {item['text']}" for item in history])
    
    # Define the structured interview flow based on standard HPI
    interview_steps = [
        "What is the exact location, quality (e.g., sharp, dull), and severity (on a scale of 1-10) of the symptom?",
        "When did this symptom first start, and how has it changed over time (e.g., constant, intermittent)?",
        "What makes the symptom better, and what makes it worse?",
        "Are you experiencing any other related symptoms, even minor ones?"
    ]
    
    current_step = len([item for item in history if item['role'] == 'User'])
    
    if current_step == 0:
        # Initial question already asked, this is the first real follow-up
        next_q = interview_steps[0]
    elif current_step <= len(interview_steps):
        # Subsequent questions following the HPI steps
        next_q = interview_steps[current_step - 1]
    else:
        # Final, open-ended follow-up before reporting
        return "Is there anything else you think is important for a doctor to know about this symptom or your overall health right now?"
        
    question_task = Task(
        description=f"""
        Based on the history and the initial symptom ('{initial_symptom}'), generate the next single, best follow-up question.
        The question MUST be one of the core elements of a standard medical interview (HPI - History of Present Illness) to gather necessary details for the report.
        
        The next specific topic to cover is: '{next_q}'.
        
        Current Conversation History:
        ---
        {formatted_history}
        ---
        
        Generate ONLY the single question text. Do NOT include a diagnosis or medical advice.
        """,
        expected_output="A single, non-diagnostic follow-up question.",
        agent=interviewer_agent
    )
    
    interview_crew = Crew(agents=[interviewer_agent], tasks=[question_task])
    try:
        question_result = interview_crew.kickoff()
        return str(question_result).strip()
    except Exception as e:
        print(f"Error generating question: {e}")
        return "I apologize, an error occurred. Can you please summarize your symptoms one more time?"

# --- Flask Routes ---

@app.route('/')
def index():
    # Reuse the existing index.html which will be adapted in the frontend
    return render_template('index.html')

@app.route('/start_interview', methods=['POST'])
def start_interview():
    """Starts a new interview session."""
    global interview_context
    print("Starting new interview...")
    
    try:
        data = request.get_json()
        initial_symptom = data.get('initial_symptom', '').strip()
        
        if not initial_symptom:
            return jsonify({'error': 'Please provide an initial symptom to start the interview.'}), 400
        
        # Reset and initialize context
        interview_context = {
            "interview_id": interview_context['interview_id'] + 1,
            "conversation_history": [
                {"role": "User", "text": initial_symptom}
            ],
            "is_complete": False,
            "initial_symptom": initial_symptom
        }
        
        # Initial response from the system
        initial_question = f"Thank you for sharing your symptom: '{initial_symptom}'. To begin, can you tell me when you first noticed this symptom?"
        
        interview_context["conversation_history"].append({
            "role": "Agent",
            "text": initial_question
        })
        
        print("Interview started successfully.")
        return jsonify({
            'interview_id': interview_context['interview_id'],
            'initial_question': initial_question,
            'history': interview_context['conversation_history']
        })
    except Exception as e:
        print(f"Error starting interview: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/continue_interview', methods=['POST'])
def continue_interview():
    """Handles user response and generates the next question."""
    global interview_context
    print(f"Continuing interview {interview_context['interview_id']}...")
    
    try:
        if interview_context["is_complete"]:
            return jsonify({'error': 'Interview is already complete. Please start a new one.'}), 400
            
        data = request.get_json()
        user_response = data.get('user_response', '').strip()
        
        if not user_response:
            return jsonify({'error': 'Please provide a response to continue.'}), 400
        
        # Append user's response to history
        interview_context["conversation_history"].append({
            "role": "User",
            "text": user_response
        })
        
        # Check if the interview is ready for reporting (based on number of turns)
        user_turn_count = len([item for item in interview_context["conversation_history"] if item['role'] == 'User'])
        
        if user_turn_count >= 5: # A good conversational length to gather enough details
            interview_context["is_complete"] = True
            
            # Kick off the Report Generator
            report = generate_report(interview_context)
            
            interview_context["conversation_history"].append({
                "role": "System",
                "text": "The interview is complete. Thank you for your patience. I have generated a structured report for review. Please find the JSON report below."
            })
            
            return jsonify({
                'interview_id': interview_context['interview_id'],
                'next_question': None, # Signal to frontend that conversation is over
                'is_complete': True,
                'structured_report': report,
                'history': interview_context['conversation_history']
            })
        
        # Generate the next question
        next_question = get_next_question(
            interview_context["conversation_history"], 
            interview_context["initial_symptom"]
        )
        
        # Append agent's question to history
        interview_context["conversation_history"].append({
            "role": "Agent",
            "text": next_question
        })
        
        return jsonify({
            'interview_id': interview_context['interview_id'],
            'next_question': next_question,
            'is_complete': False,
            'history': interview_context['conversation_history']
        })
        
    except Exception as e:
        print(f"Error continuing interview: {e}")
        # Reset the interview on major error
        interview_context["is_complete"] = True 
        return jsonify({'error': f'An unexpected error occurred during the interview process: {str(e)}'}), 500

@app.route('/get_report', methods=['GET'])
def get_report():
    """Retrieves the final structured report if the interview is complete."""
    global interview_context
    if not interview_context["is_complete"]:
        return jsonify({'error': 'Interview is not yet complete. Cannot generate report.'}), 400
    
    # Regenerate the report if not yet generated or if directly requested
    report = generate_report(interview_context)
    return jsonify(report)


if __name__ == '__main__':
    print("Starting Flask app...")
    port = int(os.environ.get('PORT', 5000))
    # Note: debug=True is okay for local development, but use a proper WSGI server (like gunicorn) for production.
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)