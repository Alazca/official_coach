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
      "self-end px-4 py-2 rounded-lg max-w-[80%]";
    userDiv.textContent = userMsg;
    chatWindow.appendChild(userDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Send to backend
    try {
      const res = await fetch("/api/nutrition-coach-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg,
        }),
      });
      const data = await res.json();

      // Display AI reply
      const aiDiv = document.createElement("div");
      aiDiv.className =
        "self-start px-4 py-2 rounded-lg max-w-[80%]";
      aiDiv.textContent = data.response || data.error || "No response received";
      chatWindow.appendChild(aiDiv);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    } catch (err) {
      console.error("Error:", err);
      const errDiv = document.createElement("div");
      errDiv.className =
        "self-start px-4 py-2 rounded-lg max-w-[80%]";
      errDiv.textContent = "Error contacting AI coach. Please try again.";
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
    "Breakfast Ideas":
      "Can you give me some healthy breakfast ideas for muscle gain?",
    "Lunch Ideas":
      "What are some nutritious lunch options for someone trying to build muscle?",
    "Dinner Ideas": "Suggest some high-protein dinner meals for athletes.",
    "High Protein":
      "What are some high-protein foods I can include in my diet?",
    "Low Carb": "Can you recommend some low-carb meal options?",
    Vegetarian: "What are good vegetarian meals for strength training?",
  };

  // Attach event listeners only to quick prompt buttons in Meal Recommendations and Special Diets
  document.querySelectorAll(".prompt-button").forEach((btn) => {
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
