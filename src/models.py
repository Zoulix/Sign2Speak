from pydantic import BaseModel

# --- Modèles de Données ---

# Modèle pour le changement de mot de passe
class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# Modèle pour la configuration WiFi
class WifiSettings(BaseModel):
    ssid: str
    password: str | None = None

# Modèle pour un appareil connecté
class ConnectedDevice(BaseModel):
    name: str
    ip_address: str
    mac_address: str

# Modèles pour le Bluetooth
class BluetoothDevice(BaseModel):
    name: str
    mac_address: str

class BluetoothStatus(BaseModel):
    connected_device: BluetoothDevice | None = None
    is_translating: bool = False

class ConnectRequest(BaseModel):
    mac_address: str
