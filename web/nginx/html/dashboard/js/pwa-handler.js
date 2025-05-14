// PWA Initialization and Handlers
class PWAHandler {
    constructor() {
        this.deferredPrompt = null;
        this.isOnline = navigator.onLine;
        this.initializeServiceWorker();
        this.setupEventListeners();
    }

    async initializeServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/dashboard/sw.js');
                console.log('ServiceWorker registration successful:', registration.scope);
                this.setupNotifications(registration);
                this.setupSync(registration);
            } catch (error) {
                console.error('ServiceWorker registration failed:', error);
                this.addLogEntry('Error: ServiceWorker registration failed');
            }
        }
    }

    async setupNotifications(registration) {
        if ('Notification' in window) {
            try {
                const permission = await Notification.requestPermission();
                console.log('Notification permission:', permission);
            } catch (error) {
                console.error('Notification permission request failed:', error);
            }
        }
    }

    setupSync(registration) {
        if ('sync' in registration) {
            document.addEventListener('online', () => {
                registration.sync.register('sync-metrics');
            });
        }
    }

    setupEventListeners() {
        // Network status
        window.addEventListener('online', () => this.updateOnlineStatus(true));
        window.addEventListener('offline', () => this.updateOnlineStatus(false));

        // Installation prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });

        // Service worker messages
        navigator.serviceWorker?.addEventListener('message', (event) => {
            if (event.data.type === 'SYNC_METRICS') {
                window.refreshMetrics?.();
                this.addLogEntry('Background sync completed');
            }
        });

        // Error handling
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.addLogEntry('Error: ' + event.reason);
        });
    }

    updateOnlineStatus(isOnline) {
        const statusIndicator = document.querySelector('.status-indicator');
        if (statusIndicator) {
            statusIndicator.className = `status-indicator status-${isOnline ? 'up' : 'warning'}`;
        }
        
        this.addLogEntry(isOnline ? 
            'Connection restored - syncing data...' : 
            'Connection lost - using cached data'
        );

        if (isOnline && window.refreshMetrics) {
            window.refreshMetrics();
        }

        document.body.classList.toggle('offline', !isOnline);
    }

    showInstallButton() {
        const header = document.querySelector('.header');
        if (!document.getElementById('install-button') && header) {
            const installButton = document.createElement('button');
            installButton.id = 'install-button';
            installButton.className = 'refresh-button';
            installButton.style.marginLeft = '10px';
            installButton.textContent = 'Install App';
            installButton.addEventListener('click', () => this.installApp());
            header.appendChild(installButton);
        }
    }

    async installApp() {
        if (this.deferredPrompt) {
            try {
                this.deferredPrompt.prompt();
                const { outcome } = await this.deferredPrompt.userChoice;
                console.log(`Installation ${outcome}`);
                this.deferredPrompt = null;
                document.getElementById('install-button')?.remove();
            } catch (error) {
                console.error('Installation failed:', error);
                this.addLogEntry('Error: Installation failed');
            }
        }
    }

    addLogEntry(message) {
        if (window.addLogEntry) {
            window.addLogEntry(message);
        } else {
            console.log(message);
        }
    }
}

// Initialize PWA handler
window.addEventListener('load', () => {
    window.pwaHandler = new PWAHandler();
});

