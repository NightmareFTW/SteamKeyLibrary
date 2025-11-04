# Steam Key Library

> ⚠️ Work in Progress

A lightweight desktop app (Python + Tkinter) to organize your Steam keys, fetch game info from Steam, and suggest bundle origins via IsThereAnyDeal (ITAD) and optional fallback providers.

## Overview

- Add a game by name with typeahead suggestions powered by a cached Steam app list
- Fetch Steam header image and price info automatically
- Suggest bundles via provider pipeline: ITAD (OpenAPI) → ITAD (legacy v02) → optional authorized feed
- Persist your ITAD API key and country in-app (Settings menu)
- Quick “Test Providers” dialog and “Validate ITAD Key” action
- Manual entry flow if no bundle information is available

## Requirements

- Python 3.10+ (Windows/macOS/Linux)
- pip

Python packages used:
- `requests` (HTTP)
- `Pillow` (images)

## Setup

```powershell
# 1) Create and activate a virtual environment (recommended)
python -m venv .venv
. .venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install requests Pillow

# 3) Run the app
python steamkeylibrary.py
```

On first launch, the app will download the Steam app list and cache it locally.

## Using the app

1) Click “Add Game”
- Start typing a title; pick one from the suggestions
- The app fetches official title/price/image from Steam
2) If bundles are found via providers, select one; otherwise you can proceed with manual entry
3) Your game is saved to `games.json`

## Configuration

### ITAD (IsThereAnyDeal)

You need an API key to use the ITAD provider:

- In the app: Settings → “Set ITAD API Key…” (stored in `settings.json`)
- Or via environment variable before running:

```powershell
$env:ITAD_API_KEY = "<your_itad_api_key>"
```

Optional: set your country for ITAD (ISO 3166‑1 alpha‑2, e.g., US, PT):

```powershell
$env:ITAD_COUNTRY = "PT"
```

Endpoints used (OpenAPI):
- `GET https://api.isthereanydeal.com/games/lookup/v1` (by Steam appid or title) → returns ITAD Game ID
- `GET https://api.isthereanydeal.com/games/bundles/v2` (by ITAD Game ID) → returns bundles

Notes and troubleshooting:
- If your key is new, it may need activation/approval and/or a short propagation period. Until then, ITAD can reply `403 Invalid or expired api key`.
- Use Settings → “Validate ITAD Key…” to run a quick lookup test and see the server’s reason if it fails.
- The Providers bar shows “ITAD key: Invalid — <reason>” when the server rejects the key.

### Optional fallback provider (authorized feed)

You can configure a custom, authorized feed (e.g., Barter.vg API/feeds you’re allowed to use). The app will only call a fallback if you explicitly set it.

Set these environment variables if desired:

```powershell
$env:BARTER_BUNDLES_URL = "https://example.com/feeds/bundles?appid={appid}&format=json"
# Optional auth header if your feed requires it
$env:BARTER_AUTH_HEADER = "Bearer <token>"
```

Placeholders supported in the URL:
- `{appid}` — Steam appid
- `{title}` — URL‑encoded title

Toggle the fallback in the UI (“Enable fallback” in the Providers bar).

## Data files

- `games.json` — your saved library
- `steam_applist.json` — cached Steam app list (24h TTL)
- `itad_cache.json` — cached provider results (12h TTL)
- `settings.json` — app settings (ITAD key, country)

## Privacy and legal

- No scraping is performed. Only configured APIs/feeds are called.
- Respect each provider’s terms of service.
- Use only legitimate activation keys and comply with Steam’s terms.

## License

MIT — see [LICENSE](LICENSE)

© 2024 Steam Key Library
