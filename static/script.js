document.addEventListener('DOMContentLoaded', () => {
    const chatbox = document.getElementById('chat-window');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');

    // Function to add a message to the chat window
    function addMessage(sender, message, isUser) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        if (isUser) {
            messageElement.classList.add('user-message');
        } else {
            messageElement.classList.add('ai-message');
        }
        messageElement.innerHTML = message; // Use innerHTML to render HTML tags from the bot
        chatbox.appendChild(messageElement);

        // Scroll to the bottom of the chat window
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    // Function to send a message
    async function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            addMessage('You', message, true);
            userInput.value = '';

            // Show typing indicator
            const typingIndicator = document.createElement('div');
            typingIndicator.id = 'typing-indicator';
            typingIndicator.classList.add('message', 'ai-message');
            typingIndicator.innerHTML = 'typing...';
            chatbox.appendChild(typingIndicator);
            chatbox.scrollTop = chatbox.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: message })
                });
                const data = await response.json();
                
                // Remove typing indicator
                const indicator = document.getElementById('typing-indicator');
                if (indicator) {
                    chatbox.removeChild(indicator);
                }

                addMessage('Fanshawe Navigator', data.reply, false);
            } catch (error) {
                console.error('Error sending message:', error);

                // Remove typing indicator
                const indicator = document.getElementById('typing-indicator');
                if (indicator) {
                    chatbox.removeChild(indicator);
                }

                addMessage('Fanshawe Navigator', 'Oops! Something went wrong. Please try again.', false);
            }
        }
    }

    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    } else {
        console.error('Send button not found, cannot attach click listener.');
    }

    if (userInput) {
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    } else {
        console.error('User input not found, cannot attach keypress listener.');
    }

    // Initial bot message
    addMessage('Fanshawe Navigator', 'Welcome! How can I help you navigate Fanshawe College today?', false);
});