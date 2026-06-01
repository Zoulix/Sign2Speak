#!/usr/bin/env python3
"""
Script de test pour le gestionnaire Bluetooth
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.bluetooth_manager import BluetoothManager


def test_bluetooth_manager():
    """Test des fonctionnalités du gestionnaire Bluetooth"""
    
    print("=== Test du Gestionnaire Bluetooth ===\n")
    
    manager = BluetoothManager()
    
    # 1. Test de scan
    print("1. Test de scan des appareils...")
    devices = manager.scan_devices(duration=5)
    print(f"Appareils trouvés: {len(devices)}")
    for device in devices:
        print(f"  - {device.name} ({device.mac_address})")
    print()
    
    if not devices:
        print("Aucun appareil trouvé. Arrêt du test.")
        return
    
    # 2. Test de connexion avec le premier appareil trouvé
    test_device = devices[0]
    print(f"2. Test de connexion avec {test_device.name}...")
    
    # Test de connexion complète
    connect_success = manager.connect_device(test_device.mac_address)
    print(f"Connexion: {'✓' if connect_success else '✗'}")
    print()
    
    # 3. Test du statut
    print("3. Test du statut...")
    status = manager.get_status()
    print(f"Appareil connecté: {status.connected_device.name if status.connected_device else 'None'}")
    print(f"Traduction active: {status.is_translating}")
    print()
    
    # 4. Test de traduction
    if status.connected_device:
        print("4. Test de la traduction...")
        start_success = manager.start_translation()
        print(f"Démarrage traduction: {'✓' if start_success else '✗'}")
        
        import time
        time.sleep(2)  # Simulation de traduction
        
        stop_success = manager.stop_translation()
        print(f"Arrêt traduction: {'✓' if stop_success else '✗'}")
        print()
    
    # 5. Test de déconnexion
    if status.connected_device:
        print("5. Test de déconnexion...")
        disconnect_success = manager.disconnect_device()
        print(f"Déconnexion: {'✓' if disconnect_success else '✗'}")
        print()
    
    print("=== Test terminé ===")


if __name__ == "__main__":
    try:
        test_bluetooth_manager()
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
    except Exception as e:
        print(f"\nErreur lors du test: {e}")
        import traceback
        traceback.print_exc()
