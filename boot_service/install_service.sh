#!/bin/bash
# Script d'installation du service systemd Sign2Speak
# Ce script configure et installe le service pour démarrage automatique

set -e

echo "=== Installation du service Sign2Speak ==="

# Détection du répertoire du projet
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Détection de l'utilisateur actuel
CURRENT_USER=$(whoami)
USER_ID=$(id -u)

# Détection du venv
if [ -d "$PROJECT_DIR/venv" ]; then
    VENV_PATH="$PROJECT_DIR/venv"
elif [ -d "$PROJECT_DIR/.venv" ]; then
    VENV_PATH="$PROJECT_DIR/.venv"
else
    echo "⚠️  Aucun environnement virtuel trouvé (venv ou .venv)"
    echo "Veuillez créer un environnement virtuel d'abord:"
    echo "  python -m venv venv"
    exit 1
fi

# Affichage des valeurs détectées
echo "Utilisateur: $CURRENT_USER"
echo "ID utilisateur: $USER_ID"
echo "Répertoire du projet: $PROJECT_DIR"
echo "Chemin du venv: $VENV_PATH"
echo ""

# Confirmation
read -p "Ces valeurs sont-elles correctes ? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation annulée."
    exit 1
fi

# Génération du fichier service
SERVICE_FILE="/tmp/sign2speak.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Serveur FastAPI Sign2Speak
After=network.target sound.target

[Service]
User=$CURRENT_USER
Environment=XDG_RUNTIME_DIR=/run/user/$USER_ID
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_PATH/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "Fichier service généré: $SERVICE_FILE"

# Installation du service
echo "Installation du service systemd..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/sign2speak.service

# Rechargement systemd
echo "Rechargement de systemd..."
sudo systemctl daemon-reload

# Activation du service
echo "Activation du service pour démarrage automatique..."
sudo systemctl enable sign2speak.service

echo ""
echo "✅ Service Sign2Speak installé avec succès !"
echo ""
echo "Commandes utiles:"
echo "  sudo systemctl start sign2speak    - Démarrer le service"
echo "  sudo systemctl stop sign2speak     - Arrêter le service"
echo "  sudo systemctl restart sign2speak  - Redémarrer le service"
echo "  sudo systemctl status sign2speak   - Voir l'état du service"
echo "  journalctl -u sign2speak -f        - Voir les logs"
echo ""
echo "Le service démarrera automatiquement au prochain redémarrage."
echo "Pour le démarrer maintenant: sudo systemctl start sign2speak"
