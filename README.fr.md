# BInformed pour Home Assistant

[![hacs][hacs-badge]][hacs]
[![Validate][validate-badge]][validate]

[English](README.md) · **Français**

Envoyez vos alertes Home Assistant en notifications push via
[BInformed](https://binformed.gericos.com). Même rôle que l'intégration Prowl,
en s'appuyant sur le service BInformed.

## Fonctionnalités

- Configuration entièrement par l'interface — aucune ligne de YAML n'est
  nécessaire.
- Une entité `notify` sélectionnable directement dans l'éditeur
  d'automatisations.
- Messages d'erreur traduits (français / anglais) pour les cas courants : clé
  révoquée, compte non vérifié, quota dépassé, API injoignable.
- Icône et logo intégrés, en versions claire et sombre.

## Prérequis

- Home Assistant **2025.3** ou plus récent.
- Un compte BInformed **vérifié** — créez-le sur
  **[binformed.gericos.com](https://binformed.gericos.com)**. Confirmez bien
  l'e-mail reçu : tant que ce n'est pas fait, l'API refuse tout envoi.
- Au moins un appareil enregistré sur le compte, sans quoi les notifications
  sont acceptées mais ne sont délivrées à personne.
- Votre **clé API**. Elle s'affiche dans votre compte sur le site BInformed
  dès l'inscription, et commence par `gn_`.

## Installation

### Via HACS

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

Rendez-vous dans **Paramètres → Appareils et services → Ajouter une
intégration**, cherchez **BInformed**, et collez votre clé API.

C'est tout. L'intégration crée une entité de notification, prête à l'emploi.

## Utilisation

### Depuis l'éditeur d'automatisations

C'est ce dont la plupart des utilisateurs ont besoin — aucun fichier de
configuration n'entre en jeu.

1. **Paramètres → Automatisations et scènes → Créer une automatisation**.
2. Construisez votre déclencheur comme d'habitude (un capteur, une heure, un
   changement d'état…).
3. Sous **Alors faire**, cliquez sur **Ajouter une action** et cherchez
   **Envoyer un message de notification**.
4. Choisissez l'entité **BInformed** comme cible.
5. Renseignez le **Message**, et éventuellement le **Titre**.

Cette même entité est disponible partout où Home Assistant permet d'envoyer
une notification : scripts, scènes, section « Notifications » d'un tableau de
bord, ou test manuel depuis **Outils de développement → Actions**.

### Utilisation avancée

<details>
<summary>Appeler l'entité depuis un YAML</summary>

```yaml
actions:
  - action: notify.send_message
    target:
      entity_id: notify.binformed
    data:
      title: Alerte chaudière
      message: La température est descendue sous 5 °C.
```

</details>

<details>
<summary>Service historique <code>notify.&lt;nom&gt;</code></summary>

Conservé pour les automatisations existantes, et seul moyen d'attacher une URL
cliquable à une notification. Déclaré dans `configuration.yaml` :

```yaml
notify:
  - platform: binformed
    name: binformed
    api_key: !secret binformed_api_key
```

Il accepte un champ `url` supplémentaire, qui doit être en HTTPS :

```yaml
actions:
  - action: notify.binformed
    data:
      title: Fuite détectée
      message: Capteur de la buanderie déclenché.
      data:
        url: https://mon-hass.example.com/lovelace/eau
```

Stockez la clé dans `secrets.yaml`, jamais dans `configuration.yaml` :

```yaml
binformed_api_key: gn_votre_cle_ici
```

</details>

<details>
<summary>Limites des champs</summary>

| Champ | Contrainte |
| --- | --- |
| `message` | obligatoire, 2000 caractères max |
| `title` | 200 caractères max |
| `url` | doit être en HTTPS |

Ces limites sont vérifiées par l'intégration avant l'appel réseau : une
notification mal formée ne consomme donc jamais votre quota.

</details>

<details>
<summary>Comment la clé API est validée</summary>

`POST /v1/notify` est le seul endpoint BInformed qui accepte l'en-tête
`X-API-Key` ; tous les endpoints de gestion exigent un JWT Bearer.
L'intégration valide donc une clé en envoyant à `/v1/notify` un corps
volontairement vide : l'API authentifie la requête, puis la rejette pour cause
de `message` manquant. Un rejet de payload prouve que la clé est acceptée, et
**aucune notification n'atteint vos appareils**.

</details>

## Dépannage

| Symptôme | Cause probable |
| --- | --- |
| `La clé API BInformed est invalide ou a été renouvelée` | La clé a été régénérée. Supprimez puis rajoutez l'intégration avec la nouvelle clé. |
| `L'adresse e-mail de ce compte n'est pas encore vérifiée` | Confirmez l'e-mail d'inscription. |
| `La limite de débit de l'API BInformed a été atteinte` | Trop d'appels (HTTP 429). Espacez les notifications. |
| La notification renvoie `pushed: 0` | Aucun appareil enregistré sur le compte. |

Pour obtenir des journaux détaillés :

```yaml
logger:
  default: warning
  logs:
    custom_components.binformed: debug
```

## Images de marque

Les images sont embarquées dans `custom_components/binformed/brand/` et
reprennent l'icône de l'application iOS BInformed :

| Fichier | Dimensions | Usage |
| --- | --- | --- |
| `icon.png` / `icon@2x.png` | 256² / 512² | Liste des intégrations, carte de l'appareil |
| `logo.png` / `logo@2x.png` | 1028×256 / 2057×512 | Page de l'intégration, thème clair |
| `dark_logo.png` / `dark_logo@2x.png` | idem | Thème sombre |

Home Assistant **2026.3** ou plus récent les charge automatiquement, sans
configuration. Les versions antérieures les ignorent et retombent sur le CDN
[brands.home-assistant.io](https://brands.home-assistant.io).

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
[validate-badge]: https://github.com/chriphil/homeassistant-binformed/actions/workflows/validate.yaml/badge.svg?branch=main&event=push
