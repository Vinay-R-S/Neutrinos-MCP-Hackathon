/*
* Main JavaScript for MCP Client
* Handles file uploads, form interactions, and theme switching
*/

document.addEventListener("DOMContentLoaded", function () {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("files");
  const fileList = document.getElementById("file-list");
  const form = document.getElementById("intake-form");
  const submitBtn = document.getElementById("submit-btn");
  const themeToggle = document.getElementById("theme-toggle");

  let selectedFiles = new DataTransfer();

  // Theme Toggle
  function initTheme() {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      document.body.classList.add("dark-theme");
      updateThemeIcon(true);
    }
  }

  function toggleTheme() {
    const isDark = document.body.classList.toggle("dark-theme");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    updateThemeIcon(isDark);
  }

  function updateThemeIcon(isDark) {
    const moonIcon = document.querySelector(".icon-moon");
    const sunIcon = document.querySelector(".icon-sun");
    if (moonIcon && sunIcon) {
      moonIcon.style.display = isDark ? "none" : "block";
      sunIcon.style.display = isDark ? "block" : "none";
    }
  }

  // Initialize theme on load
  initTheme();

  if (themeToggle) {
    themeToggle.addEventListener("click", toggleTheme);
  }

  // File Upload Handling
  if (dropZone && fileInput) {
    // Drag and drop handlers
    dropZone.addEventListener("dragover", function (e) {
      e.preventDefault();
      dropZone.style.borderColor = "#ff4b4b";
      dropZone.style.backgroundColor = document.body.classList.contains(
        "dark-theme"
      )
        ? "#2a1a1a"
        : "#fff5f5";
    });

    dropZone.addEventListener("dragleave", function (e) {
      e.preventDefault();
      dropZone.style.borderColor = "";
      dropZone.style.backgroundColor = "";
    });

    dropZone.addEventListener("drop", function (e) {
      e.preventDefault();
      dropZone.style.borderColor = "";
      dropZone.style.backgroundColor = "";

      const files = e.dataTransfer.files;
      handleFiles(files);
    });

    // File input change handler
    fileInput.addEventListener("change", function (e) {
      handleFiles(e.target.files);
    });
  }

  function handleFiles(files) {
    for (let file of files) {
      selectedFiles.items.add(file);
    }
    fileInput.files = selectedFiles.files;
    updateFileList();
  }

  function updateFileList() {
    if (!fileList) return;

    fileList.innerHTML = "";

    for (let i = 0; i < selectedFiles.files.length; i++) {
      const file = selectedFiles.files[i];
      const item = document.createElement("div");
      item.className = "file-item";
      item.innerHTML = `
                <span>${file.name} (${formatFileSize(file.size)})</span>
                <button type="button" data-index="${i}">&times;</button>
            `;
      fileList.appendChild(item);
    }

    // Add remove handlers
    fileList.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", function () {
        const index = parseInt(this.dataset.index);
        removeFile(index);
      });
    });
  }

  function removeFile(index) {
    const newFiles = new DataTransfer();
    for (let i = 0; i < selectedFiles.files.length; i++) {
      if (i !== index) {
        newFiles.items.add(selectedFiles.files[i]);
      }
    }
    selectedFiles = newFiles;
    fileInput.files = selectedFiles.files;
    updateFileList();
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  // Form Submission
  if (form && submitBtn) {
    form.addEventListener("submit", function () {
      submitBtn.disabled = true;
      submitBtn.textContent = "Processing...";
    });
  }
});
