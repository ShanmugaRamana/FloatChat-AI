// This event listener ensures our script runs after the entire HTML page has loaded.
document.addEventListener('DOMContentLoaded', () => {

    // Get references to the essential HTML elements
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatLog = document.getElementById('chat-log');
    
    // API_BASE_URL is provided by a <script> tag in the EJS template (footer.ejs)

    /**
     * Handles the form submission event.
     */
    const handleSubmit = async (event) => {
        event.preventDefault(); // Prevent the default form submission (which reloads the page)

        const userQuery = chatInput.value.trim();
        if (!userQuery) return; // Don't send empty messages

        // 1. Display the user's message immediately
        addMessageToLog(userQuery, 'user');
        chatInput.value = ''; // Clear the input box
        chatInput.focus();

        // 2. Display a "thinking" message for the AI
        const thinkingMessage = addMessageToLog('Thinking...', 'assistant');
        
        try {
            // 3. Send the user's query to the backend API
            const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: userQuery,
                    model: "mistralai/mistral-7b-instruct:free"
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `API error: ${response.statusText}`);
            }

            const data = await response.json();
            
            // 4. Render the response
            if (data.answer) {
                // Format and display the text response
                const formattedAnswer = formatResponse(data.answer);
                thinkingMessage.innerHTML = formattedAnswer;
            } else {
                throw new Error("Invalid response from server.");
            }

        } catch (error) {
            console.error('Failed to get response from API:', error);
            thinkingMessage.textContent = `Sorry, something went wrong: ${error.message}`;
            thinkingMessage.classList.add('error');
        }
    };

    /**
     * Formats the AI response for better readability and organization.
     * @param {string} text - The raw response text.
     * @returns {string} - The formatted HTML string.
     */
    const formatResponse = (text) => {
        // Configure marked.js for better formatting
        marked.setOptions({
            breaks: true, // Convert single line breaks to <br>
            gfm: true,    // Enable GitHub Flavored Markdown
        });

        // Pre-process the text for better spacing
        let processedText = text
            // Add extra spacing around headers
            .replace(/^(#{1,6}\s+.+)$/gm, '\n$1\n')
            // Add spacing around code blocks
            .replace(/^```/gm, '\n```')
            .replace(/```$/gm, '```\n')
            // Add spacing around lists
            .replace(/^(\s*[\*\-\+]\s+.+)$/gm, (match, p1, offset, string) => {
                const prevChar = string[offset - 1];
                return (prevChar && prevChar !== '\n') ? '\n' + match : match;
            })
            // Add spacing around numbered lists
            .replace(/^(\s*\d+\.\s+.+)$/gm, (match, p1, offset, string) => {
                const prevChar = string[offset - 1];
                return (prevChar && prevChar !== '\n') ? '\n' + match : match;
            })
            // Ensure paragraphs have proper spacing
            .replace(/\n\n+/g, '\n\n')
            .trim();

        // Parse with marked.js
        let htmlContent = marked.parse(processedText);

        // Post-process the HTML for additional styling
        htmlContent = htmlContent
            // Add classes to different elements for better styling
            .replace(/<h([1-6])>/g, '<h$1 class="response-heading">')
            .replace(/<p>/g, '<p class="response-paragraph">')
            .replace(/<ul>/g, '<ul class="response-list">')
            .replace(/<ol>/g, '<ol class="response-ordered-list">')
            .replace(/<li>/g, '<li class="response-list-item">')
            .replace(/<pre>/g, '<pre class="response-code-block">')
            .replace(/<code>/g, '<code class="response-inline-code">')
            .replace(/<blockquote>/g, '<blockquote class="response-quote">');

        return htmlContent;
    };

    /**
     * Helper function to add a new message to the chat window.
     * @param {string} text - The message content.
     * @param {string} sender - 'user' or 'assistant'.
     * @returns {HTMLElement} - The message element that was added.
     */
    const addMessageToLog = (text, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        
        if (sender === 'assistant') {
            // For assistant messages, create a content wrapper for better spacing
            const contentWrapper = document.createElement('div');
            contentWrapper.classList.add('message-content');
            
            if (text === 'Thinking...') {
                // Simple text for thinking state
                contentWrapper.innerHTML = `<p class="thinking-message">${text}</p>`;
            } else {
                // Formatted response
                contentWrapper.innerHTML = formatResponse(text);
            }
            
            messageElement.appendChild(contentWrapper);
        } else {
            // For user messages, keep it simple but consistent
            const messageText = document.createElement('p');
            messageText.classList.add('user-text');
            messageText.textContent = text;
            messageElement.appendChild(messageText);
        }
        
        chatLog.appendChild(messageElement);

        // Scroll to the bottom of the chat log to show the latest message
        chatLog.scrollTop = chatLog.scrollHeight;
        return messageElement;
    };

    // Attach the event listener to the form to handle user submissions
    chatForm.addEventListener('submit', handleSubmit);
});