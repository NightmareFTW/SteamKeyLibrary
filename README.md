# Steam Key Library

Desktop app in Python + Tkinter to manage Steam keys, track bundle origin, and fetch Steam/ITAD pricing data.

## Features

- Local library of games and multiple keys per game
- Steam search with suggestions and automatic app lookup
- Price data from Steam store API (regular + historical low)
- Bundle history from ITAD (OpenAPI) with optional fallback feed
- Cloud sync support (JSONBin, Google Drive links, custom JSON endpoint)
- English and Portuguese (Portugal) UI
- Multiple visual themes (Steam, Dark, White, Black/Red)

## Requirements

- Python 3.10+
- pip

Dependencies:

- requests
- Pillow

## Quick Start

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install requests Pillow
python steamkeylibrary.py
```

Alternative launcher on Windows:

- Open [OpenSteamKeyLibrary.bat](OpenSteamKeyLibrary.bat)

## Configuration

Settings are stored locally and edited in-app in the Settings tab.

Sensitive fields (do not commit real values):

- ITAD API key
- Cloud URL/auth header
- Fallback provider auth header

Environment variables supported:

```powershell
$env:ITAD_API_KEY = "<your_itad_api_key>"
$env:ITAD_COUNTRY = "PT"
$env:CLOUD_SAVE_URL = "https://api.jsonbin.io/v3/b/YOUR_BIN_ID"
$env:CLOUD_AUTH_HEADER = "X-Master-Key <your_key>"
$env:BARTER_BUNDLES_URL = "https://example.com/feeds/bundles?appid={appid}&format=json"
$env:BARTER_AUTH_HEADER = "Bearer <token>"
```

## Data Files

The app creates/uses these local files:

- games.json
- settings.json
- itad_cache.json
- steam_applist.json

For public repositories, these files are ignored by default in [.gitignore](.gitignore).

## Screenshots

Add your screenshots to [docs/screenshots](docs/screenshots) and keep these names for automatic README preview:

- [Library view](docs/screenshots/library.png)
- [Add game dialog](docs/screenshots/add-game.png)
- [Settings view](docs/screenshots/settings.png)

![Library view](docs/screenshots/library.png)
![Add game dialog](docs/screenshots/add-game.png)
![Settings view](docs/screenshots/settings.png)

## Build EXE (Windows)

```powershell
.\build_exe.bat
```

Output:

- dist/SteamKeyLibrary.exe

## Privacy & Publishing Checklist

Before publishing:

1. Keep personal keys/tokens only in local settings (never commit them).
2. Keep local library/cache files out of Git.
3. Rotate any key that was previously exposed.

## License

MIT - see [LICENSE](LICENSE)
