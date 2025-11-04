# Steam Key Library

> ⚠️ **Work in Progress** ⚠️  
> This project is currently under active development and is not yet complete. Many features are missing, and you may encounter bugs or unexpected behavior. Use at your own discretion and expect frequent changes.

A simple Steam game key management tool for organizing and tracking your activation keys.

## Overview

Steam Key Library helps you organize, track, and manage your Steam activation keys with a clean and straightforward interface.

## Key Features

- **Secure Key Storage**: Encrypted storage for your activation keys
- **Usage Tracking**: Track which keys have been activated
- **Search & Filter**: Find keys quickly with search functionality
- **Collection Management**: Organize keys with custom categories
- **Data Export**: Export your library for backup purposes
- **Simple Interface**: Clean, easy-to-use design

## System Requirements

- Node.js 16.0 or higher
- npm 8.0 or higher
- Modern web browser

## Installation

```bash
# Clone the repository
git clone https://github.com/NightmareFTW/SteamKeyLibrary.git

# Navigate to project directory
cd SteamKeyLibrary

# Install dependencies
npm install

# Start the application
npm start
```

## Quick Start Guide

1. **Launch**: Start the application
2. **Add Keys**: Input your Steam activation keys
3. **Organize**: Create categories for your games
4. **Track**: Mark keys as used when activated
5. **Search**: Use filters to find specific games

## Configuration

Create a `.env` file in the root directory:

```env
DATABASE_URL=sqlite://./steamkeys.db
ENCRYPTION_KEY=your_secure_encryption_key
PORT=3000
```

## ITAD API configuration

This app integrates with IsThereAnyDeal (ITAD) to look up bundle history. You'll need an API key:

- Create an API key in your ITAD account
- Set the environment variable `ITAD_API_KEY` before running the app

Example (Windows PowerShell, current session only):

```powershell
$env:ITAD_API_KEY = "<your_itad_api_key>"
```

Notes:

- If `ITAD_API_KEY` isn't set or the key is invalid/expired, ITAD lookups will fail and bundles may not be shown.
- The app uses IsThereAnyDeal's public API (OpenAPI): it looks up a game via `GET /games/lookup/v1` (by Steam appid or title) and fetches bundles via `GET /games/bundles/v2`. A custom User-Agent is included to comply with API requirements.

Optional: set your country (affects pricing/availability on some endpoints):

```powershell
$env:ITAD_COUNTRY = "PT"  # defaults to US if not set
```

## Optional providers (fallback)

You can optionally configure an authorized feed for bundle history as a fallback to ITAD (e.g., Barter.vg feeds). This app will only call a fallback if you explicitly configure it.

- Set `BARTER_BUNDLES_URL` to a provider feed template. It may include `{appid}` and/or `{title}` placeholders.

Example (PowerShell):

```powershell
$env:BARTER_BUNDLES_URL = "https://example.com/your-authorized-feed?appid={appid}&format=json"
# Optional auth header, if your feed requires it
$env:BARTER_AUTH_HEADER = "Bearer <token>"
```

Restrictions and notes:

- Respect the provider's Terms of Service. This app will not scrape websites; it will only use feeds or APIs you configure.
- Fallback results are cached locally for 12 hours to reduce load and avoid rate limits.
- The bundle selection popup will tag each entry with its source, e.g., "[ITAD]" or "[Barter]".

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## Security

- Local encryption for key storage
- No external data transmission
- Secure local database

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Legal Notice

**Important**: This tool is for personal use only. Please comply with Steam's Terms of Service and only use legitimate activation keys.

---
© 2024 Steam Key Library
