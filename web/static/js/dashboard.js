// Fonction wrapper pour les appels fetch authentifiés
async function fetchWithAuth(url, options = {}) {
    const token = sessionStorage.getItem('accessToken');

    if (!token) {
        window.location.href = '/'; // Rediriger si pas de token
        return Promise.reject('No token found');
    }

    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    // Pour les requêtes POST avec corps JSON, s'assurer que le Content-Type est défini
    if (options.body && typeof options.body === 'string') {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        sessionStorage.removeItem('accessToken');
        window.location.href = '/';
        return Promise.reject('Unauthorized');
    }

    return response;
}

document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-button');
    const logoutButton = document.getElementById('logout-button');
    const tabsContainer = document.getElementById('tabs-content-container');

    let networkIntervalId = null;
    let btStatusIntervalId = null;

    function stopIntervals() {
        if (networkIntervalId) clearInterval(networkIntervalId);
        if (btStatusIntervalId) clearInterval(btStatusIntervalId);
        networkIntervalId = null;
        btStatusIntervalId = null;
    }

    async function loadTabContent(tabName) {
        stopIntervals();
        tabsContainer.innerHTML = '<p style="text-align: center;">Chargement...</p>';

        try {
            const response = await fetchWithAuth(`/tabs/${tabName}`);
            if (!response.ok) throw new Error('Network response was not ok.');
            
            tabsContainer.innerHTML = await response.text();
            initializeTabScripts(tabName);
        } catch (error) {
            tabsContainer.innerHTML = `<p style="text-align: center; color: var(--error-color);">Erreur lors du chargement de l'onglet.</p>`;
            console.error('Error loading tab:', error);
        }
    }

    function initializeTabScripts(tabName) {
        switch (tabName) {
            case 'systeme':
                loadSystemInfo();
                attachPasswordFormListener();
                break;
            case 'wifi':
                loadWifiSettings();
                attachWifiFormListener();
                break;
            case 'reseau':
                loadConnectedDevices();
                networkIntervalId = setInterval(loadConnectedDevices, 10000);
                break;
            case 'bluetooth':
                initializeBluetoothTab();
                btStatusIntervalId = setInterval(getBluetoothStatus, 5000);
                break;
        }
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelector('.tab-button.active').classList.remove('active');
            tab.classList.add('active');
            loadTabContent(tab.dataset.tab);
        });
    });

    logoutButton.addEventListener('click', async () => {
        try {
            // Appeler l'endpoint de déconnexion pour invalider le cookie httpOnly
            await fetchWithAuth('/logout', { method: 'POST' });
        } catch (error) {
            console.error('Erreur lors de la déconnexion:', error);
        } finally {
            // Toujours nettoyer le sessionStorage et rediriger
            sessionStorage.removeItem('accessToken');
            window.location.href = '/';
        }
    });

    // --- Initialisation des onglets ---

    async function loadSystemInfo() {
        try {
            const response = await fetchWithAuth('/api/system/info');
            const data = await response.json();
            document.getElementById('device-name').textContent = data.device_name;
            document.getElementById('device-id').textContent = data.device_id;
            document.getElementById('device-mac').textContent = data.device_mac;
            document.getElementById('sw-version').textContent = data.sw_version;
            document.getElementById('hw-version').textContent = data.hw_version;
        } catch (error) {
            console.error('Erreur chargement infos système:', error);
        }
    }

    function attachPasswordFormListener() {
        const form = document.getElementById('password-change-form');
        if (!form) return;

        const toggleIcons = form.querySelectorAll('.password-toggle-icon');

        toggleIcons.forEach(icon => {
            icon.addEventListener('click', () => {
                const targetInput = icon.previousElementSibling;
                if (targetInput.type === 'password') {
                    targetInput.type = 'text';
                    icon.textContent = '🙈';
                } else {
                    targetInput.type = 'password';
                    icon.textContent = '👁️';
                }
            });
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const old_password = e.target.old_password.value;
            const new_password = e.target.new_password.value;
            try {
                const response = await fetchWithAuth('/api/system/change-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_password, new_password })
                });
                if (response.ok) {
                    alert('Mot de passe mis à jour !');
                    form.reset();
                } else {
                    const errorData = await response.json();
                    alert(`Erreur: ${errorData.detail}`);
                }
            } catch (error) {
                alert('Une erreur est survenue.');
            }
        });
    }

    async function loadWifiSettings() {
        try {
            const response = await fetchWithAuth('/api/wifi/settings');
            const data = await response.json();
            document.getElementById('wifi-ssid').value = data.ssid;
            document.getElementById('wifi-password').value = data.password || '';
        } catch (error) {
            console.error('Erreur chargement config WiFi:', error);
        }
    }

    function attachWifiFormListener() {
        const form = document.getElementById('wifi-settings-form');
        if (!form) return;

        const passwordInput = document.getElementById('wifi-password');
        const toggleIcon = form.querySelector('.password-toggle-icon');

        if (toggleIcon && passwordInput) {
            toggleIcon.addEventListener('click', () => {
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    toggleIcon.textContent = '🙈';
                } else {
                    passwordInput.type = 'password';
                    toggleIcon.textContent = '👁️';
                }
            });
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const ssid = e.target.ssid.value;
            const password = e.target.password.value;
            try {
                const response = await fetchWithAuth('/api/wifi/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ssid, password })
                });
                if (response.ok) {
                    alert('Paramètres WiFi mis à jour !');
                } else {
                    const errorData = await response.json();
                    alert(`Erreur: ${errorData.detail}`);
                }
            } catch (error) {
                alert('Une erreur est survenue.');
            }
        });
    }

    async function loadConnectedDevices() {
        const tableBody = document.querySelector('#connected-devices-table tbody');
        try {
            const response = await fetchWithAuth('/api/network/connected-devices');
            const devices = await response.json();
            if (!tableBody) return;
            tableBody.innerHTML = '';
            if (devices.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="3">Aucun appareil connecté.</td></tr>';
            } else {
                devices.forEach(device => {
                    tableBody.innerHTML += `<tr><td>${device.name}</td><td>${device.ip_address}</td><td>${device.mac_address}</td></tr>`;
                });
            }
        } catch (error) {
            if (tableBody) tableBody.innerHTML = '<tr><td colspan="3">Erreur de chargement.</td></tr>';
        }
    }

    function initializeBluetoothTab() {
        getBluetoothStatus();
        const scanBtn = document.getElementById('bt-scan-btn');
        const disconnectBtn = document.getElementById('bt-disconnect-btn');
        const startBtn = document.getElementById('translation-start-btn');
        const stopBtn = document.getElementById('translation-stop-btn');
        const devicesList = document.getElementById('bt-devices-list');

        scanBtn.addEventListener('click', async () => {
            devicesList.innerHTML = '<li>Scan en cours...</li>';
            scanBtn.disabled = true;
            try {
                const response = await fetchWithAuth('/api/bluetooth/scan', { method: 'POST' });
                const devices = await response.json();
                devicesList.innerHTML = '';
                if (devices.length > 0) {
                    devices.forEach(device => {
                        devicesList.innerHTML += `<li>${device.name} (${device.mac_address}) <button class="btn" data-mac="${device.mac_address}">Connecter</button></li>`;
                    });
                } else {
                    devicesList.innerHTML = '<li>Aucun appareil trouvé.</li>';
                }
            } catch (error) {
                devicesList.innerHTML = '<li>Erreur lors du scan.</li>';
            } finally {
                scanBtn.disabled = false;
            }
        });

        devicesList.addEventListener('click', async (e) => {
            if (e.target.tagName === 'BUTTON' && e.target.dataset.mac) {
                e.target.textContent = '...';
                e.target.disabled = true;
                try {
                    const response = await fetchWithAuth('/api/bluetooth/connect', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mac_address: e.target.dataset.mac })
                    });
                    if (response.ok) getBluetoothStatus();
                    else alert(`Erreur: ${(await response.json()).detail}`);
                } catch (error) {
                    alert('Erreur de connexion.');
                }
            }
        });

        disconnectBtn.addEventListener('click', async () => {
            try {
                const response = await fetchWithAuth('/api/bluetooth/disconnect', { method: 'POST' });
                if (response.ok) getBluetoothStatus();
                else alert(`Erreur: ${(await response.json()).detail}`);
            } catch (error) { alert('Erreur de déconnexion.'); }
        });

        startBtn.addEventListener('click', async () => {
            try {
                await fetchWithAuth('/api/bluetooth/translation/start', { method: 'POST' });
                getBluetoothStatus();
            } catch (error) { alert('Erreur au démarrage.'); }
        });

        stopBtn.addEventListener('click', async () => {
            try {
                await fetchWithAuth('/api/bluetooth/translation/stop', { method: 'POST' });
                getBluetoothStatus();
            } catch (error) { alert("Erreur à l'arrêt."); }
        });
    }

    async function getBluetoothStatus() {
        try {
            const response = await fetchWithAuth('/api/bluetooth/status');
            const status = await response.json();
            updateBluetoothUI(status);
        } catch (error) {
            console.error('Erreur statut Bluetooth:', error);
        }
    }

    function updateBluetoothUI(status) {
        const deviceSpan = document.getElementById('bt-connected-device');
        const statusSpan = document.getElementById('translation-status');
        const disconnectBtn = document.getElementById('bt-disconnect-btn');
        const startBtn = document.getElementById('translation-start-btn');
        const stopBtn = document.getElementById('translation-stop-btn');

        if (!deviceSpan) return; // Tab not loaded

        if (status.connected_device) {
            deviceSpan.textContent = `${status.connected_device.name} (${status.connected_device.mac_address})`;
            disconnectBtn.style.display = 'inline-block';
            startBtn.disabled = status.is_translating;
            stopBtn.disabled = !status.is_translating;
        } else {
            deviceSpan.textContent = 'Aucun';
            disconnectBtn.style.display = 'none';
            startBtn.disabled = true;
            stopBtn.disabled = true;
        }
        statusSpan.textContent = `État : ${status.is_translating ? 'Actif' : 'Inactif'}`;
    }

    // --- Chargement initial ---
    loadTabContent('systeme');
});