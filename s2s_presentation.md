# Conception d'un dispositif embarqué autonome de traduction de la langue des signes en audio avec diffusion Bluetooth

## Objectifs spécifiques

- **Concevoir un système embarqué** capable de capturer des gestes en langue des signes via une caméra.
- **Traduire ces gestes** en phrases audio compréhensibles.
- **Diffuser ces traductions** en temps réel vers tout appareil audio Bluetooth.
- **Proposer une interface web légère** pour gérer l'appareillage Bluetooth et les configurations du dispositif.

---

## App Web S2S

### Contexte et Objectif

Cette application web sert d'interface homme machine (IHM) avec le dispositif. Elle est générée localement via le Raspberry Pi accessible en Wi-Fi (point d'accès du Raspberry Pi) pour gérer l'appareillage Bluetooth et les configurations du dispositif.

En gros l'app est comparable au application de gestion de routeur ou pocket wifi qu'on peut visualiser en entrant dans le navigateur l'adresse ip de la passerelle. Elle sera donc accessible via une adresse ip unique également.

### L'application

L'application web que je conçois est une interface homme-machine (IHM) locale, conçue pour gérer et superviser le dispositif embarqué de traduction. Cette application, accessible via un point d'accès Wi-Fi, est comparable à une interface de gestion de routeur et se distingue par son caractère.

---

## Page de connexion 🔒

L'application s'ouvre sur une page de connexion sécurisée, servant de point d'entrée unique.

- **Objectif** : Authentifier les utilisateurs et gérer les rôles (Admin, Responsable pédagogique, Technicien).

### Fonctionnalités :
- Authentification basée sur le nom d'utilisateur et le mot de passe, avec la possibilité d'un "se souvenir de moi" grâce à une expiration plus longue du jeton JWT.
- En cas d'échec, un message d'erreur s'affiche.
- Une fois authentifié, l'utilisateur est redirigé de manière sécurisée vers le tableau de bord.

---

## Tableau de bord & Navigation 📊

Après la connexion, l'utilisateur accède à un tableau de bord offrant une vue d'ensemble du système. Ce tableau de bord est structuré en plusieurs onglets, facilitant la navigation vers les différentes fonctionnalités. Il se rafraîchit automatiquement en temps réel pour présenter des données à jour.

### 1. Onglet Système ⚙

Cet onglet permet de gérer les informations et la maintenance de base du dispositif.

- **Informations** : Affiche les données techniques du dispositif, telles que le nom de l'appareil, le matricule, l'adresse MAC, l'IMEI, ainsi que les versions matérielle et logicielle.
- **Changement du username et du mot de passe** : Permet aux utilisateurs de mettre à jour leur mot de passe et leur username via un formulaire dédié. (Ex: ancien password, nouveau password)

### 2. Onglet Paramètres Wi-Fi 📶

Cet onglet permet la configuration du point d'accès Wi-Fi du dispositif.

- **Modification des attributs** : Permet de modifier le SSID et le mot de passe du point d'accès.

### 3. Onglet Réseau 🌐

Il fournit des informations sur les appareils connectés au point d'accès.

- **Vue détaillée** : Affiche un tableau listant les appareils connectés, avec leur nom, adresse IP et adresse MAC.

### 4. Onglet Appareillage Bluetooth 🎧

C'est le cœur de l'interface, gérant l'interaction audio avec les périphériques externes.

- **Gestion des appareils** : Affiche la liste des appareils Bluetooth disponibles et la preuve de connexion d'un appareil appairé (nom, adresse MAC).
- **Contrôle de la traduction** : Comprend des boutons dédiés pour Démarrer et Arrêter le processus de traduction de la langue des signes.


uvicorn src.main:app --reload