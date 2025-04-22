const Calendar = (() => {
    function renderCalendar() {
      const cal = document.getElementById("calendar");
      cal.innerHTML = "";
  
      const today = new Date();
      const year = today.getFullYear();
      const month = today.getMonth(); // 0-indexed
  
      const firstDay = new Date(year, month, 1).getDay(); // Day of week
      const daysInMonth = new Date(year, month + 1, 0).getDate();
  
      // Add empty slots for first week offset
      for (let i = 0; i < firstDay; i++) {
        cal.innerHTML += `<div></div>`;
      }
  
      for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const btn = document.createElement("button");
        btn.className = "bg-white p-2 rounded shadow hover:bg-gray-200";
        btn.textContent = day;
        btn.onclick = () => loadReadinessVector(dateStr);
        cal.appendChild(btn);
      }
    }
  
    async function loadReadinessVector(dateStr) {
      try {
        const res = await fetch(`/api/readiness/vector?date=${dateStr}`);
        const data = await res.json();
        document.getElementById("readiness-output").textContent = JSON.stringify(data, null, 2);
        console.log("Readiness Vector for", dateStr, data);
      } catch (err) {
        console.error("Failed to fetch vector:", err);
      }
    }
  
    document.addEventListener("DOMContentLoaded", renderCalendar);
  
    return {
      render: renderCalendar
    };
  })();
  