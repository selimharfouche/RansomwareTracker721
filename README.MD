# Ransomware Tracker System

[Pour la version française, veuillez cliquer ici](#ransomware-tracker-system-fr)

## Overview

This project is an automated ransomware leak site monitoring system that tracks victim organizations published by ransomware groups. It uses Tor to safely access darknet sites, extracts information about compromised organizations, and provides notifications when new victims are identified.

## GitHub Workflows

The system uses two primary GitHub Actions workflows:

1. **Scrape Workflow (`scrape.yml`)**: 
   - Runs every 5 minutes automatically (can also be run manually)
   - Configures a Tor proxy and Firefox for anonymous browsing
   - Scrapes multiple ransomware leak sites based on JSON configurations
   - Identifies and saves new victim entities
   - Triggers the AI processing workflow when new entities are found

2. **AI Processing Workflow (`ai_processing.yml`)**:
   - Triggered by the scrape workflow when new entities are found
   - Extracts domain information from victim organizations
   - Enriches domain data using OpenAI API
   - Adds details like organization name, industry, country, size, etc.
   - Sends Telegram notifications with the enriched information

## Architecture

The system is built with a modular architecture:

- **Browser Module**: Handles Tor connectivity and secure browsing
- **Scraper Module**: Contains the base parser and generic parser for extracting entities
- **Processing Module**: Standardizes, archives, and processes entity data
- **AI Module**: Performs domain enrichment using OpenAI
- **Telegram Bot**: Provides real-time notifications for new entities
- **Utils**: Contains shared utility functions for logging, file operations, and Tor management

All site configurations are stored in JSON files, allowing new ransomware sites to be added without code changes.

## Running the Application

### Prerequisites

- Python 3.9+
- Tor service installed and running
- Firefox browser
- Required Python packages (installable via `pip install -r requirements.txt`)

### Running main.py

The main script offers several options for customizing its behavior:

#### Basic Usage

```bash
python tracker/main.py
```

This will run the scraper against all configured ransomware sites, process the entities, and send notifications if enabled.

#### Target Specific Sites

```bash
python tracker/main.py --sites lockbit bashe
```

This runs the scraper only against the specified sites (in this example, LockBit and Bashe).

#### Headless Mode

```bash
python tracker/main.py --headless
```

Runs the browser in headless mode (without a visible window), useful for servers or GitHub Actions.

#### Disable Entity Processing

```bash
python tracker/main.py --no-process
```

Only scrapes the sites without processing or archiving entities.

#### Disable Telegram Notifications

```bash
python tracker/main.py --no-telegram
```

Runs without sending Telegram notifications.

#### Constant Monitoring Mode

```bash
python tracker/main.py --constant-monitoring
```

Only sends notifications and triggers AI processing when new entities are found.

#### Browser Configuration Overrides

```bash
python tracker/main.py --browser-config timing.min_wait_time=15
```

Overrides specific browser configuration values from the command line.

### Configuration

The system uses JSON configuration files located in the `config/` directory:

- **Code Configs**: Technical configurations for browser, proxy, etc.
- **Site Configs**: Definitions for each ransomware site, including selectors

To add support for a new ransomware leak site, create a new JSON configuration file in `config/sites/`.

### Troubleshooting

- **Tor Connection Issues**: Make sure Tor is running on port 9050
- **Missing Telegram Notifications**: Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID environment variables
- **OpenAI API Issues**: Check that the OPENAI_API_KEY environment variable is set correctly

---

<a name="ransomware-tracker-system-fr"></a>
# Système de Suivi des Ransomwares

## Aperçu

Ce projet est un système automatisé de surveillance des sites de fuite de ransomware qui suit les organisations victimes publiées par les groupes de ransomware. Il utilise Tor pour accéder en toute sécurité aux sites du darknet, extrait des informations sur les organisations compromises et fournit des notifications lorsque de nouvelles victimes sont identifiées.

## Workflows GitHub

Le système utilise deux workflows GitHub Actions principaux :

1. **Workflow de Scraping (`scrape.yml`)** :
   - S'exécute automatiquement toutes les 5 minutes (peut également être exécuté manuellement)
   - Configure un proxy Tor et Firefox pour une navigation anonyme
   - Extrait les données de plusieurs sites de fuite de ransomware basés sur des configurations JSON
   - Identifie et sauvegarde les nouvelles entités victimes
   - Déclenche le workflow de traitement AI lorsque de nouvelles entités sont trouvées

2. **Workflow de Traitement AI (`ai_processing.yml`)** :
   - Déclenché par le workflow de scraping lorsque de nouvelles entités sont trouvées
   - Extrait les informations de domaine des organisations victimes
   - Enrichit les données de domaine à l'aide de l'API OpenAI
   - Ajoute des détails comme le nom de l'organisation, l'industrie, le pays, la taille, etc.
   - Envoie des notifications Telegram avec les informations enrichies

## Architecture

Le système est construit avec une architecture modulaire :

- **Module Navigateur** : Gère la connectivité Tor et la navigation sécurisée
- **Module Scraper** : Contient le parseur de base et le parseur générique pour extraire les entités
- **Module de Traitement** : Standardise, archive et traite les données d'entité
- **Module AI** : Effectue l'enrichissement de domaine à l'aide d'OpenAI
- **Bot Telegram** : Fournit des notifications en temps réel pour les nouvelles entités
- **Utils** : Contient des fonctions utilitaires partagées pour la journalisation, les opérations de fichiers et la gestion de Tor

Toutes les configurations de site sont stockées dans des fichiers JSON, permettant d'ajouter de nouveaux sites de ransomware sans modifications de code.

## Exécution de l'Application

### Prérequis

- Python 3.9+
- Service Tor installé et en cours d'exécution
- Navigateur Firefox
- Packages Python requis (installables via `pip install -r requirements.txt`)

### Exécution de main.py

Le script principal offre plusieurs options pour personnaliser son comportement :

#### Utilisation de Base

```bash
python tracker/main.py
```

Cela exécutera le scraper sur tous les sites de ransomware configurés, traitera les entités et enverra des notifications si activées.

#### Cibler des Sites Spécifiques

```bash
python tracker/main.py --sites lockbit bashe
```

Cela exécute le scraper uniquement sur les sites spécifiés (dans cet exemple, LockBit et Bashe).

#### Mode Headless

```bash
python tracker/main.py --headless
```

Exécute le navigateur en mode headless (sans fenêtre visible), utile pour les serveurs ou GitHub Actions.

#### Désactiver le Traitement des Entités

```bash
python tracker/main.py --no-process
```

Scrappe uniquement les sites sans traiter ni archiver les entités.

#### Désactiver les Notifications Telegram

```bash
python tracker/main.py --no-telegram
```

Exécute sans envoyer de notifications Telegram.

#### Mode de Surveillance Constante

```bash
python tracker/main.py --constant-monitoring
```

Envoie des notifications et déclenche le traitement AI uniquement lorsque de nouvelles entités sont trouvées.

#### Remplacements de Configuration du Navigateur

```bash
python tracker/main.py --browser-config timing.min_wait_time=15
```

Remplace des valeurs spécifiques de configuration du navigateur depuis la ligne de commande.

### Configuration

Le système utilise des fichiers de configuration JSON situés dans le répertoire `config/` :

- **Configs de Code** : Configurations techniques pour le navigateur, le proxy, etc.
- **Configs de Site** : Définitions pour chaque site de ransomware, y compris les sélecteurs

Pour ajouter le support d'un nouveau site de fuite de ransomware, créez un nouveau fichier de configuration JSON dans `config/sites/`.

### Dépannage

- **Problèmes de Connexion Tor** : Assurez-vous que Tor est en cours d'exécution sur le port 9050
- **Notifications Telegram Manquantes** : Vérifiez les variables d'environnement TELEGRAM_BOT_TOKEN et TELEGRAM_CHANNEL_ID
- **Problèmes d'API OpenAI** : Vérifiez que la variable d'environnement OPENAI_API_KEY est correctement définie