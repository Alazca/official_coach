class TrainerAI {
    constructor() {
        this.context = [];
        this.responses = {
            workout: {
                exercises: [
                    "Let's start with 3 sets of 12 bodyweight squats. Focus on form - keep your chest up and knees tracking over toes.",
                    "For chest, try 3 sets of 10 push-ups. Go to your knees if needed, quality over quantity!",
                    "Time for a core workout: 3 sets of 30-second planks with perfect form.",
                    "Let's work on pull-ups. If you can't do full ones yet, start with negative reps - jump up and lower slowly."
                ],
                form: [
                    "Remember to breathe! Exhale during exertion, inhale during the easier part.",
                    "Keep your core tight throughout the movement - it's your foundation.",
                    "Slow down the movement. Control is more important than speed.",
                    "Make sure your back stays straight, don't round your spine."
                ]
            },
            nutrition: {
                meals: [
                    "Aim for protein with every meal - about a palm-sized portion.",
                    "Try to eat within 30 minutes after your workout for better recovery.",
                    "Don't forget your veggies - fill half your plate with colorful vegetables.",
                    "Stay hydrated! Drink water throughout the day, not just during workouts."
                ],
                planning: [
                    "Prep your meals in advance to avoid making unhealthy choices when hungry.",
                    "Track your protein intake - aim for 1.6-2.2g per kg of bodyweight.",
                    "Complex carbs are your friend - especially around workouts.",
                    "Include healthy fats like avocados, nuts, and olive oil in your diet."
                ]
            },
            motivation: [
                "Remember why you started. Every rep brings you closer to your goals!",
                "Progress isn't always visible - trust the process and keep pushing!",
                "You're stronger than you think. Let's prove it today!",
                "Small steps every day lead to big changes. Stay consistent!"
            ],
            general: [
                "How can I help you with your fitness goals today?",
                "What specific area would you like to focus on?",
                "Remember, consistency is key to achieving your fitness goals.",
                "Let's make today's workout count!"
            ]
        };
    }

    generateResponse(message) {
        message = message.toLowerCase();
        let category = 'general';
        let subcategory = '';
        
        // Determine message category and subcategory
        if (message.includes('workout') || message.includes('exercise')) {
            category = 'workout';
            subcategory = message.includes('form') ? 'form' : 'exercises';
        } else if (message.includes('food') || message.includes('eat') || message.includes('nutrition')) {
            category = 'nutrition';
            subcategory = message.includes('meal') ? 'meals' : 'planning';
        } else if (message.includes('motivat') || message.includes('tired') || message.includes('hard')) {
            category = 'motivation';
        }

        // Get response
        const responses = subcategory ? 
            this.responses[category][subcategory] : 
            this.responses[category];
        
        return responses[Math.floor(Math.random() * responses.length)];
    }
}

// Initialize chat interface
document.addEventListener('DOMContentLoaded', () => {
    const trainer = new TrainerAI();
    const chatContainer = document.getElementById('chatContainer');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendMessageBtn');

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`;
        messageDiv.innerHTML = `
            <div class="max-w-[75%] ${isUser ? 'bg-red-600' : 'bg-gray-700'} rounded-lg px-4 py-2">
                <p class="text-white">${message}</p>
            </div>
        `;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async function handleSendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        messageInput.value = '';
        
        // Show typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'flex justify-start mb-4';
        typingDiv.innerHTML = `
            <div class="bg-gray-700 rounded-lg px-4 py-2">
                <p class="text-white">Typing...</p>
            </div>
        `;
        chatContainer.appendChild(typingDiv);

        try {
            const response = await trainer.generateResponse(message);
            typingDiv.remove();
            addMessage(response);
        } catch (error) {
            typingDiv.remove();
            addMessage("Sorry, I'm having trouble connecting. Please try again.");
        }
    }

    // Add event listeners
    sendButton.addEventListener('click', handleSendMessage);
    
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Make handleSendMessage available globally
    window.sendMessage = handleSendMessage;
});
