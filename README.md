# Garmin Data Bridge for Home Assistant

A read-only, deliberately small Home Assistant API for Garmin Connect IQ watch faces.

> **Early development / 0.1.0 prototype.** The HTTP and authentication code
> has not yet been tested inside a running Home Assistant instance. Do not
> expose this integration to the internet before that validation is complete.

## Design

- Each configured profile has its **own independent bearer token**.
- A token only grants access to the selected states in its profile; it is
  **not** a Home Assistant user token and cannot call Home Assistant services.
- The token is displayed **once**, during profile creation. Only its SHA-256
  digest is retained in Home Assistant's config entry.
- The API returns at most eight explicitly selected entities. It exposes only
  a short display label, string value, unit, slot number and availability.
  It never includes entity attributes or entity IDs.
- Options can be changed through **Settings → Devices & services → Garmin Data
  Bridge → Configure**. The changes take effect on subsequent HTTP requests.
- To revoke or rotate a token in this initial version, remove its profile and
  create a new one. Multiple profiles have independent keys.

## Installation (development)

Until the repository is public, install manually: copy
`custom_components/garmin_data_bridge/` to the same directory under your
Home Assistant `config` folder, restart Home Assistant, then add
**Garmin Data Bridge** in Settings → Devices & services.

Home Assistant 2026.11+ includes the Marketplace (formerly HACS). The
Marketplace **cannot install private GitHub repositories**. Once public, this
repository can be added from **Settings → Marketplace → Add from link**.
The same layout works with earlier HACS versions.

## Setup

1. Add the integration and choose a profile name and 1–8 entities.
2. **Copy the token** from the pre-filled text field in the confirmation step before
   submitting. Focus the input and use Select All / Copy (Ctrl+A, Ctrl+C or
   Cmd+A, Cmd+C) to avoid missing characters. Do not edit the token: the form
   will reject modified text. The token cannot be recovered later.
3. Set the URL and token in the Connect IQ client's settings (client code is
   a separate project).

```text
GET https://YOUR-HA-DOMAIN/api/garmin_data_bridge/v1/data
Authorization: Bearer YOUR_PROFILE_TOKEN
```

Example response (values are illustrative):

```json
{
  "version": 1,
  "generated_at": "2026-11-12T10:40:00+00:00",
  "items": [
    {
      "slot": 1,
      "label": "Outside temperature",
      "value": "4.2",
      "unit": "°C",
      "status": "ok"
    }
  ]
}
```

An invalid or missing token returns HTTP 401 and never exposes state data.

## Security boundaries

Use **HTTPS with a valid certificate**, never put tokens in query strings,
and do not embed them in published watch-face source code. An HA administrator
chooses the entities; a client bearing that profile's token can retrieve those
states even when it has no standard HA credentials. Tokens are high-entropy
secrets and must be handled like passwords. Do not expose personal or sensitive
states casually.

This is a polling endpoint, not a public webhook and not a control API.
Rate limiting and more convenient one-time pairing are future improvements.
For now configure reasonable polling intervals on the watch, for example
10–15 minutes.

## Scope of v0.1.0

The endpoint, profile setup, selected-entity options, unit tests and CI
are the first increment. Device pairing, friendly slot aliases, token
rotation without recreating a profile, and an actual Garmin watch face
are intentionally not included yet.
