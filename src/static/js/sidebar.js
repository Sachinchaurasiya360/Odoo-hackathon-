// Sidebar Toggle Functionality

document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("sidebar");
  const menuToggle = document.getElementById("menuToggle");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebarOverlay = document.getElementById("sidebarOverlay");

  // Toggle sidebar function
  function toggleSidebar() {
    const isShown = sidebar.classList.toggle("show");
    if (sidebarOverlay) {
      sidebarOverlay.classList.toggle("show", isShown);
    }

    // Update ARIA attributes
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", isShown);
    }
    if (sidebarToggle) {
      sidebarToggle.setAttribute("aria-expanded", isShown);
    }
    sidebar.setAttribute("aria-hidden", !isShown);
  }

  // Close sidebar function
  function closeSidebar() {
    sidebar.classList.remove("show");
    if (sidebarOverlay) {
      sidebarOverlay.classList.remove("show");
    }

    // Update ARIA attributes
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", "false");
    }
    if (sidebarToggle) {
      sidebarToggle.setAttribute("aria-expanded", "false");
    }
    sidebar.setAttribute("aria-hidden", "true");
  }

  // Toggle sidebar on mobile menu button click
  if (menuToggle) {
    menuToggle.addEventListener("click", toggleSidebar);
  }

  // Toggle sidebar on sidebar close button click
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", closeSidebar);
  }

  // Close sidebar when clicking overlay
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeSidebar);
  }

  // Close sidebar when clicking outside on mobile
  document.addEventListener("click", function (event) {
    if (window.innerWidth <= 991.98) {
      const isClickInsideSidebar = sidebar.contains(event.target);
      const isClickOnToggle =
        (menuToggle && menuToggle.contains(event.target)) ||
        (sidebarToggle && sidebarToggle.contains(event.target));
      const isClickOnOverlay =
        sidebarOverlay && sidebarOverlay.contains(event.target);

      if (
        !isClickInsideSidebar &&
        !isClickOnToggle &&
        !isClickOnOverlay &&
        sidebar.classList.contains("show")
      ) {
        closeSidebar();
      }
    }
  });

  // Handle window resize
  window.addEventListener("resize", function () {
    if (window.innerWidth > 991.98) {
      closeSidebar();
    }
  });

  // Keyboard navigation - ESC to close sidebar
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && sidebar.classList.contains("show")) {
      closeSidebar();
      if (menuToggle) {
        menuToggle.focus(); // Return focus to menu toggle
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
