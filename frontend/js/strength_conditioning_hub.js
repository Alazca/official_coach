document.addEventListener("DOMContentLoaded", () => {
  // Chat functionality
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chatWindow = document.getElementById("chatWindow");

  // Helper to send a message to the AI and display response
  async function sendMessageToAI(userMsg) {
    // Display user message
    const userDiv = document.createElement("div");
    userDiv.className =
      "self-end bg-red-700 text-white px-4 py-2 rounded-lg max-w-[80%]";
    userDiv.textContent = userMsg;
    chatWindow.appendChild(userDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Send to backend
    try {
      const res = await fetch("/api/strength-coach-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();

      // Display AI reply
      const aiDiv = document.createElement("div");
      aiDiv.className =
        "self-start bg-gray-600 text-white px-4 py-2 rounded-lg max-w-[80%]";
      aiDiv.textContent = data.response || data.error || "No response received";
      chatWindow.appendChild(aiDiv);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    } catch (err) {
      console.error("Error:", err);
      const errDiv = document.createElement("div");
      errDiv.className =
        "self-start bg-gray-600 text-white px-4 py-2 rounded-lg max-w-[80%]";
      errDiv.textContent = "Error contacting AI coach. Please try again.";
      chatWindow.appendChild(errDiv);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  }

  // Handle form-submitted messages
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const userMsg = chatInput.value.trim();
    if (!userMsg) return;
    chatInput.value = "";
    await sendMessageToAI(userMsg);
  });

  // Quick prompts mapping
  const quickPrompts = {
    "Beginner Workout":
      "Can you give me a beginner full-body strength workout?",
    "Intermediate Workout":
      "Can you give me an intermediate strength workout plan?",
    "Advanced Workout":
      "Can you give me an advanced strength and conditioning routine?",
    "Upper Body": "Can you suggest an upper body strength workout?",
    "Lower Body": "Can you suggest a lower body strength workout?",
    Core: "Can you suggest a core strengthening routine?",
    "Form Check": "Can you explain proper form for deadlifts?",
    Progression: "How should I progress my bench press?",
    Recovery: "What are the best recovery practices between workouts?",
    Programming: "Can you suggest a 3-day split routine?",
    Technique: "What are common mistakes in squat form?",
    Equipment: "What equipment do I need for a home gym?",
  };

  // Attach to only the buttons inside #quick-prompts
  document.querySelectorAll("#quick-prompts button").forEach((btn) => {
    const prompt = quickPrompts[btn.textContent.trim()];
    if (!prompt) return;
    btn.addEventListener("click", () => {
      sendMessageToAI(prompt);
    });
  });
});
