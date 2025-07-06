// Reload the page when the title button is clicked
window.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("title-refresh-button");
  if (button) {
    button.addEventListener("click", () => {
      // Navigate to the root URL to mimic a hard refresh
      window.location.href = "/";
    });
  }
});
