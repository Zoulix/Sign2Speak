import subprocess
import time
import re

class BluetoothManager:
    def __init__(self):
        # On s'assure que le Bluetooth est activé au démarrage du script
        subprocess.run(['bluetoothctl', 'power', 'on'], check=True)

    def scan_devices(self, duration=8):
        print(f"--- Recherche d'appareils ({duration}s)... ---")
        # Lance le scan en tâche de fond
        scan_proc = subprocess.Popen(['bluetoothctl', 'scan', 'on'], stdout=subprocess.DEVNULL)
        time.sleep(duration)
        
        # Récupère la liste des périphériques détectés
        out = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True)
        scan_proc.terminate() # Arrête le scan
        subprocess.run(['bluetoothctl', 'scan', 'off'], stdout=subprocess.DEVNULL)

        devices = []
        for line in out.stdout.splitlines():
            # Regex pour extraire l'adresse MAC et le nom
            match = re.search(r"Device (([0-9A-F]{2}:){5}[0-9A-F]{2}) (.*)", line)
            if match:
                devices.append({"mac": match.group(1), "name": match.group(3)})
        return devices

    def connect_device(self, mac_address):
        print(f"--- Tentative de connexion à : {mac_address} ---")
        try:
            # 1. Appairage (Pair)
            subprocess.run(['bluetoothctl', 'pair', mac_address], timeout=15, check=True)
            # 2. Confiance (Trust) - Indispensable pour que le Pi se reconnecte seul plus tard
            subprocess.run(['bluetoothctl', 'trust', mac_address], check=True)
            # 3. Connexion (Connect)
            res = subprocess.run(['bluetoothctl', 'connect', mac_address], capture_output=True, text=True)
            
            if "Connection successful" in res.stdout or "already connected" in res.stdout:
                print("✅ Succès : L'enceinte est prête !")
                return True
            else:
                print("❌ Échec de la connexion finale.")
                return False
        except Exception as e:
            print(f"⚠️ Erreur lors de l'appareillage : {e}")
            return False

# --- EXEMPLE D'UTILISATION ---
if __name__ == "__main__":
    bt = BluetoothManager()
    found = bt.scan_devices(5)
    
    if found:
        for i, dev in enumerate(found):
            print(f"{i} : {dev['name']} ({dev['mac']})")
        
        choix = input("Entrez le numéro de l'appareil à connecter : ")
        target_mac = found[int(choix)]['mac']
        
        if bt.connect_device(target_mac):
            print("🚀 La caméra peut maintenant démarrer !")
            # C'est ici que tu lances ton thread Caméra + MediaPipe