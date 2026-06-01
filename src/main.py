from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

from .utils import security
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio

from . import models
from .utils import security
from .utils.config import FAKE_DB, FAKE_WIFI_CONFIG, save_user_db
from .utils.bluetooth_manager import bluetooth_manager

# Initialisation de l'application
app = FastAPI()

# Montage des fichiers statiques (CSS, JS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Configuration des templates HTML
templates = Jinja2Templates(directory="web/templates")


# --- Pages HTML ---

# Route pour la page de connexion
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Route pour le tableau de bord
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, token: Optional[str] = None):
    # Vérification simple via query param pour le chargement initial de la page
    # La vraie sécurité se fera via les headers pour les appels API
    try:
        if not token:
            token = request.cookies.get("access_token")
        if not token:
            return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        
        await security.get_current_user(token.split(" ")[-1]) # Vérifie si le token est valide
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except HTTPException:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    # Pour l'instant, on n'a pas de gestion de session, on sert juste la page
    # Dans un vrai projet, il faudrait vérifier l'authentification
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/tabs/{tab_name}", response_class=HTMLResponse)
async def get_tab_content(request: Request, tab_name: str, user: dict = Depends(security.get_current_user)):
    # Sécurité simple pour s'assurer que seuls les onglets valides sont servis
    valid_tabs = {
        "systeme": "system",
        "wifi": "wifi",
        "reseau": "network",
        "bluetooth": "bluetooth"
    }

    if tab_name not in valid_tabs:
        raise HTTPException(status_code=404, detail="Onglet non trouvé")

    template_name = valid_tabs[tab_name]
    return templates.TemplateResponse(f"tabs/{template_name}.html", {"request": request})


# --- Endpoints API ---

# Endpoint pour l'authentification
@app.post("/login")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user_hash = FAKE_DB.get(form_data.username)
    if not user_hash or not security.verify_password(form_data.password, user_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": form_data.username})
    
    # Le token est retourné dans le corps et dans un cookie httpOnly
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite='lax')
    return {"access_token": access_token, "token_type": "bearer"}

# --- API pour le tableau de bord ---

@app.get("/api/system/info")
async def get_system_info(user: dict = Depends(security.get_current_user)):
    # Données factices pour la démonstration
    return {
        "device_name": "S2S-Device-001",
        "device_id": "S2S-MAT789-2024",
        "device_mac": "00:1B:44:11:3A:B7",
        "sw_version": "1.0.2",
        "hw_version": "1.1.0"
    }

@app.post("/api/system/change-password")
async def change_password(pass_data: models.PasswordChange, current_user: dict = Depends(security.get_current_user)):
    username = current_user['username']
    if not security.verify_password(pass_data.old_password, FAKE_DB[username]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'ancien mot de passe est incorrect.",
        )
    FAKE_DB[username] = security.get_password_hash(pass_data.new_password)
    save_user_db(FAKE_DB) # Sauvegarde la mise à jour dans le fichier JSON
    return {"success": True, "message": "Mot de passe mis à jour avec succès."}

@app.get("/api/wifi/settings", response_model=models.WifiSettings)
async def get_wifi_settings(user: dict = Depends(security.get_current_user)):
    return FAKE_WIFI_CONFIG

@app.post("/api/wifi/settings")
async def set_wifi_settings(settings: models.WifiSettings, user: dict = Depends(security.get_current_user)):
    global FAKE_WIFI_CONFIG
    # Validation simple
    if len(settings.ssid) < 1:
        raise HTTPException(status_code=400, detail="Le SSID ne peut pas être vide.")
    if settings.password and len(settings.password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caractères.")
    
    FAKE_WIFI_CONFIG = settings
    # Dans un vrai cas, on appellerait un script pour mettre à jour la configuration système (hostapd, etc.)
    print(f"WiFi settings updated: SSID={settings.ssid}, Password={'*' * len(settings.password) if settings.password else 'None'}")
    return {"success": True, "message": "Paramètres WiFi mis à jour avec succès."}

@app.get("/api/network/connected-devices", response_model=list[models.ConnectedDevice])
async def get_connected_devices(user: dict = Depends(security.get_current_user)):
    # Données factices. Dans un cas réel, on lirait les baux DHCP.
    return [
        models.ConnectedDevice(name="Smartphone-John", ip_address="192.168.4.2", mac_address="A1:B2:C3:D4:E5:F6"),
        models.ConnectedDevice(name="Laptop-Jane", ip_address="192.168.4.3", mac_address="F6:E5:D4:C3:B2:A1"),
    ]
    # Données factices. Dans un cas réel, on lirait les baux DHCP.
    return [
        ConnectedDevice(name="Smartphone-John", ip_address="192.168.4.2", mac_address="A1:B2:C3:D4:E5:F6"),
        ConnectedDevice(name="Laptop-Jane", ip_address="192.168.4.3", mac_address="F6:E5:D4:C3:B2:A1"),
    ]

@app.get("/api/bluetooth/status", response_model=models.BluetoothStatus)
def get_bluetooth_status(user: dict = Depends(security.get_current_user)):
    return bluetooth_manager.get_status()

@app.post("/api/bluetooth/scan", response_model=list[models.BluetoothDevice])
def scan_bluetooth_devices(user: dict = Depends(security.get_current_user)):
    """Scanne les appareils Bluetooth audio disponibles"""
    devices = bluetooth_manager.scan_devices(duration=8)
    return devices

@app.post("/api/bluetooth/connect")
def connect_bluetooth_device(payload: models.ConnectRequest, user: dict = Depends(security.get_current_user)):
    """Connecte un appareil Bluetooth (Pair -> Trust -> Connect -> Audio Routing)"""
    success = bluetooth_manager.connect_device(payload.mac_address)
    if not success:
        raise HTTPException(status_code=400, detail="Échec de la connexion à l'appareil.")
    
    status = bluetooth_manager.get_status()
    return {"success": True, "message": f"Connecté à {status.connected_device.name}"}

@app.post("/api/bluetooth/disconnect")
def disconnect_bluetooth_device(user: dict = Depends(security.get_current_user)):
    """Déconnecte l'appareil Bluetooth actuel"""
    success = bluetooth_manager.disconnect_device()
    if not success:
        raise HTTPException(status_code=400, detail="Échec de la déconnexion.")
    
    return {"success": True, "message": "Appareil déconnecté."}

@app.post("/api/bluetooth/translation/start")
def start_translation(user: dict = Depends(security.get_current_user)):
    """Démarre la traduction (requiert un appareil connecté)"""
    success = bluetooth_manager.start_translation()
    if not success:
        raise HTTPException(status_code=400, detail="Impossible de démarrer la traduction.")
    
    return {"success": True, "message": "Traduction démarrée."}

@app.post("/api/bluetooth/translation/stop")
def stop_translation(user: dict = Depends(security.get_current_user)):
    """Arrête la traduction"""
    success = bluetooth_manager.stop_translation()
    return {"success": True, "message": "Traduction arrêtée."}

@app.post("/logout")
async def logout(response: Response):
    """Déconnecte l'utilisateur en supprimant le cookie d'accès."""
    response.delete_cookie("access_token")
    return {"success": True, "message": "Déconnexion réussie"}
