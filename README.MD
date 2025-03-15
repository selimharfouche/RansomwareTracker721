# RansomwareTracker721

![RansomwareTracker](https://img.shields.io/badge/RansomwareTracker-1.0-blue)

Un système de suivi complet pour surveiller les entités divulguées par différents groupes de ransomware. Ce projet automatise la collecte de données via Tor, standardise les formats de date, et enrichit les informations par IA.

## Table des matières

- [Introduction](#introduction)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [Fonctionnalités](#fonctionnalités)
- [GitHub Actions](#github-actions)
- [Notifications Telegram](#notifications-telegram)
- [Site Web](#site-web)
- [Contribuer](#contribuer)

## Introduction

RansomwareTracker721 est un système avancé qui surveille automatiquement les sites de fuite de ransomware, identifie les nouvelles victimes, et standardise les données dans un format cohérent. Le système utilise Tor pour accéder aux sites .onion, extrait les informations des entités et notifie les utilisateurs via Telegram des nouvelles découvertes.

## Installation

### Cloner le dépôt

```bash
git clone https://github.com/selimharfouche/RansomwareTracker721
cd RansomwareTracker721
```

### Créer et activer un environnement virtuel

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows
venv\Scripts\activate
# Sur macOS et Linux
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### Prérequis

- Python 3.9+
- Tor 
- Firefox et Geckodriver

## Configuration

### Variables d'environnement (Facultatif)

Créez un fichier `.env` à la racine du projet avec les variables suivantes (facultatif) :

```
# Configuration Telegram (facultatif)
TELEGRAM_BOT_TOKEN=votre_token_bot
TELEGRAM_CHANNEL_ID=votre_id_canal

# Configuration OpenAI (pour l'enrichissement des données, facultatif)
OPENAI_API_KEY=votre_clé_api_openai
```

### Configuration des sites

Le système est conçu pour être facilement extensible. Vous pouvez ajouter de nouveaux sites ransomware en créant simplement un fichier JSON dans le répertoire `config/sites/`.

Exemple de structure pour un site :

```json
{
  "site_key": "lockbit",
  "site_name": "LockBit",
  "json_file": "lockbit_entities.json",
  "mirrors": [
    "lockbit3753ekiocyo5epmpy6klmejchjtzddoekjlnt6mu3qh4de2id.onion",
    "lockbit3g3ohd3katajf6zaehxz4h4cnhmz5t735zpltywhwpc6oy3id.onion"
  ],
  "site_verification": {
    "type": "text",
    "value": "LockBit"
  },
  "parsing": {
    "entity_selector": "a.post-block",
    "fields": [
      {
        "name": "id",
        "type": "attribute",
        "selector": "self",
        "attribute": "href",
        "regex": "^\\/?(.+)$",
        "regex_group": 1
      },
      ...
    ]
  }
}
```

## Utilisation

### Scraping des sites de ransomware

Toutes les options pour exécuter main.py :

```bash
# Scraping de tous les sites configurés
python tracker/main.py

# Scraping de sites spécifiques
python tracker/main.py --sites lockbit bashe

# Désactiver les notifications Telegram
python tracker/main.py --no-telegram

# Mode headless (sans interface graphique)
python tracker/main.py --headless

# Sauter l'étape de traitement des entités
python tracker/main.py --no-process

# Configurer les temps d'attente
python tracker/main.py --browser-config timing.min_wait_time=5 timing.max_wait_time=10

# Configurer les options de snapshot HTML
python tracker/main.py --scraping-config snapshots.save_html=true

# Combiner plusieurs options
python tracker/main.py --sites lockbit --no-telegram --headless --browser-config timing.min_wait_time=2
```

### Traitement et standardisation des entités

```bash
# Traitement des nouvelles entités découvertes
python tracker/processing/process_entities.py
```

### Traitement IA

```bash
# Extraction des domaines pour enrichissement
python tracker/processing/run_ai_processing.py
```

## Structure du projet

RansomwareTracker721 est un monorepo contenant tous les composants nécessaires :

```
project-root/
├── tracker/                    # Code Python principal
│   ├── main.py                 # Script principal
│   ├── browser/                # Gestion du navigateur Tor
│   ├── scraper/                # Extraction des données
│   ├── processing/             # Traitement des données
│   ├── telegram_bot/           # Bot Telegram
│   └── AI/                     # Scripts d'enrichissement par IA
├── config/                     # Fichiers de configuration
│   ├── sites/                  # Configuration des sites (JSON)
│   └── code/                   # Configuration du comportement
├── data/                       # Stockage des données
│   ├── output/                 # Fichiers JSON principaux
│   │   └── per_group/          # Données par groupe
│   ├── processed/              # Données standardisées
│   ├── snapshots/              # Captures HTML
│   └── AI/                     # Données enrichies par IA
├── website/                    # Code source du site web
└── .github/
    └── workflows/              # Configuration GitHub Actions
```

## Fonctionnalités

- **Extensible** : Ajoutez de nouveaux sites en créant simplement un fichier JSON
- **Configuration flexible** : Contrôlez le comportement via des paramètres JSON et des variables d'environnement
- **Standardisation des dates** : Toutes les dates sont converties en UTC
- **Détection des victimes** : Identification des nouvelles victimes apparaissant sur les sites
- **Enrichissement par IA** : Données améliorées via l'API OpenAI
- **Notifications en temps réel** : Alertes via Telegram
- **Rotation des snapshots** : Conservation des N derniers snapshots HTML

## GitHub Actions

Le projet utilise GitHub Actions pour automatiser les processus de scraping et d'analyse :

- **Scraping automatique** : Exécution toutes les 6 heures des scraping des sites ransomware
- **Traitement des entités** : Standardisation automatique des données
- **Enrichissement IA** : Exécution toutes les 48 heures du traitement IA
- **Notifications** : Envoi automatique des résultats dans le canal Telegram
- **Persistance des données** : Mise à jour automatique des fichiers JSON dans le dépôt

Les workflows sont configurés dans le répertoire `.github/workflows/` et fonctionnent de manière autonome.

## Notifications Telegram

Le système envoie des notifications pour :

1. Les nouvelles victimes découvertes
2. Les résumés de scan complets
3. Les résultats de traitement IA

Rejoignez notre canal Telegram pour recevoir ces notifications :
[https://t.me/+OxLHO7fclkwxOTQ0](https://t.me/+OxLHO7fclkwxOTQ0)

## Site Web

Une interface web est disponible dans le répertoire `website/` à la racine du projet.

## Contribuer

Les contributions sont les bienvenues ! Voici comment vous pouvez aider :

1. Ajouter des configurations pour de nouveaux sites de ransomware
2. Améliorer les extracteurs de données existants
3. Développer de nouvelles fonctionnalités d'analyse
4. Signaler des bugs ou proposer des améliorations

---

**Note** : Ce projet est développé à des fins de recherche et d'information uniquement