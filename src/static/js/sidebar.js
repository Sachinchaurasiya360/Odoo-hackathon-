// Sidebar Toggle Functionality - v2.0

document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("sidebar");
  const menuToggle = document.getElementById("menuToggle");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebarOverlay = document.getElementById("sidebarOverlay");
  const mainContent = document.getElementById("main-content");

  // Toggle sidebar function with animation
  function toggleSidebar() {
    const isShown = sidebar.classList.toggle("show");

    // Add smooth transition class
    sidebar.classList.add("transitioning");
    setTimeout(() => sidebar.classList.remove("transitioning"), 300);

    if (sidebarOverlay) {
      sidebarOverlay.classList.toggle("show", isShown);
      if (isShown) {
        sidebarOverlay.classList.add("animate-fade-in");
      } else {
        sidebarOverlay.classList.remove("animate-fade-in");
      }
    }

    // Update ARIA attributes for accessibility
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", isShown);
    }
    if (sidebarToggle) {
      sidebarToggle.setAttribute("aria-expanded", isShown);
    }
    sidebar.setAttribute("aria-hidden", !isShown);

    // Prevent body scroll when sidebar is open on mobile
    if (window.innerWidth <= 1024) {
      document.body.style.overflow = isShown ? "hidden" : "";
    }
  }

  // Close sidebar function with animation
  function closeSidebar() {
    sidebar.classList.remove("show");
    sidebar.classList.add("transitioning");
    setTimeout(() => sidebar.classList.remove("transitioning"), 300);

    if (sidebarOverlay) {
      sidebarOverlay.classList.remove("show");
      sidebarOverlay.classList.remove("animate-fade-in");
    }

    // Update ARIA attributes
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", "false");
    }
    if (sidebarToggle) {
      sidebarToggle.setAttribute("aria-expanded", "false");
    }
    sidebar.setAttribute("aria-hidden", "true");

    // Restore body scroll
    document.body.style.overflow = "";
  }

  // Toggle sidebar on mobile menu button click
  if (menuToggle) {
    menuToggle.addEventListener("click", function (e) {
      e.stopPropagation();
      toggleSidebar();
    });
  }

  // Toggle sidebar on sidebar close button click
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", function (e) {
      e.stopPropagation();
      closeSidebar();
    });
  }

  // Close sidebar when clicking overlay
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeSidebar);
  }

  // Close sidebar when clicking outside on mobile
  document.addEventListener("click", function (event) {
    if (window.innerWidth <= 1024) {
      const isClickInsideSidebar = sidebar.contains(event.target);
      const isClickOnToggle =
        (menuToggle && menuToggle.contains(event.target)) ||
        (sidebarToggle && sidebarToggle.contains(event.target));

      if (
        !isClickInsideSidebar &&
        !isClickOnToggle &&
        sidebar.classList.contains("show")
      ) {
        closeSidebar();
      }
    }
  });

  // Handle window resize
  let resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (window.innerWidth > 1024) {
        closeSidebar();
        document.body.style.overflow = "";
      }
    }, 250);
  });

  // Keyboard navigation - ESC to close sidebar
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && sidebar.classList.contains("show")) {
      closeSidebar();
      if (menuToggle) {
        menuToggle.focus(); // Return focus to menu toggle for accessibility
      }
    }
  });

  // Trap focus within sidebar when open on mobile
  sidebar.addEventListener("keydown", function (event) {
    if (window.innerWidth <= 991.98 && sidebar.classList.contains("show")) {
      const focusableElements = sidebar.querySelectorAll(
        'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.key === "Tab") {
        if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    }
  });
});
