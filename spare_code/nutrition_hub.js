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
      const res = await fetch("/api/ai-coach-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg,
          coach_type: "nutrition", // Specify this is for nutrition coaching
        }),
      });
      const data = await res.json();
      // Display AI reply
      const aiDiv = document.createElement("div");
      aiDiv.className =
        "self-start bg-gray-600 text-white px-4 py-2 rounded-lg max-w-[80%]";
      aiDiv.textContent = data.reply;
      chatWindow.appendChild(aiDiv);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    } catch (err) {
      const errDiv = document.createElement("div");
      errDiv.className =
        "self-start bg-gray-600 text-white px-4 py-2 rounded-lg max-w-[80%]";
      errDiv.textContent = "Error contacting AI coach.";
      chatWindow.appendChild(errDiv);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  }

  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const userMsg = chatInput.value.trim();
    if (!userMsg) return;
    chatInput.value = "";
    await sendMessageToAI(userMsg);
  });

  // Quick prompt buttons for nutrition-related questions
  const quickPrompts = {
    Macros:
      "What are the recommended macronutrient ratios for strength training?",
    "Pre-Workout": "What should I eat before a workout?",
    "Post-Workout": "What are the best post-workout meals?",
    Supplements: "What supplements are recommended for strength training?",
    Hydration: "How much water should I drink during workouts?",
    "Meal Timing": "When should I eat in relation to my workouts?",
  };

  document.querySelectorAll("button").forEach((btn) => {
    const prompt = quickPrompts[btn.textContent.trim()];
    if (prompt) {
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        await sendMessageToAI(prompt);
      });
    }
  });

  // Food Logger functionality
  const foodLoggerForm = document.getElementById("foodLoggerForm");
  const foodInput = document.getElementById("foodInput");
  const foodLoggerResults = document.getElementById("foodLoggerResults");

  if (foodLoggerForm && foodInput && foodLoggerResults) {
    foodLoggerForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const query = foodInput.value.trim();
      if (!query) return;
      foodLoggerResults.textContent = "Loading...";
      try {
        const res = await fetch("/api/food-search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query }),
        });
        const data = await res.json();
        if (data.error) {
          foodLoggerResults.textContent = "Error: " + data.error;
        } else if (data.foods && data.foods.length > 0) {
          foodLoggerResults.innerHTML = data.foods
            .map(
              (food) =>
                `<div class="mb-2 p-2 bg-gray-800 rounded">
                            <div class="font-bold text-white">${food.description}${food.brand ? ' <span class=\"text-xs text-gray-400\">(' + food.brand + ")</span>" : ""}</div>
                            <div class="text-gray-300 text-sm">Calories: ${food.calories ?? "N/A"} | Protein: ${food.protein ?? "N/A"}g</div>
                        </div>`,
            )
            .join("");
        } else {
          foodLoggerResults.textContent = "No results found.";
        }
      } catch (err) {
        foodLoggerResults.textContent = "Error searching for food.";
      }
    });
  }
});
