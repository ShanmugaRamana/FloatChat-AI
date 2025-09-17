document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');

    // --- NEW: Create a Showdown converter instance ---
    const converter = new showdown.Converter();

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const question = userInput.value.trim();
        if (!question) return;

        appendMessage(question, 'user-message');
        userInput.value = '';

        const loadingIndicator = showLoadingIndicator();

        try {
            const response = await fetch(`${BACKEND_URL}/api/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
                const errorMessage = `Error: ${response.status} - ${errorData.detail || response.statusText}`;
                throw new Error(errorMessage);
            }

            const data = await response.json();
            
            loadingIndicator.remove();
            appendMessage(data.answer, 'bot-message');

        } catch (error) {
            console.error('Error fetching bot response:', error);
            loadingIndicator.remove();
            appendMessage(error.message, 'bot-message error-message');
        }
    });

    function appendMessage(text, className) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', className);

        const messageP = document.createElement('p');

        // --- MODIFIED: Use the converter for bot messages ---
        if (className.includes('bot-message')) {
            const html = converter.makeHtml(text); // Convert Markdown to HTML
            messageP.innerHTML = html; // Use innerHTML to render the formatting
        } else {
            messageP.textContent = text; // User messages are still plain text
        }

        messageDiv.appendChild(messageP);
        chatBox.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }

    function showLoadingIndicator() {
        // ... (this function is unchanged)
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'bot-message');
        const indicatorDiv = document.createElement('div');
        indicatorDiv.classList.add('typing-indicator');
        indicatorDiv.innerHTML = '<span></span><span></span><span></span>';
        messageDiv.appendChild(indicatorDiv);
        chatBox.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});