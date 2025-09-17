// public/js/chat.js

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent the form from reloading the page

        const question = userInput.value.trim();
        if (!question) return;

        // Display the user's message
        appendMessage(question, 'user-message');
        userInput.value = ''; // Clear the input field

        // Show a "thinking" indicator for the bot
        const thinkingMessage = appendMessage('...', 'bot-message thinking');

        try {
            // Send the question to the backend API
            const response = await fetch(`${BACKEND_URL}/api/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question }),
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }

            const data = await response.json();

            // Replace "thinking" message with the actual response
            thinkingMessage.querySelector('p').textContent = data.answer;
            thinkingMessage.classList.remove('thinking');

        } catch (error) {
            console.error('Error fetching bot response:', error);
            thinkingMessage.querySelector('p').textContent = 'Sorry, I am having trouble connecting to my brain right now. Please try again later.';
            thinkingMessage.classList.remove('thinking');
        }
    });

    function appendMessage(text, className) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', className);

        const messageP = document.createElement('p');
        messageP.textContent = text;

        messageDiv.appendChild(messageP);
        chatBox.appendChild(messageDiv);

        // Scroll to the bottom of the chat box
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageDiv;
    }
});