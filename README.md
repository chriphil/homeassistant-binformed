# BInformed for Home Assistant

[![hacs][hacs-badge]][hacs]
[![Validate][validate-badge]][validate]

**English** · [Français](README.fr.md)

Send your Home Assistant alerts as push notifications through
[BInformed](https://binformed.gericos.com). Same role as the Prowl
integration, backed by the BInformed service.

## Features

- Set up entirely from the user interface — no YAML required.
- A `notify` entity you can pick directly in the automation editor.
- Translated error messages (English / French) for the common cases: revoked
  key, unverified account, rate limit, unreachable API.
- Brand icon and logo included, in light and dark variants.

## Requirements

- Home Assistant **2025.3** or newer.
- A **verified** BInformed account — create one at
  **[binformed.gericos.com](https://binformed.gericos.com)**. Confirm the
  email you receive: the API refuses to send anything until you do.
- At least one device registered on the account, otherwise notifications are
  accepted but delivered to nobody.
- Your **API key**. It is shown in your account on the BInformed website once
  you sign up, and starts with `gn_`.

## Installation

### Through HACS

1. In HACS, open the ⋮ menu → **Custom repositories**.
2. Add `https://github.com/chriphil/homeassistant-binformed` with the
   **Integration** category.
3. Install "BInformed", then restart Home Assistant.

[![Open in HACS][hacs-repo-badge]][hacs-repo]

### Manually

Copy the `custom_components/binformed` folder into the `config/custom_components/`
directory of your installation, then restart Home Assistant.

## Setup

Go to **Settings → Devices & services → Add integration**, search for
**BInformed**, and paste your API key.

That's it. The integration creates one notification entity, ready to use.

## Usage

### From the automation editor

This is all most people need — no configuration file involved.

1. **Settings → Automations & scenes → Create automation**.
2. Build your trigger as usual (a sensor, a time, a state change…).
3. Under **Then do**, click **Add action** and search for
   **Send a notification message**.
4. Pick the **BInformed** entity as the target.
5. Fill in **Message**, and optionally **Title**.

The same entity is available anywhere Home Assistant lets you send a
notification: scripts, scenes, the "Notifications" section of a dashboard, or
a manual test from **Developer tools → Actions**.

### Advanced usage

<details>
<summary>Calling the entity from YAML</summary>

```yaml
actions:
  - action: notify.send_message
    target:
      entity_id: notify.binformed
    data:
      title: Boiler alert
      message: Temperature dropped below 5 °C.
```

</details>

<details>
<summary>Legacy <code>notify.&lt;name&gt;</code> service</summary>

Kept for existing automations, and the only way to attach a clickable URL to a
notification. Declared in `configuration.yaml`:

```yaml
notify:
  - platform: binformed
    name: binformed
    api_key: !secret binformed_api_key
```

It accepts an extra `url` field, which must use HTTPS:

```yaml
actions:
  - action: notify.binformed
    data:
      title: Leak detected
      message: Laundry room sensor triggered.
      data:
        url: https://my-hass.example.com/lovelace/water
```

Store the key in `secrets.yaml`, never in `configuration.yaml`:

```yaml
binformed_api_key: gn_your_key_here
```

</details>

<details>
<summary>Field limits</summary>

| Field | Constraint |
| --- | --- |
| `message` | required, 2000 characters max |
| `title` | 200 characters max |
| `url` | must use HTTPS |

These are checked by the integration before the network call, so a malformed
notification never consumes your quota.

</details>

<details>
<summary>How the API key is validated</summary>

`POST /v1/notify` is the only BInformed endpoint that accepts the `X-API-Key`
header; every management endpoint requires a Bearer JWT. The integration
therefore validates a key by sending `/v1/notify` a deliberately empty body:
the API authenticates the request, then rejects it for the missing `message`.
A payload rejection proves the key was accepted, and **no notification reaches
your devices**.

</details>

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| `The BInformed API key is invalid or has been rotated` | The key was regenerated. Remove the integration and add it again with the new key. |
| `The email address of this account is not verified yet` | Confirm the signup email. |
| `The BInformed API rate limit has been exceeded` | Too many calls (HTTP 429). Space out notifications. |
| The notification returns `pushed: 0` | No device registered on the account. |

For detailed logs:

```yaml
logger:
  default: warning
  logs:
    custom_components.binformed: debug
```

## Brand images

Brand assets live in `custom_components/binformed/brand/` and reuse the icon of
the BInformed iOS app:

| File | Dimensions | Usage |
| --- | --- | --- |
| `icon.png` / `icon@2x.png` | 256² / 512² | Integration list, device card |
| `logo.png` / `logo@2x.png` | 1028×256 / 2057×512 | Integration page, light theme |
| `dark_logo.png` / `dark_logo@2x.png` | same | Dark theme |

Home Assistant **2026.3** or newer loads them automatically, with no
configuration. Older versions ignore them and fall back to the
[brands.home-assistant.io](https://brands.home-assistant.io) CDN.

The wordmark comes in two shades because the brand's light blue (`#2DABFA`)
only reaches a 2.4:1 contrast ratio on white: the light variant uses `#0B4FA8`
(7.5:1), the dark one keeps `#2DABFA`.

## Development

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/pytest --cov=custom_components.binformed --cov-report=term-missing
```

## License

[MIT](LICENSE)

[hacs]: https://github.com/hacs/integration
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-repo]: https://my.home-assistant.io/redirect/hacs_repository/?owner=chriphil&repository=homeassistant-binformed&category=integration
[hacs-repo-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[validate]: https://github.com/chriphil/homeassistant-binformed/actions/workflows/validate.yaml
[validate-badge]: https://github.com/chriphil/homeassistant-binformed/actions/workflows/validate.yaml/badge.svg?branch=main&event=push
