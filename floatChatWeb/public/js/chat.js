// public/js/chat.js

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const question = userInput.value.trim();
        if (!question) return;

        appendMessage(question, 'user-message');
        userInput.value = '';

        // NEW: Show the typing animation
        const loadingIndicator = showLoadingIndicator();

        try {
            const response = await fetch(`${BACKEND_URL}/api/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question }),
            });

            // NEW: Improved error handling
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
                const errorMessage = `Error: ${response.status} - ${errorData.detail || response.statusText}`;
                throw new Error(errorMessage);
            }

            const data = await response.json();
            
            // Remove the loading indicator and display the real message
            loadingIndicator.remove();
            appendMessage(data.answer, 'bot-message');

        } catch (error) {
            console.error('Error fetching bot response:', error);
            // Remove the loading indicator and show an error message in the chat
            loadingIndicator.remove();
            appendMessage(error.message, 'bot-message error-message');
        }
    });

    function appendMessage(text, className) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', className);

        const messageP = document.createElement('p');
        messageP.textContent = text;

        messageDiv.appendChild(messageP);
        chatBox.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }

    // NEW: Function to create and show the loading animation
    function showLoadingIndicator() {
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