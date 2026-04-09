// PWA Install Prompt Handler
let deferredPrompt = null;
let installButton = null;

// Listen for the beforeinstallprompt event
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log('[PWA] Install prompt ready');
  
  // Show install button if it exists
  if (installButton) {
    installButton.style.display = 'block';
  }
});

// Listen for successful installation
window.addEventListener('appinstalled', () => {
  console.log('[PWA] App installed successfully');
  deferredPrompt = null;
  if (installButton) {
    installButton.style.display = 'none';
  }
});

// Function to show install prompt (call this from your UI)
function showInstallPrompt() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('[PWA] User accepted the install prompt');
      } else {
        console.log('[PWA] User dismissed the install prompt');
      }
      deferredPrompt = null;
      if (installButton) {
        installButton.style.display = 'none';
      }
    });
    return true;
  } else {
    console.log('[PWA] Install prompt not available - app may already be installed');
    return false;
  }
}

// Auto-create install button if not present
document.addEventListener('DOMContentLoaded', function() {
  // Check if we should show install button
  const existingButton = document.getElementById('pwa-install-btn');
  if (!existingButton && deferredPrompt) {
    createInstallButton();
  }
});

function createInstallButton() {
  const button = document.createElement('button');
  button.id = 'pwa-install-btn';
  button.textContent = '📲 Install App';
  button.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 24px;
    background: #f0a500;
    color: #000;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-size: 14px;
    cursor: pointer;
    z-index: 9999;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    display: none;
  `;
  button.onclick = showInstallPrompt;
  document.body.appendChild(button);
  installButton = button;
  
  // Show button if prompt is ready
  if (deferredPrompt) {
    button.style.display = 'block';
  }
}

// Check if already installed
function isAppInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches || 
         window.navigator.standalone === true;
}

console.log('[PWA] Install handler loaded');
