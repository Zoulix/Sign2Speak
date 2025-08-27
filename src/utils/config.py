import json
from pathlib import Path
from .. import models
from . import security

# --- Configuration Persistante ---

CONFIG_DIR = Path(__file__).parent.parent.parent # Racine du projet
USER_CONFIG_FILE = CONFIG_DIR / "user_config.json"

def load_user_db():
    """Charge la base de données utilisateur depuis le fichier JSON.
    Crée le fichier avec un utilisateur par défaut si il n'existe pas.
    """
    if not USER_CONFIG_FILE.exists():
        print(f"Fichier de configuration utilisateur non trouvé. Création de {USER_CONFIG_FILE}...")
        default_user = {"admin": security.get_password_hash("admin")}
        save_user_db(default_user)
        return default_user
    
    with open(USER_CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_user_db(db_dict):
    """Sauvegarde la base de données utilisateur dans le fichier JSON."""
    with open(USER_CONFIG_FILE, 'w') as f:
        json.dump(db_dict, f, indent=4)

# Base de données utilisateur (chargée depuis le fichier)
FAKE_DB = load_user_db()


# --- Données Factices en Mémoire ---


# Configuration WiFi factice
FAKE_WIFI_CONFIG = models.WifiSettings(ssid="S2S_Device_AP", password="sign2speak")

# État Bluetooth factice
FAKE_BT_STATUS = models.BluetoothStatus()

# Appareils Bluetooth scannés factices
FAKE_SCANNED_DEVICES = [
    models.BluetoothDevice(name="JBL Go 3", mac_address="11:22:33:AA:BB:CC"),
    models.BluetoothDevice(name="Sony WH-1000XM4", mac_address="44:55:66:DD:EE:FF"),
]
