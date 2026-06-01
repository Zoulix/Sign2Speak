#!/usr/bin/env python3
"""
Gestionnaire Bluetooth utilisant BlueZ pour l'appareillage et la connexion audio.
Implémente les étapes: Scan -> Pair -> Trust -> Connect -> Audio Routing
Basé sur le script bt_manager.py fonctionnel
"""

import subprocess
import time
import re
from typing import List, Optional, Dict, Any

from .. import models


class BluetoothManager:
    """Gestionnaire pour les opérations Bluetooth via BlueZ"""
    
    def __init__(self):
        # On s'assure que le Bluetooth est activé au démarrage
        try:
            subprocess.run(['bluetoothctl', 'power', 'on'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("Impossible d'activer le Bluetooth")
        
        self.connected_device: Optional[models.BluetoothDevice] = None
        self.is_translating = False
        
    def scan_devices(self, duration: int = 8) -> List[models.BluetoothDevice]:
        """
        Scan des appareils Bluetooth disponibles
        
        Args:
            duration: Durée du scan en secondes
            
        Returns:
            Liste des appareils découverts
        """
        print(f"--- Recherche d'appareils ({duration}s)... ---")
        
        # Lance le scan en tâche de fond
        scan_proc = subprocess.Popen(['bluetoothctl', 'scan', 'on'], stdout=subprocess.DEVNULL)
        time.sleep(duration)
        
        # Récupère la liste des périphériques détectés
        out = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True)
        scan_proc.terminate()  # Arrête le scan
        subprocess.run(['bluetoothctl', 'scan', 'off'], stdout=subprocess.DEVNULL)

        devices = []
        for line in out.stdout.splitlines():
            # Regex pour extraire l'adresse MAC et le nom
            match = re.search(r"Device (([0-9A-F]{2}:){5}[0-9A-F]{2}) (.*)", line)
            if match:
                mac_address = match.group(1)
                name = match.group(3)
                # Ajouter tous les appareils (comme dans le script original)
                devices.append(models.BluetoothDevice(name=name, mac_address=mac_address))
        
        print(f"Appareils audio découverts: {len(devices)}")
        return devices
    
    def pair_device(self, mac_address: str) -> bool:
        """
        Appaire un appareil Bluetooth
        
        Args:
            mac_address: Adresse MAC de l'appareil
            
        Returns:
            True si l'appairage a réussi
        """
        print(f"Tentative d'appairage avec {mac_address}...")
        
        # Vérifier si l'appareil est déjà appairé
        paired_result = subprocess.run(['bluetoothctl', 'paired-devices'], capture_output=True, text=True)
        if mac_address in paired_result.stdout:
            print(f"L'appareil {mac_address} est déjà appairé")
            return True
        
        try:
            subprocess.run(['bluetoothctl', 'pair', mac_address], timeout=15, check=True, capture_output=True)
            print(f"Appairage réussi avec {mac_address}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Échec de l'appairage: {e}")
            return False
        except subprocess.TimeoutExpired:
            print("Timeout lors de l'appairage")
            return False
    
    def trust_device(self, mac_address: str) -> bool:
        """
        Ajouter un appareil à la liste de confiance (reconnexion automatique)
        
        Args:
            mac_address: Adresse MAC de l'appareil
            
        Returns:
            True si l'appareil est maintenant de confiance
        """
        print(f"Ajout de {mac_address} à la liste de confiance...")
        
        try:
            subprocess.run(['bluetoothctl', 'trust', mac_address], check=True, capture_output=True)
            print(f"Appareil {mac_address} maintenant de confiance")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Échec de l'ajout à la confiance: {e}")
            return False
    
    def connect_device(self, mac_address: str) -> bool:
        """
        Connecter un appareil Bluetooth et établir la liaison audio
        
        Args:
            mac_address: Adresse MAC de l'appareil
            
        Returns:
            True si la connexion a réussi
        """
        print(f"--- Tentative de connexion à : {mac_address} ---")
        
        try:
            # 1. Appairage (Pair)
            if not self.pair_device(mac_address):
                return False
            
            # 2. Confiance (Trust) - Indispensable pour que le Pi se reconnecte seul plus tard
            if not self.trust_device(mac_address):
                return False
            
            # 3. Connexion (Connect)
            res = subprocess.run(['bluetoothctl', 'connect', mac_address], capture_output=True, text=True, timeout=30)
            
            if "Connection successful" in res.stdout or "already connected" in res.stdout:
                print("✅ Succès : L'enceinte est prête !")
                
                # Récupérer le nom de l'appareil
                info_result = subprocess.run(['bluetoothctl', 'info', mac_address], capture_output=True, text=True)
                device_name = mac_address  # Nom par défaut
                if info_result.returncode == 0:
                    name_pattern = r"Name: (.+)"
                    match = re.search(name_pattern, info_result.stdout)
                    if match:
                        device_name = match.group(1)
                
                self.connected_device = models.BluetoothDevice(
                    name=device_name,
                    mac_address=mac_address
                )
                
                # Router l'audio vers l'appareil
                self._route_audio_to_device(mac_address)
                
                return True
            else:
                print("❌ Échec de la connexion finale.")
                print(f"Sortie: {res.stdout}")
                print(f"Erreur: {res.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("Timeout lors de la connexion")
            return False
        except Exception as e:
            print(f"⚠️ Erreur lors de l'appareillage : {e}")
            return False
    
    def disconnect_device(self) -> bool:
        """
        Déconnecter l'appareil Bluetooth actuel
        
        Returns:
            True si la déconnexion a réussi
        """
        if not self.connected_device:
            print("Aucun appareil à déconnecter")
            return True
        
        if self.is_translating:
            print("Impossible de déconnecter pendant la traduction")
            return False
        
        print(f"Déconnexion de {self.connected_device.mac_address}...")
        
        try:
            subprocess.run(['bluetoothctl', 'disconnect', self.connected_device.mac_address], 
                         check=True, capture_output=True)
            print(f"Déconnexion réussie de {self.connected_device.mac_address}")
            self.connected_device = None
            return True
        except subprocess.CalledProcessError as e:
            print(f"Échec de la déconnexion: {e}")
            return False
    
    def _route_audio_to_device(self, mac_address: str) -> bool:
        """
        Router le son vers l'appareil Bluetooth connecté
        
        Args:
            mac_address: Adresse MAC de l'appareil
            
        Returns:
            True si le routage audio a réussi
        """
        print(f"Routage audio vers {mac_address}...")
        
        try:
            # Utiliser PulseAudio pour router le son
            # D'abord trouver le sink PulseAudio correspondant
            sink_result = subprocess.run(['pactl', 'list', 'sinks', 'short'], 
                                      capture_output=True, text=True)
            
            if sink_result.returncode != 0:
                print(f"Erreur lors de la liste des sinks audio: {sink_result.stderr}")
                return False
            
            # Chercher le sink Bluetooth correspondant
            bluez_sink = None
            mac_normalized = mac_address.replace(':', '_').lower()
            for line in sink_result.stdout.split('\n'):
                if 'bluez' in line.lower() and mac_normalized in line.lower():
                    bluez_sink = line.split('\t')[0]  # Premier élément est le nom du sink
                    break
            
            if not bluez_sink:
                print(f"Aucun sink audio trouvé pour {mac_address}")
                print("Sinks disponibles:")
                print(sink_result.stdout)
                return False
            
            # Définir ce sink comme défaut
            set_default_result = subprocess.run(['pactl', 'set-default-sink', bluez_sink], 
                                             capture_output=True, text=True)
            
            if set_default_result.returncode == 0:
                print(f"Audio routé vers {bluez_sink}")
                return True
            else:
                print(f"Échec du routage audio: {set_default_result.stderr}")
                return False
                
        except Exception as e:
            print(f"Erreur lors du routage audio: {e}")
            return False
    
    def get_status(self) -> models.BluetoothStatus:
        """
        Obtenir le statut actuel du Bluetooth
        
        Returns:
            Objet BluetoothStatus avec l'état actuel
        """
        return models.BluetoothStatus(
            connected_device=self.connected_device,
            is_translating=self.is_translating
        )
    
    def start_translation(self) -> bool:
        """
        Démarrer la traduction (simulation)
        
        Returns:
            True si le démarrage a réussi
        """
        if not self.connected_device:
            print("Aucun appareil connecté pour démarrer la traduction")
            return False
        
        print("Démarrage de la traduction...")
        self.is_translating = True
        return True
    
    def stop_translation(self) -> bool:
        """
        Arrêter la traduction (simulation)
        
        Returns:
            True si l'arrêt a réussi
        """
        print("Arrêt de la traduction...")
        self.is_translating = False
        return True


# Instance globale du gestionnaire Bluetooth
bluetooth_manager = BluetoothManager()
