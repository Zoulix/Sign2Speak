# Sign2Speak - Système de Traduction de Langue des Signes

Système embarqué autonome capable de capturer des gestes en langue des signes via une caméra, les traduire en phrases audio, et diffuser les traductions en temps réel via Bluetooth.

## 🎯 Présentation

Sign2Speak est une application web complète qui combine :
- **Capture vidéo** en temps réel via caméra
- **Reconnaissance de signes** utilisant MediaPipe et TFLite
- **Traduction** via un modèle LLM (Llama)
- **Synthèse vocale** via Piper TTS
- **Diffusion audio** via Bluetooth vers enceintes/casques

Le système fonctionne sur **Raspberry Pi 5** et **PC Linux**, avec des optimisations automatiques pour chaque plateforme.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Web (Navigateur)                   │
│  - Interface utilisateur responsive                         │
│  - Polling vidéo (200ms)                                    │
│  - Requêtes API (Bluetooth, Traduction)                     │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Serveur FastAPI                           │
│  - Authentification JWT                                      │
│  - Endpoints API (Bluetooth, Traduction, Vidéo)            │
│  - Orchestration des composants                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├──────────────────────────────────────┐
                     │                                      │
                     ▼                                      ▼
┌─────────────────────────────┐           ┌─────────────────────────────┐
│   TranslationEngine         │           │   BluetoothManager          │
│   (Thread séparé)           │           │   (BlueZ + PipeWire)        │
│                             │           │                             │
│  - Capture vidéo (OpenCV)   │           │  - Scan appareils            │
│  - MediaPipe Holistic       │           │  - Pairage/Connexion         │
│  - TFLite (ai_edge_litert)  │           │  - Routage audio             │
│  - Llama (LLM)              │           │                             │
│  - Piper (TTS)              │           │                             │
└─────────────────────────────┘           └─────────────────────────────┘
```

## 📋 Prérequis

### Matériel
- **Raspberry Pi 5** (recommandé) ou PC Linux
- Caméra USB ou caméra intégrée
- Adaptateur Bluetooth (intégré ou USB)
- Enceinte ou casque Bluetooth

### Logiciel
- Python 3.8+
- Linux (Raspberry Pi OS, Ubuntu, etc.)
- BlueZ (gestion Bluetooth)
- PipeWire ou PulseAudio (routage audio)

## 🚀 Installation

### 1. Cloner le projet

```bash
git clone <repository-url>
cd Sign2Speak
```

### 2. Installer les dépendances système

```bash
# Sur Raspberry Pi / Ubuntu
sudo apt-get update
sudo apt-get install -y \
    bluetooth bluez bluez-tools \
    pipewire pipewire-audio-client-libraries \
    pipewire-pulse \
    python3-dev python3-pip \
    libopencv-dev python3-opencv
```

### 3. Créer l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 5. Configurer la caméra

⚠️ **Important** : Vous devez adapter l'index de votre caméra dans le code.

Pour trouver l'index de votre caméra :

```bash
# Lister les périphériques vidéo
ls /dev/video*
# Vous verrez probablement /dev/video0, /dev/video1, etc.
```

Ensuite, modifiez l'index dans `src/utils/translation_engine.py` :

```python
def __init__(self, camera_index: int = 2, bt_sink: Optional[str] = None):
    self.camera_index = camera_index  # Changez 2 par votre index (0, 1, 2, ...)
```

Par défaut, l'index est `2`. Testez avec `0` si vous avez une seule caméra.

### 6. Configurer les permissions Bluetooth

```bash
sudo usermod -a -G bluetooth $USER
# Redémarrez votre session ou exécutez :
newgrp bluetooth
```

## 🎮 Utilisation

### Démarrage manuel

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Démarrer le serveur (développement avec rechargement)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Ou en production
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Installation en service systemd (démarrage automatique)

```bash
cd boot_service
chmod +x install_service.sh
sudo ./install_service.sh
```

Le script détectera automatiquement :
- Votre utilisateur
- Le répertoire du projet
- L'environnement virtuel

### Accès à l'interface

1. Ouvrez un navigateur web
2. Accédez à `http://<IP-du-Pi>:8000` ou `http://localhost:8000`
3. Identifiez-vous avec les identifiants par défaut :
   - **Nom d'utilisateur** : `admin`
   - **Mot de passe** : `admin`

