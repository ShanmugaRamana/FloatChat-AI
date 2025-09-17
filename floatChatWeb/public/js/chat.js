// public/js/chat.js

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
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

        if (className.includes('bot-message')) {
            const html = converter.makeHtml(text);
        
            messageP.innerHTML = html;
        } else {
            messageP.textContent = text;
        }

        messageDiv.appendChild(messageP);
        chatBox.appendChild(messageDiv);
        
        // --- MODIFIED: Use scrollIntoView on the new message ---
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        
        return messageDiv;
    }

    function showLoadingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'bot-message');
        const indicatorDiv = document.createElement('div');
        indicatorDiv.classList.add('typing-indicator');
        indicatorDiv.innerHTML = '<span></span><span></span><span></span>';
        messageDiv.appendChild(indicatorDiv);
        chatBox.appendChild(messageDiv);
        
        // --- MODIFIED: Use scrollIntoView on the loading indicator ---
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });

        return messageDiv;
    }

    // The old scrollToBottom function is no longer needed and can be deleted.
});