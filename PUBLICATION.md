# Publier BInformed dans le magasin par défaut de HACS

Objectif : que n'importe quel utilisateur trouve l'intégration en cherchant
« BInformed » dans HACS, sans avoir à ajouter un dépôt personnalisé.

État actuel : le contenu du dépôt est prêt et validé localement (manifest,
`hacs.json`, images de marque aux dimensions exactes, zip de release conforme,
34 tests). Il reste six étapes, toutes côté GitHub.

---

## 1. Créer le dépôt

Le nom doit être **`homeassistant-binformed`** : c'est celui déjà inscrit dans
`manifest.json` (`documentation`, `issue_tracker`) et dans les liens du README.
Si vous en choisissez un autre, corrigez ces trois endroits avant de pousser.

| Réglage | Valeur |
| --- | --- |
| Visibilité | **Public** (obligatoire) |
| Issues | **Activées** (obligatoire) |
| Archivé | Non |

**Description** (obligatoire — champ « About », en haut à droite du dépôt) :

```
Intégration Home Assistant pour les notifications push BInformed : entité notify pilotable par notify.send_message, configuration par l'interface, aucune dépendance externe.
```

**Topics** (obligatoire — même panneau « About », roue dentée) :

```
home-assistant  homeassistant  hacs  hacs-integration  custom-integration
notify  notifications  push-notifications  binformed
```

## 2. Pousser le code

Depuis `Documents\work\BInformed - HomeAssistant` :

```bash
git init
git add .
git commit -m "feat: initial BInformed notify integration for Home Assistant"
git branch -M main
git remote add origin https://github.com/jclaude95/homeassistant-binformed.git
git push -u origin main
```

Vérifiez avant de pousser que `.github/workflows/` contient bien
`validate.yaml` et `release.yaml`, et que le dossier `.venv/` n'est pas suivi
(le `.gitignore` s'en charge).

## 3. Vérifier que la CI passe

L'onglet **Actions** doit afficher trois jobs au vert :

- **Hassfest** — validation officielle du `manifest.json` par Home Assistant.
- **HACS** — validation officielle du dépôt par HACS. C'est celui qui compte
  pour la candidature : il doit passer **sans aucune erreur**.
- **Tests** — ruff + pytest.

Si HACS échoue, le message d'erreur nomme précisément la règle non respectée.

## 4. Publier une release

HACS exige une **release**, pas un simple tag.

```bash
git tag v0.1.0
git push origin v0.1.0
```

Puis sur GitHub : **Releases → Draft a new release**, choisir le tag `v0.1.0`,
titrer `v0.1.0`, décrire brièvement, et **Publish release**.

Le workflow `release.yaml` se déclenche alors automatiquement : il réécrit la
version du manifest d'après le tag, construit `binformed.zip` et l'attache à la
release. Vérifiez que le fichier apparaît bien dans les *assets* — `hacs.json`
déclare `zip_release`, donc HACS installera ce zip et refusera la release s'il
est absent.

## 5. Candidater au magasin par défaut

Sur [github.com/hacs/default](https://github.com/hacs/default) :

1. Forkez le dépôt, puis créez une branche **depuis `master`** — n'ouvrez pas
   la PR depuis `master` lui-même, elle serait refusée.
2. Éditez le fichier `integration` (un tableau JSON de `"propriétaire/dépôt"`).
3. Insérez `"jclaude95/homeassistant-binformed"` **à sa place alphabétique**,
   sans casser la virgule de la ligne précédente.
4. Ouvrez la PR en remplissant intégralement le gabarit proposé.

Deux règles à respecter : seul le propriétaire ou un contributeur principal du
dépôt peut candidater, et la PR doit rester modifiable par les mainteneurs
(elle ne doit donc pas venir d'un compte d'organisation).

La CI de `hacs/default` rejoue la validation HACS, la validation du manifest et
le lint JSON. Si l'étape 3 est verte, il n'y a en principe pas de surprise.

## 6. Après l'acceptation

L'intégration devient installable par tous depuis HACS. Pour publier une mise à
jour : commit, `git tag vX.Y.Z`, push du tag, puis nouvelle release. HACS
proposera automatiquement la montée de version aux utilisateurs.

---

## Ce qui n'est pas nécessaire pour cette voie

- **Pas de PR sur `home-assistant/brands`.** L'exigence d'icône est déjà
  satisfaite par `custom_components/binformed/brand/icon.png`. La PR sur
  `brands` ne deviendrait utile que pour couvrir les installations en Home
  Assistant antérieur à 2026.3, ou pour une candidature au Core.
- **Pas de bibliothèque PyPI, pas de `quality_scale.yaml`.** Ce sont des
  exigences du dépôt `home-assistant/core`, pas de HACS.

## En cas de refus de la CI HACS

Les causes les plus fréquentes, dans l'ordre :

| Erreur | Cause |
| --- | --- |
| `Repository has no topics` | Topics non renseignés (étape 1) |
| `Repository has no description` | Champ « About » vide (étape 1) |
| `No releases found` | Un tag a été poussé, mais aucune release publiée (étape 4) |
| `Missing zip file in release` | Le workflow `release.yaml` n'a pas tourné ou a échoué |
| `Repository has no icon` | Le dossier `brand/` n'a pas été poussé |
