/**
 * COACH Frontpage Module
 * Handles all frontend animations and interactions for the landing page
 */
const FrontpageModule = (() => {
  /**
   * Initialize all frontpage animations and interactions
   */
  const initialize = () => {
    document.addEventListener("DOMContentLoaded", () => {
      console.log("Frontpage Module initializing...");

      // Set up smooth scrolling for navigation
      setupSmoothScroll();

      // Set up parallax effect for hero section
      setupParallaxEffect();

      // Set up animations for sections
      setupSectionAnimations();

      // Set up team cards animations
      setupTeamCardsAnimations();
    });
  };

  /**
   * Setup smooth scrolling for navigation links
   */
  const setupSmoothScroll = () => {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", function (e) {
        e.preventDefault();
        const targetElement = document.querySelector(this.getAttribute("href"));
        if (targetElement) {
          targetElement.scrollIntoView({
            behavior: "smooth",
          });
        }
      });
    });
  };

  /**
   * Setup parallax effect for the hero section
   */
  const setupParallaxEffect = () => {
    window.addEventListener("scroll", () => {
      const scrolled = window.pageYOffset;
      const heroContent = document.querySelector(".hero-content");
      if (heroContent) {
        heroContent.style.transform = `translateY(${scrolled * 0.5}px)`;
      }
    });
  };

  /**
   * Setup animations for sections using Intersection Observer
   */
  const setupSectionAnimations = () => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("opacity-100");
          entry.target.classList.remove("opacity-0");
        }
      });
    });

    document.querySelectorAll("section").forEach((section) => {
      section.classList.add("opacity-0", "transition-opacity", "duration-1000");
      observer.observe(section);
    });
  };

  /**
   * Setup staggered animations for team cards
   */
  const setupTeamCardsAnimations = () => {
    const teamObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry, index) => {
          if (entry.isIntersecting) {
            // Add staggered animation delay
            setTimeout(() => {
              entry.target.classList.add("opacity-100", "translate-y-0");
              entry.target.classList.remove("opacity-0", "translate-y-10");
            }, index * 150);
          }
        });
      },
      { threshold: 0.2 },
    );

    document.querySelectorAll(".team-card").forEach((card) => {
      card.classList.add(
        "opacity-0",
        "translate-y-10",
        "transition-all",
        "duration-700",
      );
      teamObserver.observe(card);
    });
  };

  /**
   * Replace navigation button inline onclick handlers with proper event listeners
   */
  const setupNavigationButtons = () => {
    // Setup signup buttons
    document
      .querySelectorAll('button[onclick*="signup.html"]')
      .forEach((button) => {
        button.removeAttribute("onclick");
        button.addEventListener("click", () => {
          window.location.href = "signup.html";
        });
      });

    // Setup Start Free Trial button
    document
      .querySelectorAll(
        "button[onclick*=\"window.location.href='signup.html'\"]",
      )
      .forEach((button) => {
        button.removeAttribute("onclick");
        button.addEventListener("click", () => {
          window.location.href = "signup.html";
        });
      });
  };

  // Public API
  return {
    initialize,
  };
})();

      function openCoachChat() {
        document.getElementById("coachChatModal").classList.remove("hidden");
        document.getElementById("coachChatModal").classList.add("flex");
        document.getElementById("chatInput").focus();
      }

      function closeCoachChat() {
        document.getElementById("coachChatModal").classList.add("hidden");
        document.getElementById("coachChatModal").classList.remove("flex");
      }

      function handleChatInput(event) {
        if (event.key === "Enter") {
          sendChatMessage();
        }
      }

      function addMessage(message, isUser = false) {
        const chatMessages = document.getElementById("chatMessages");
        const messageDiv = document.createElement("div");
        if (isUser) {
          messageDiv.className =
            "flex items-center space-x-4 justify-end flex-row-reverse";
          messageDiv.innerHTML = `
            <div class=\"flex-shrink-0 ml-2\">
              <div class=\"w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white font-bold shadow-md\">U</div>
            </div>
            <div class=\"bg-gradient-to-l from-gray-700/90 to-gray-800/80 rounded-xl px-5 py-3 max-w-[95%] min-w-[48px] shadow text-white text-right\">${message}</div>
          `;
        } else {
          messageDiv.className = "flex items-center space-x-4 justify-start";
          messageDiv.innerHTML = `
            <div class=\"flex-shrink-0 mr-2\">
              <div class=\"w-8 h-8 rounded-full bg-red-600 flex items-center justify-center text-white font-bold shadow-md\">C</div>
            </div>
            <div class=\"bg-gradient-to-r from-red-500/80 to-orange-400/80 rounded-xl px-5 py-3 max-w-[80%] min-w-[48px] shadow text-white text-left\">${message}</div>
          `;
        }
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }

      async function sendChatMessage() {
        const input = document.getElementById("chatInput");
        const message = input.value.trim();

        if (!message) return;

        // Add user message to chat
        addMessage(message, true);
        input.value = "";

        try {
          const response = await fetch("/api/general-coach-chat", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ message }),
          });

          const data = await response.json();

          if (data.error) {
            addMessage("Sorry, I encountered an error. Please try again.");
          } else {
            addMessage(data.response);
          }
        } catch (error) {
          addMessage("Sorry, I encountered an error. Please try again.");
        }
      }
    
// Initialize the module when loaded
FrontpageModule.initialize();
