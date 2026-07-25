# BInformed pour Home Assistant

[![hacs][hacs-badge]][hacs]
[![Validate][validate-badge]][validate]

Intégration Home Assistant qui envoie vos notifications d'alerte via l'API
[BInformed](https://binformed.gericos.com/api-docs). Elle joue exactement le
même rôle que l'intégration Prowl, mais s'appuie sur votre propre service.

## Fonctionnalités

- Configuration entièrement par l'interface (config flow), aucune ligne de YAML
  n'est nécessaire.
- Une entité `notify` par compte, pilotable avec l'action
  `notify.send_message` (message + titre).
- Un service historique `notify.<nom>` pour les configurations YAML et les
  automatisations existantes, avec en plus le champ `url`.
- Messages d'erreur traduits (français / anglais) pour les cas courants :
  clé révoquée, compte non vérifié, quota dépassé, API injoignable.

## Prérequis

- Home Assistant **2025.3** ou plus récent.
- Un compte BInformed **vérifié** (l'API renvoie `403` tant que l'adresse
  e-mail n'est pas confirmée) avec au moins un appareil enregistré.
- Une clé API. Elle s'obtient uniquement via `POST /v1/keys/rotate` (qui exige
  un JWT, donc un login préalable), commence par `gn_` et n'est **affichée
  qu'une seule fois**. Générer une nouvelle clé invalide immédiatement la
  précédente.

> **Note sur la validation de la clé.** `POST /v1/notify` est le seul endpoint
> de l'API BInformed qui accepte l'en-tête `X-API-Key` ; tous les endpoints de
> gestion (`/v1/me`, `/v1/devices`, `/v1/keys/rotate`…) exigent un JWT Bearer.
> L'intégration vérifie donc la clé en envoyant à `/v1/notify` un corps
> volontairement vide : l'API authentifie la requête puis la rejette pour
> cause de `message` manquant. Un rejet de payload prouve que la clé est
> acceptée, et **aucune notification n'est envoyée à vos appareils**.

## Installation

### Via HACS (recommandé)

1. Dans HACS, ouvrez le menu ⋮ → **Custom repositories**.
2. Ajoutez `https://github.com/chriphil/homeassistant-binformed` avec la
   catégorie **Integration**.
3. Installez « BInformed », puis redémarrez Home Assistant.

[![Ouvrir dans HACS][hacs-repo-badge]][hacs-repo]

### Manuellement

Copiez le dossier `custom_components/binformed` dans le répertoire
`config/custom_components/` de votre installation, puis redémarrez Home
Assistant.

## Configuration

**Paramètres → Appareils et services → Ajouter une intégration → BInformed**,
puis collez votre clé API.

L'URL de base de l'API (`https://api-binformed.gericos.com` par défaut) n'est
proposée que si les *options avancées* sont activées sur votre profil
utilisateur ; ne la modifiez que si vous hébergez votre propre instance.

## Utilisation

### Entité notify (recommandé)

```yaml
actions:
  - action: notify.send_message
    target:
      entity_id: notify.mon_compte_binformed
    data:
      title: Alerte chaudière
      message: La température est descendue sous 5 °C.
```

### Service historique

Déclaré via `configuration.yaml` :

```yaml
notify:
  - platform: binformed
    name: binformed
    api_key: !secret binformed_api_key
```

Il accepte en plus un champ `url` (HTTPS obligatoire) :

```yaml
actions:
  - action: notify.binformed
    data:
      title: Fuite détectée
      message: Capteur de la buanderie déclenché.
      data:
        url: https://mon-hass.example.com/lovelace/eau
```

## Limites de l'API

| Champ     | Contrainte                    |
| --------- | ----------------------------- |
| `message` | obligatoire, 2000 caractères max |
| `title`   | 200 caractères max            |
| `url`     | doit être en HTTPS            |

Ces limites sont vérifiées côté intégration avant l'appel réseau, ce qui évite
de consommer inutilement votre quota.

## Dépannage

| Symptôme | Cause probable |
| --- | --- |
| `La clé API BInformed est invalide ou a été renouvelée` | La clé a été régénérée via `/v1/keys/rotate`. Supprimez puis rajoutez l'intégration avec la nouvelle clé. |
| `L'adresse e-mail de ce compte n'est pas encore vérifiée` | Confirmez l'e-mail (`POST /v1/auth/resend-verification`). |
| `La limite de débit de l'API a été atteinte` | Trop d'appels (HTTP 429). Espacez les notifications. |
| La notification renvoie `pushed: 0` | Aucun appareil enregistré sur le compte. Vérifiez avec `GET /v1/devices` (JWT requis, pas la clé API). |

Pour obtenir des journaux détaillés :

```yaml
logger:
  default: warning
  logs:
    custom_components.binformed: debug
```

## Logo et icône

Les images de marque sont embarquées dans `custom_components/binformed/brand/`
et reprennent l'icône de l'application iOS BInformed :

| Fichier | Dimensions | Usage |
| --- | --- | --- |
| `icon.png` / `icon@2x.png` | 256² / 512² | Liste des intégrations, carte de l'appareil |
| `logo.png` / `logo@2x.png` | 1028×256 / 2057×512 | Page de l'intégration, thème clair |
| `dark_logo.png` / `dark_logo@2x.png` | idem | Thème sombre |

Home Assistant **2026.3** ou plus récent les charge automatiquement, sans
configuration. Sur les versions antérieures elles sont ignorées et l'interface
retombe sur le CDN [brands.home-assistant.io](https://brands.home-assistant.io) ;
pour les couvrir, soumettez les mêmes fichiers au dépôt
[home-assistant/brands](https://github.com/home-assistant/brands) dans
`custom_integrations/binformed/`.

Le logotype existe en deux teintes parce que le bleu clair de la marque
(`#2DABFA`) n'offre qu'un contraste de 2,4:1 sur fond blanc : la version claire
utilise `#0B4FA8` (7,5:1), la version sombre garde `#2DABFA`.

## Développement

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/pytest --cov=custom_components.binformed --cov-report=term-missing
```

## Licence

[MIT](LICENSE)

[hacs]: https://github.com/hacs/integration
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-repo]: https://my.home-assistant.io/redirect/hacs_repository/?owner=chriphil&repository=homeassistant-binformed&category=integration
[hacs-repo-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[validate]: https://github.com/chriphil/homeassistant-binformed/actions/workflows/validate.yaml
[validate-badge]: https://github.com/chriphil/homeassistant-binformed/actions/workflows/validate.yaml/badge.svg