## 📱 Interface Web

L'interface web comprend 4 onglets :

### 1. Système
- Informations sur le dispositif
- Modification du mot de passe

### 2. Wi-Fi
- Configuration du point d'accès (si activé)

### 3. Réseau
- Liste des appareils connectés

### 4. Bluetooth (Cœur du système)
- **Scan** : Rechercher des appareils Bluetooth audio
- **Connecter** : Appairer et connecter un appareil
- **Traduction** : Démarrer/arrêter la traduction
- **Vidéo** : Stream vidéo en temps réel

## 🔧 Fonctionnement de la traduction

1. **Capture vidéo** : La caméra capture les images à ~30 FPS
2. **Extraction landmarks** : MediaPipe Holistic extrait les points clés (mains, visage, pose)
3. **Rééchantillonnage temporel** : Les séquences sont normalisées en durée
4. **Classification** : TFLite identifie le signe
5. **Validation** : Le signe est validé après stabilité (5+ frames)
6. **Traduction** : LLM convertit les glosses en phrase française
7. **Synthèse vocale** : Piper TTS génère l'audio
8. **Diffusion** : L'audio est routé vers l'appareil Bluetooth

## 🔐 Sécurité

- Authentification par token JWT
- Cookies HTTP-only sécurisés
- Mot de passe haché avec bcrypt
- Expiration des tokens (60 minutes)

## 🐛 Dépannage

### Caméra non détectée

```bash
# Vérifier les périphériques vidéo
ls -l /dev/video*

# Tester avec OpenCV
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Bluetooth ne fonctionne pas

```bash
# Vérifier le service Bluetooth
sudo systemctl status bluetooth
sudo systemctl restart bluetooth

# Vérifier les permissions
groups $USER  # Doit contenir 'bluetooth'
```

### Audio ne route pas vers Bluetooth

```bash
# Sur Raspberry Pi (PipeWire)
pactl list sinks short
pw-cli list-objects | grep node

# Sur PC Linux (PulseAudio)
pactl list sinks short
pactl load-module module-bluetooth-discover
```

### Service systemd ne démarre pas

```bash
# Voir les logs
sudo systemctl status sign2speak
journalctl -u sign2speak -f
```

## 📁 Structure du Projet

```
Sign2Speak/
├── src/                          # Code source Python
│   ├── main.py                   # Application FastAPI principale
│   ├── models.py                 # Modèles de données Pydantic
│   └── utils/                    # Utilitaires
│       ├── bluetooth_manager.py  # Gestionnaire Bluetooth
│       ├── translation_engine.py # Moteur de traduction
│       ├── security.py           # Authentification JWT
│       └── config.py             # Configuration
├── web/                          # Frontend
│   ├── static/                   # CSS, JS
│   └── templates/                # Templates HTML
├── moteur_trad_pi/               # Modèles ML
│   ├── Model/                    # Modèle TFLite
│   ├── piper/                    # Modèles TTS
│   └── sign_to_prediction_index_map.json
├── boot_service/                 # Service systemd
│   ├── sign2speak.service        # Template service
│   └── install_service.sh        # Script d'installation
├── requirements.txt              # Dépendances Python
└── README.md                     # Ce fichier
```

## 🔄 Compatibilité

| Plateforme | Statut | Notes |
|------------|--------|-------|
| Raspberry Pi 5 | ✅ Pleinement supporté | Optimisé (ai_edge_litert, V4L2, PipeWire) |
| PC Linux | ✅ Supporté | Fallback tflite_runtime, PulseAudio |
| Windows | ❌ Non supporté | Bluetooth/Audio non compatibles |
| macOS | ❌ Non supporté | Bluetooth/Audio non compatibles |

## 📊 Mesures de performance

Le système affiche les latences suivantes dans le terminal :
- **Latence Détection Signe Moyenne** : Temps de reconnaissance des signes
- **Latence LLM** : Temps de traduction glosses → français
- **Latence Audio** : Temps de génération audio
- **Latence Totale** : Temps total de traduction + génération
- **Temps Routage Audio Complet** : Temps de génération + lecture

## 🎬 Démo

Vidéo de démonstration du système Sign2Speak :

<video src="demo.mp4" controls width="640"></video>

## 🤝 Contributing

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

[À définir]

## 👨‍💻 Auteurs

- [Zoulix] - Développement principal