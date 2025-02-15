const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
    console.error("Speech Recognition API is not supported in this browser.");
} else {
    console.log("Speech Recognition API is available.");

    const recognition = new SpeechRecognition();
    recognition.continuous = false; // Stop automatically after speech input
    recognition.interimResults = true; // Allow real-time text update
    recognition.lang = "en-US";

    const txtMessage = document.getElementById("TxtMessage");
    const startVoiceButton = document.getElementById("startVoice");

    recognition.onstart = () => {
        console.log("Voice recognition started...");
        txtMessage.placeholder = "Listening...";
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
    };

    recognition.onresult = (event) => {
        let interimTranscript = "";
        let finalTranscript = "";

        for (let i = 0; i < event.results.length; i++) {
            let transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + " ";
            } else {
                interimTranscript += transcript + " ";
            }
        }

        txtMessage.value = finalTranscript || interimTranscript; // Show interim results live
    };

    recognition.onend = () => {
        console.log("Voice recognition stopped.");
        txtMessage.placeholder = "Type a message...";
    };

    startVoiceButton.addEventListener("click", () => {
        recognition.start();
    });
}
//////////////////////////////////////////////////////////////////SELECT CHAT//////////////////////////
document.addEventListener('DOMContentLoaded', () => {
    const chatArea = document.getElementById('chat-area');
    const selectionToolbar = document.getElementById('selection-toolbar');
    const deleteButton = document.getElementById('delete-selected');
  
    // Array to track selected message IDs
    let selectedMessages = [];
  
    // Example of dynamically adding messages (e.g., after fetching from the server)
    function loadMessages() {
      const messages = [
        { id: 1, text: 'Hello, how are you?' },
        { id: 2, text: 'I\'m doing great, thanks!' }
      ];
  
      messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');
        messageDiv.setAttribute('data-message-id', message.id);
        messageDiv.innerHTML = `
          <span class="message-text">${message.text}</span>
        `;
        chatArea.appendChild(messageDiv);
      });
    }
  
    // Toggle message selection on click
    chatArea.addEventListener('click', (event) => {
      const messageDiv = event.target.closest('.chat-message');
      if (messageDiv) {
        const messageId = messageDiv.getAttribute('data-message-id');
        if (messageDiv.classList.contains('selected')) {
          messageDiv.classList.remove('selected');
          selectedMessages = selectedMessages.filter(id => id !== messageId); // Remove from selection
        } else {
          messageDiv.classList.add('selected');
          selectedMessages.push(messageId); // Add to selection
        }
  
        // Show/hide the toolbar based on selection count
        if (selectedMessages.length > 0) {
          selectionToolbar.style.display = 'flex';
        } else {
          selectionToolbar.style.display = 'none';
        }
      }
    });
  
    // Delete selected messages when the delete button is clicked
    deleteButton.addEventListener('click', () => {
      selectedMessages.forEach(messageId => {
        const messageToDelete = document.querySelector(`.chat-message[data-message-id="${messageId}"]`);
        if (messageToDelete) {
          messageToDelete.remove();
        }
      });
  
      // Reset the selection
      selectedMessages = [];
      selectionToolbar.style.display = 'none'; // Hide toolbar after deletion
    });
  
    // Load messages on page load (simulating fetching from server)
    loadMessages();
  });