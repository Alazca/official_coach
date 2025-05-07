document.addEventListener("DOMContentLoaded", () => {
  let selectedWorkoutType = null;

  // Highlight selected workout type
  const typeButtons = document.querySelectorAll(".workout-type-btn");
  typeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      typeButtons.forEach((b) =>
        b.classList.remove("ring", "ring-red-500", "ring-offset-2"),
      );
      btn.classList.add("ring", "ring-red-500", "ring-offset-2");
      selectedWorkoutType = btn.getAttribute("data-workout-type");
    });
  });

  // Handle Save button click
  const saveBtn = document.getElementById("saveWorkoutBtn");
  saveBtn.addEventListener("click", async () => {
    const workoutDate = document.getElementById("workoutDate").value;
    const duration = parseInt(document.getElementById("workoutDuration").value);
    const notes = document.getElementById("workoutNotes").value;

    if (!selectedWorkoutType || !workoutDate || !duration || duration <= 0) {
      alert("Please fill out all required fields.");
      return;
    }

    const workoutData = {
      workout_type: selectedWorkoutType,
      workout_date: workoutDate,
      duration: duration,
      notes: notes,
    };

    try {
      const token = Credentialsl.getToken();
      const response = await fetch("/api/workout/log", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(workoutData),
      });

      const result = await response.json();

      if (response.ok) {
        alert("Workout saved!");
        // Reset form
        document.getElementById("workoutDate").value = "";
        document.getElementById("workoutDuration").value = "";
        document.getElementById("workoutNotes").value = "";
        selectedWorkoutType = null;
        typeButtons.forEach((b) =>
          b.classList.remove("ring", "ring-red-500", "ring-offset-2"),
        );
      } else {
        alert("Failed to save workout: " + (result.error || "Unknown error"));
        console.error("Server error:", result);
      }
    } catch (error) {
      console.error("Error saving workout:", error);
      alert("An error occurred. Please try again.");
    }
  });
});
