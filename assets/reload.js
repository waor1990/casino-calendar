// Reload the page when the title button is clicked
window.addEventListener('DOMContentLoaded', () => {
  const button = document.getElementById('title-refresh-button');
  if (button) {
    button.addEventListener('click', () => {
      window.location.reload();
    });
  }
});
