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
//////////////////////////////////////////////////////////////////STYLES CSS DARK AND LIGHT MODE//////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

const toggleButton = document.querySelector('.dark-light');
const colors = document.querySelectorAll('.color');

// Load saved theme from localStorage
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('themeColor');
    if (savedTheme) {
        document.body.setAttribute('data-theme', savedTheme);
        
        // Remove 'selected' from all and apply only to the saved theme
        colors.forEach(color => {
            color.classList.remove('selected'); 
            if (color.getAttribute('data-color') === savedTheme) {
                color.classList.add('selected'); // Only select the saved theme
            }
        });
    }

    const isDarkMode = localStorage.getItem('darkMode') === 'enabled';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }
});

// Event listener for theme selection
colors.forEach(color => {
    color.addEventListener('click', () => {
        // Remove 'selected' from all before adding it to the clicked one
        colors.forEach(c => c.classList.remove('selected'));

        const theme = color.getAttribute('data-color');
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('themeColor', theme); // Save theme in localStorage
        
        color.classList.add('selected'); // Add 'selected' to clicked color
    });
});

// Event listener for dark/light mode toggle
toggleButton.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled'); // Store dark mode preference
});

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////ADD DIV TOGGLE///////////
document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.querySelector(".add");
    const backButton = document.querySelector(".go-back");  // Button to go back to recent chats
    const recentsArea = document.querySelector(".msg-detail");
    const registeredUsers = document.querySelector(".registeredusers");

    // When the 'Add' button is clicked, show registered users and hide recent chats
    addButton.addEventListener("click", function () {
        recentsArea.style.display = "none"; 
        registeredUsers.style.display = "flex"; // Use flex to match registered-users layout
    });

    // When the 'Go Back' button is clicked, show recent chats and hide registered users
    backButton.addEventListener("click", function () {
        registeredUsers.style.display = "none";
        recentsArea.style.display = "block";  // Show recent chats
    });
});
///////////////////////////////////////////////////////////////////////////////////////////////////Settings Toggle////////////////////////////

document.addEventListener("DOMContentLoaded", function () {
    const settingsIcon = document.getElementById("settings-icon");
    const settingsMenu = document.getElementById("settings-menu");
    const logoutButton = document.getElementById("logout-button");

    // Toggle dropdown visibility
    settingsIcon.addEventListener("click", function (event) {
        event.stopPropagation(); // Prevents closing when clicking the icon
        const isVisible = settingsMenu.style.display === "block";

        settingsMenu.style.display = isVisible ? "none" : "block";
        logoutButton.style.display = isVisible ? "none" : "block"; // Show/hide logout button
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function (event) {
        if (!settingsIcon.contains(event.target) && !settingsMenu.contains(event.target)) {
            settingsMenu.style.display = "none";
            logoutButton.style.display = "none"; // Hide logout button
        }
    });
});

////////////////////////SRCL Conversation
document.addEventListener("DOMContentLoaded", function () {
    const conversationArea = document.getElementById("conversation-area");
    const scrollDownBtn = document.getElementById("scroll-down-btn");

    // Scroll to bottom function
    function scrollToBottom() {
        conversationArea.scrollTo({
            top: conversationArea.scrollHeight,
            behavior: "smooth"
        });
    }
    // Show/hide button based on scroll position
    function toggleScrollButton() {
        const isAtBottom = conversationArea.scrollHeight - conversationArea.scrollTop <= conversationArea.clientHeight + 10;
        if (isAtBottom) {
            scrollDownBtn.classList.remove("show"); // Hide button when already at the bottom
        } else {
            scrollDownBtn.classList.add("show"); // Show button when scrolled up
        }
    }

    // Scroll event listener
    conversationArea.addEventListener("scroll", toggleScrollButton);

    // Button click to scroll down
    scrollDownBtn.addEventListener("click", scrollToBottom);

});
//////////////////////////////////////////////////////////////////////seacrch in conversation/////////////////////////////////

document.getElementById('conversation-search').addEventListener('input', function () {
    let searchQuery = this.value.toLowerCase();
    let messages = document.querySelectorAll('#conversation-area .msg .msg-message');
    let firstMatch = null;

    messages.forEach(msg => {
        let originalText = msg.textContent;
        let lowerText = originalText.toLowerCase();

        if (searchQuery && lowerText.includes(searchQuery)) {
            // Highlight matching text
            let highlightedText = originalText.replace(new RegExp(`(${searchQuery})`, 'gi'), 
                `<span class="highlight">$1</span>`);
            msg.innerHTML = highlightedText;

            // Store the first matching element to scroll to
            if (!firstMatch) {
                firstMatch = msg;
            }
        } else {
            // Restore original text if search is cleared
            msg.innerHTML = originalText;
        }
    });

    // Scroll to the first match
    if (firstMatch) {
        firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});
