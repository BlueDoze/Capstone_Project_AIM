document.addEventListener('DOMContentLoaded', () => {
    const chatbox = document.getElementById('chatbox');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');

    console.log('chatbox:', chatbox);
    console.log('userInput:', userInput);
    console.log('sendButton:', sendButton);

    const addMessage = (sender, message, isUser) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', isUser ? 'user-message' : 'bot-message');

        const senderElement = document.createElement('strong');
        senderElement.textContent = sender;

        const contentElement = document.createElement('div');
        contentElement.innerHTML = message; // Use innerHTML to render HTML tags

        messageElement.appendChild(senderElement);
        messageElement.appendChild(contentElement);
        if (chatbox) {
            chatbox.appendChild(messageElement);
            chatbox.scrollTop = chatbox.scrollHeight;
        } else {
            console.error('Chatbox element not found!');
        }
    };

    const sendMessage = async () => {
        if (!userInput || !sendButton) {
            console.error('Input or Send button element not found!');
            return;
        }

        const message = userInput.value.trim();
        if (message) {
            addMessage('You', message, true);
            userInput.value = '';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: message })
                });

                if (response.ok) {
                    const data = await response.json();
                    addMessage('Bot', data.reply, false);
                } else {
                    addMessage('Bot', 'Error: Could not get a response from the server.', false);
                }
            } catch (error) {
                addMessage('Bot', `Error: ${error.message}`, false);
            }
        }
    };

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
    addMessage('Bot', 'Welcome! How can I help you navigate the M1 Blue Building today?', false);
});
