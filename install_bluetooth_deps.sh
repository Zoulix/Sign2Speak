#!/bin/bash
# Script d'installation des dépendances Bluetooth pour Sign2Speak

echo "=== Installation des dépendances Bluetooth pour Sign2Speak ==="

# Vérifier si on est sur un système basé sur Debian/Ubuntu
if ! command -v apt-get &> /dev/null; then
    echo "Ce script est conçu pour les systèmes Debian/Ubuntu. Veuillez adapter pour votre distribution."
    exit 1
fi

# Mettre à jour les paquets
echo "Mise à jour des paquets..."
sudo apt-get update

# Installer les dépendances BlueZ
echo "Installation de BlueZ et outils associés..."
sudo apt-get install -y \
    bluetooth \
    bluez \
    bluez-tools \
    pulseaudio \
    pulseaudio-module-bluetooth \
    pulseaudio-utils

# Installer les dépendances Python si nécessaire
echo "Installation des dépendances Python..."
pip install -r requirements.txt

# Configurer PulseAudio pour le Bluetooth
echo "Configuration de PulseAudio..."
# Charger le module Bluetooth pour PulseAudio
pactl load-module module-bluetooth-discover
pactl load-module module-bluez5-device

# Donner les permissions nécessaires à l'utilisateur
echo "Configuration des permissions..."
# Ajouter l'utilisateur au groupe bluetooth
sudo usermod -a -G bluetooth $USER

# Activer et démarrer le service Bluetooth
echo "Configuration du service Bluetooth..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

echo ""
echo "=== Installation terminée ==="
echo ""
echo "Veuillez redémarrer votre session ou exécuter 'newgrp bluetooth' pour que les changements de groupe prennent effet."
echo ""
echo "Pour tester l'installation, vous pouvez exécuter :"
echo "  bluetoothctl --version"
echo "  pactl list sinks short"
echo ""
echo "Pour tester le gestionnaire Bluetooth :"
echo "  python3 test_bluetooth.py"
