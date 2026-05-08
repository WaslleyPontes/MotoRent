let deferredInstallPrompt = null;

function setElementText(selector, value) {
    const el = document.querySelector(selector);
    if (el) {
        el.textContent = value;
    }
}

function handleBackgroundCheckResult(result) {
    if (!result) return;
    const container = document.querySelector('.ocr-result');
    if (!container) return;
}

function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/service-worker.js')
            .then(() => console.log('Service worker registrado com sucesso.'))
            .catch(err => console.warn('Falha ao registrar Service worker:', err));
    }
}

window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredInstallPrompt = event;
    const installButton = document.createElement('button');
    installButton.className = 'button install-button';
    installButton.textContent = 'Instalar app';
    installButton.addEventListener('click', async () => {
        if (!deferredInstallPrompt) return;
        deferredInstallPrompt.prompt();
        const choiceResult = await deferredInstallPrompt.userChoice;
        if (choiceResult.outcome === 'accepted') {
            console.log('Usuário aceitou a instalação.');
        }
        deferredInstallPrompt = null;
        installButton.remove();
    });

    const topbar = document.querySelector('.topbar');
    if (topbar) {
        topbar.appendChild(installButton);
    }
});

window.addEventListener('appinstalled', () => {
    console.log('MotoRent instalado com sucesso.');
    const installButton = document.querySelector('.install-button');
    if (installButton) {
        installButton.remove();
    }
});

window.addEventListener('DOMContentLoaded', () => {
    registerServiceWorker();

    const themeToggle = document.querySelector('#themeToggle');
    const menuToggle = document.querySelector('#menuToggle');
    const mobileBackdrop = document.querySelector('#mobileBackdrop');

    if (menuToggle && mobileBackdrop) {
        menuToggle.addEventListener('click', () => {
            document.body.classList.toggle('sidebar-open');
        });

        mobileBackdrop.addEventListener('click', () => {
            document.body.classList.remove('sidebar-open');
        });
    }

    const navLinks = document.querySelectorAll('.sidebar nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            document.body.classList.remove('sidebar-open');
        });
    });
});
