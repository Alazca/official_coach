/**
 * COACH Frontpage Module
 * Handles all frontend animations and interactions for the landing page
 */
const FrontpageModule = (() => {
  /**
   * Initialize all frontpage animations and interactions
   */
  const initialize = () => {
    document.addEventListener('DOMContentLoaded', () => {
      console.log('Frontpage Module initializing...');
      
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
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const targetElement = document.querySelector(this.getAttribute('href'));
        if (targetElement) {
          targetElement.scrollIntoView({
            behavior: 'smooth'
          });
        }
      });
    });
  };
  
  /**
   * Setup parallax effect for the hero section
   */
  const setupParallaxEffect = () => {
    window.addEventListener('scroll', () => {
      const scrolled = window.pageYOffset;
      const heroContent = document.querySelector('.hero-content');
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
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('opacity-100');
          entry.target.classList.remove('opacity-0');
        }
      });
    });

    document.querySelectorAll('section').forEach((section) => {
      section.classList.add('opacity-0', 'transition-opacity', 'duration-1000');
      observer.observe(section);
    });
  };
  
  /**
   * Setup staggered animations for team cards
   */
  const setupTeamCardsAnimations = () => {
    const teamObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          // Add staggered animation delay
          setTimeout(() => {
            entry.target.classList.add('opacity-100', 'translate-y-0');
            entry.target.classList.remove('opacity-0', 'translate-y-10');
          }, index * 150);
        }
      });
    }, { threshold: 0.2 });

    document.querySelectorAll('.team-card').forEach((card) => {
      card.classList.add('opacity-0', 'translate-y-10', 'transition-all', 'duration-700');
      teamObserver.observe(card);
    });
  };
  
  /**
   * Replace navigation button inline onclick handlers with proper event listeners
   */
  const setupNavigationButtons = () => {
    // Setup signup buttons
    document.querySelectorAll('button[onclick*="sign-up.html"]').forEach(button => {
      button.removeAttribute('onclick');
      button.addEventListener('click', () => {
        window.location.href = 'sign-up.html';
      });
    });
    
    // Setup Start Free Trial button
    document.querySelectorAll('button[onclick*="window.location.href=\'sign-up.html\'"]').forEach(button => {
      button.removeAttribute('onclick');
      button.addEventListener('click', () => {
        window.location.href = 'sign-up.html';
      });
    });
  };
  
  // Public API
  return {
    initialize
  };
})();

// Initialize the module when loaded
FrontpageModule.initialize();