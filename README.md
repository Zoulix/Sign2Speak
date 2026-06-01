# Sign2Speak - Dispositif embarqué de traduction de la langue des signes

Projet de conception d'un système embarqué autonome capable de capturer des gestes en langue des signes via une caméra, les traduire en phrases audio, et diffuser les traductions en temps réel via Bluetooth.

## Architecture

- **Backend** : FastAPI avec Python
- **Frontend** : HTML/CSS/JavaScript responsive
- **Bluetooth** : Gestion via BlueZ (Pair → Trust → Connect → Audio Routing)
- **Audio** : PulseAudio pour le routage du son

## Installation

### Prérequis

- Raspberry Pi (ou système Linux compatible)
- Python 3.8+
- Adaptateur Bluetooth intégré ou USB
- Caméra pour la capture des gestes

### Installation des dépendances

```bash
# Cloner le projet
git clone <repository-url>
cd Sign2Speak

# Exécuter le script d'installation
./install_bluetooth_deps.sh

# Ou installer manuellement :
sudo apt-get update
sudo apt-get install -y bluetooth bluez bluez-tools pulseaudio pulseaudio-module-bluetooth pulseaudio-utils
pip install -r requirements.txt
```

### Configuration

1. **Permissions Bluetooth** : Ajoutez votre utilisateur au groupe `bluetooth` :
   ```bash
   sudo usermod -a -G bluetooth $USER
   # Redémarrez votre session ou exécutez : newgrp bluetooth
   ```

2. **Configuration PulseAudio** : Le script d'installation charge automatiquement les modules nécessaires.

## Utilisation

### Démarrage du serveur

```bash
# Développement avec rechargement automatique
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Interface Web

1. Connectez-vous au point d'accès Wi-Fi du dispositif
2. Ouvrez un navigateur et accédez à l'adresse IP du Raspberry Pi
3. Identifiez-vous avec les identifiants par défaut :
   - Nom d'utilisateur : `admin`
   - Mot de passe : `admin`

### Gestion Bluetooth

L'interface web permet de :

1. **Scanner** les appareils Bluetooth audio disponibles
2. **Connecter** un appareil (processus automatique : Pair → Trust → Connect)
3. **Router** l'audio vers l'appareil connecté
4. **Démarrer/Arrêter** la traduction

Le son bascule automatiquement vers l'enceinte/casque dès que la connexion est réussie.

## Test du Bluetooth

Pour tester la gestion Bluetooth indépendamment de l'interface web :

```bash
python3 test_bluetooth.py
```

Ce script teste :
- Le scan des appareils
- L'appairage
- L'ajout à la liste de confiance
- La connexion
- Le routage audio
- La déconnexion

## Structure du Projet

```
Sign2Speak/
├── src/                    # Code source Python
│   ├── main.py            # Application FastAPI principale
│   ├── models.py          # Modèles de données Pydantic
│   └── utils/             # Utilitaires
│       ├── bluetooth_manager.py  # Gestionnaire Bluetooth BlueZ
│       ├── security.py     # Authentification JWT
│       └── config.py       # Configuration
├── web/                    # Frontend
│   ├── static/            # CSS, JS, images
│   └── templates/         # Templates HTML
├── test_model/            # Tests et modèles ML
├── boot_service/          # Scripts de démarrage
├── requirements.txt       # Dépendances Python
├── install_bluetooth_deps.sh  # Script d'installation
├── test_bluetooth.py      # Script de test Bluetooth
└── README.md             # Ce fichier
```

## Fonctionnalités

### Interface Web Responsive

- **Page de connexion** sécurisée avec JWT
- **Tableau de bord** avec onglets :
  - **Système** : Informations et configuration
  - **Wi-Fi** : Paramètres du point d'accès
  - **Réseau** : Appareils connectés
  - **Bluetooth** : Appareillage et contrôle de traduction

### Gestion Bluetooth

Le système implémente un processus de connexion robuste :

1. **Scan** : Découverte des appareils audio Bluetooth
2. **Pair** : Appairage sécurisé avec l'appareil
3. **Trust** : Ajout à la liste de confiance (reconnexion automatique)
4. **Connect** : Établissement de la connexion
5. **Audio Routing** : Basculement automatique du son vers l'appareil

### Sécurité

- Authentification par token JWT
- Cookies HTTP-only sécurisés
- Validation des entrées utilisateur

## Dépannage

### Problèmes courants

1. **Bluetooth ne fonctionne pas** :
   ```bash
   sudo systemctl status bluetooth
   sudo systemctl restart bluetooth
   ```

2. **Audio ne route pas vers le Bluetooth** :
   ```bash
   pactl load-module module-bluetooth-discover
   pactl list sinks short
   ```

3. **Permissions refusées** :
   ```bash
   groups $USER  # Vérifiez que 'bluetooth' est dans la liste
   sudo usermod -a -G bluetooth $USER
   ```

### Logs

Pour voir les logs de l'application :
```bash
# En développement
uvicorn src.main:app --reload --log-level debug

# Logs système Bluetooth
sudo journalctl -u bluetooth
```

## Développement

### Ajout de fonctionnalités

1. **Nouveaux endpoints** : Ajoutez dans `src/main.py`
2. **Modèles de données** : Définissez dans `src/models.py`
3. **Utilitaires** : Créez dans `src/utils/`
4. **Frontend** : Modifiez les templates dans `web/templates/`

### Tests

```bash
# Test Bluetooth
python3 test_bluetooth.py

# Tests unitaires (à implémenter)
pytest tests/
```

## Licence

[À définir]

## Contributing

[À définir]