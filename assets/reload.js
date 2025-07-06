// Reload the page when the title button is clicked
function attachReloadHandler() {
  const button = document.getElementById("title-refresh-button");
  if (button) {
    button.addEventListener("click", () => {
      // Navigate to the root URL to mimic a hard refresh
      window.location.href = "/";
    });
  }
}

if (document.readyState === "loading") {
  window.addEventListener("DOMContentLoaded", attachReloadHandler);
} else {
  attachReloadHandler();
}
