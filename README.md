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
