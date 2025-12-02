That's the final piece of documentation\! A detailed `README.md` is essential for any project. It will explain the **Symptom Interview Agent**'s purpose, structure, and how to set it up and run it.

Here is a comprehensive `README.md` file for your repository.

```markdown
# 🩺 Symptom Interview Agent (SIA)

A full-stack **Agentic AI** application designed to conduct a structured, non-diagnostic symptom interview and generate a professional intake report.

The application uses **Flask** for the web interface and **CrewAI** to orchestrate specialized Gemini-powered agents, ensuring a safe, structured, and compliant pre-screening process.

## ✨ Features

* **Non-Diagnostic:** Explicitly designed to **never provide a diagnosis or medical advice**, functioning purely as an information collection tool.
* **Structured Interview Flow:** Agents follow a systematic process (similar to a medical HPI: History of Present Illness) to gather details on onset, duration, severity, and modifying factors.
* **Agent Collaboration:** Uses a crew of two specialized agents to drive conversation and compile documentation.
* **Structured Output:** Generates a clean, organized **JSON report** ready for review by a healthcare professional.
* **Web Interface:** Simple, conversational chat interface built with HTML, CSS, and JavaScript.

## ⚙️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | **Python (Flask)** | Web server and API endpoints. |
| **Agent Orchestration** | **CrewAI** | Manages agent roles, goals, and task collaboration. |
| **Large Language Model** | **Gemini (via `litellm`)** | Powers the agents' reasoning and generation capabilities. |
| **Server** | **Gunicorn** | Production-ready WSGI server. |
| **Frontend** | **HTML/CSS/JavaScript** | Conversational user interface. |

## 📦 Project Structure

The project follows a standard Flask structure to cleanly separate logic from presentation.

```

Agentic\_AI\_2/
├── .env                  \# Environment variables (API Key, Port) - IGNORED BY GIT
├── .gitignore            \# Specifies files to exclude from Git
├── app.py                \# **Flask Backend & CrewAI Logic**
├── requirements.txt      \# Python dependencies
├── Procfile              \# Render/Heroku deployment instruction
├── templates/
│   └── index.html        \# Main conversational web interface
└── static/
├── app.js            \# Frontend JavaScript logic (handles chat flow)
└── style.css         \# Styling for the application

````

## 🚀 Getting Started

Follow these steps to set up and run the application locally.

### 1. Prerequisites

You must have **Python 3.10+** installed.

### 2. Setup Environment

Navigate to the root directory of your project and set up a virtual environment:

```bash
# Create and activate virtual environment (Windows/macOS/Linux)
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
````

### 3\. Install Dependencies

Install all required Python libraries, including Flask, CrewAI, and Gunicorn.

```bash
pip install -r requirements.txt
```

### 4\. Configure API Key

The application requires a **Gemini API Key** to function.

1.  Get your key from [Google AI Studio](https://ai.google.dev/).
2.  Create a file named `.env` in the project root directory.
3.  Add your API key to the file:

<!-- end list -->

```dotenv
# .env file content
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
PORT=5000
```

### 5\. Run the Application

Start the Flask development server:

```bash
python app.py
```

You should see output indicating the server is running:

```
Starting Flask app...
 * Running on [http://127.0.0.1:5000](http://127.0.0.1:5000)
```

### 6\. Access the App

Open your web browser and go to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

## 👤 Agent Roles

The application uses two primary agents orchestrated by the CrewAI framework:

| Agent | Role | Goal |
| :--- | :--- | :--- |
| **Conversational Interviewer** | Guides the user through a non-diagnostic symptom interview. | To gather detailed, structured information on the patient's chief complaint (Onset, Location, Duration, Severity, Modifying Factors, Associated Symptoms). |
| **Structured Report Generator** | Clinical documentation expert. | To compile the entire conversation history into a concise, professional, structured JSON report suitable for a medical professional's review. |

## ⚠️ Safety Disclaimer

This application is for **demonstration and informational purposes only**. It is explicitly **NON-DIAGNOSTIC**. It does not replace, nor is it a substitute for, professional medical advice, diagnosis, or treatment. **Always seek the advice of a qualified health provider** with any questions you may have regarding a medical condition.

```
```
