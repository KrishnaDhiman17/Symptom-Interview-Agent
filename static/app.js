document.addEventListener("DOMContentLoaded", () => {
    // --- DOM Elements ---
    const chatHistory = document.getElementById("chat-history");
    const interviewForm = document.getElementById("interview-form");
    const userInput = document.getElementById("user-input");
    const submitButton = document.getElementById("submit-button");
    const buttonText = document.getElementById("button-text");
    const loaderSpinner = document.getElementById("loader-spinner");
    const reportContainer = document.getElementById("report-container");
    const structuredReportDisplay = document.getElementById("structured-report-display");

    let isInterviewActive = false;
    let isRequestPending = false;

    // --- Utility Functions ---

    /**
     * Appends a message to the chat history.
     * @param {string} role - 'User' or 'Agent'
     * @param {string} text - The message content
     */
    function appendMessage(role, text) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", role.toLowerCase());

        const roleSpan = document.createElement("span");
        roleSpan.classList.add("role");
        roleSpan.textContent = role;

        const contentP = document.createElement("p");
        contentP.innerHTML = text.replace(/\n/g, "<br>"); // Use <br> for newline formatting

        messageDiv.appendChild(roleSpan);
        messageDiv.appendChild(contentP);
        chatHistory.appendChild(messageDiv);

        // Auto-scroll to the latest message
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    /**
     * Toggles the loading state of the submit button.
     * @param {boolean} isLoading - Whether a request is currently pending.
     * @param {string} [text] - Optional text to set on the button.
     */
    function toggleLoadingState(isLoading, text = null) {
        isRequestPending = isLoading;
        submitButton.disabled = isLoading;
        loaderSpinner.style.display = isLoading ? 'inline-block' : 'none';
        buttonText.textContent = text || (isLoading ? 'Processing...' : (isInterviewActive ? 'Send Response' : 'Start Interview'));
        
        // Disable input while waiting for response
        userInput.disabled = isLoading;
    }

    /**
     * Handles the interview submission (initial symptom or follow-up).
     */
    async function handleSubmission(event) {
        event.preventDefault();
        
        const text = userInput.value.trim();
        if (!text || isRequestPending) return;

        toggleLoadingState(true);

        // Append user message immediately
        appendMessage("User", text);
        userInput.value = ""; // Clear input field

        const endpoint = isInterviewActive ? '/continue_interview' : '/start_interview';
        const payload = isInterviewActive 
            ? { user_response: text }
            : { initial_symptom: text };
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            if (!isInterviewActive) {
                // Initial response
                isInterviewActive = true;
                userInput.placeholder = "Enter your response here...";
            }

            if (data.is_complete) {
                // Interview is complete, display report
                isInterviewActive = false;
                userInput.placeholder = "Interview complete. Start a new one above.";
                userInput.disabled = true;
                submitButton.style.display = 'none'; // Hide send button
                
                // Display the final agent message from the history
                const finalAgentMessage = data.history.findLast(m => m.role === 'System');
                if (finalAgentMessage) {
                    appendMessage("Agent", finalAgentMessage.text);
                }

                // Format and display the structured report JSON
                structuredReportDisplay.textContent = JSON.stringify(data.structured_report, null, 2);
                reportContainer.style.display = 'block';

            } else {
                // Continue interview, append agent's question
                appendMessage("Agent", data.next_question);
            }

        } catch (error) {
            console.error("Agent Request Failed:", error);
            // Display an error message to the user
            const errorMessage = `An error occurred: ${error.message}. Please refresh and try again.`;
            appendMessage("System Error", errorMessage);
            
            // Allow user to try again if it's not a severe error
            if (isInterviewActive) {
                userInput.value = text; // Put the user's last message back
            } else {
                // If initial start failed, keep state reset
                isInterviewActive = false;
                userInput.placeholder = "e.g., I have a headache.";
            }

        } finally {
            // Restore initial button text if the interview is complete
            if (!isInterviewActive) {
                toggleLoadingState(false, 'Start Interview');
                submitButton.style.display = 'inline-block';
            } else {
                toggleLoadingState(false);
            }
        }
    }

    // --- Event Listener ---
    interviewForm.addEventListener('submit', handleSubmission);

    // Initial state check for button text
    toggleLoadingState(false, 'Start Interview');
});