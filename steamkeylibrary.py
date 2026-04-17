import difflib
import io
import re
from html import unescape as _html_unescape
import json
import os
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from urllib.parse import parse_qs, urlparse

import requests
from PIL import Image, ImageTk


if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(APP_DIR, "games.json")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
STEAM_APPLIST_CACHE_FILE = os.path.join(APP_DIR, "steam_applist.json")
STEAM_APPLIST_CACHE_TTL = 60 * 60 * 24
ITAD_CACHE_FILE = os.path.join(APP_DIR, "itad_cache.json")
ITAD_CACHE_TTL = 60 * 60 * 12
APP_ICON_FILE = os.path.join(APP_DIR, "app_icon.ico")

ITAD_BASE_URL = "https://api.isthereanydeal.com"
ITAD_STEAM_SHOP_ID = 61  # Steam shop ID on IsThereAnyDeal
HTTP_HEADERS = {
    "User-Agent": "SteamKeyLibrary/1.0 (+https://github.com/NightmareFTW/SteamKeyLibrary)",
}

ITAD_LAST_ERROR = ""
ITAD_LAST_STATUS = 0


TRANSLATIONS = {
    "en": {
        "title": "Steam Key Library",
        "subtitle": "Track Steam keys, bundles, prices and notes in one place.",
        "tab_library": "Library",
        "tab_settings": "Settings",
        "search": "Search",
        "details": "Details",
        "general": "General",
        "providers": "Providers",
        "cloud": "Cloud Sync",
        "add_game": "Add Game",
        "remove_game": "Remove Selected",
        "save_changes": "Save Changes",
        "show_key": "Show Key",
        "hide_key": "Hide Key",
        "status": "Status",
        "game": "Game",
        "note": "Note",
        "bundle_dropdown": "Bundles",
        "platform": "Bundle Platform",
        "bundle_name": "Bundle Name",
        "drm": "DRM",
        "steam_regular_eur": "Steam Regular EUR",
        "steam_regular_usd": "Steam Regular USD",
        "steam_lowest_eur": "Steam Lowest EUR",
        "steam_lowest_usd": "Steam Lowest USD",
        "steam_regular": "Steam Regular",
        "steam_lowest": "Steam Historical Low",
        "best_price_shop": "Best Current Shop",
        "best_price_value": "Best Current Price",
        "bundle_date": "Bundle Date",
        "key_code": "Steam Key Code",
        "theme": "Theme",
        "language": "Language",
        "currency": "Currency",
        "save_mode": "Save Mode",
        "save_mode_local": "Local only",
        "save_mode_cloud": "Cloud only",
        "save_mode_both": "Local and Cloud",
        "cloud_url": "Cloud Save URL",
        "cloud_auth": "Cloud Auth Header",
        "cloud_download": "Load from Cloud",
        "cloud_upload": "Upload to Cloud",
        "cloud_missing_url": "Cloud URL is empty. Add it in Settings.",
        "cloud_load_failed": "Failed to load cloud save.",
        "cloud_save_failed": "Failed to upload cloud save.",
        "cloud_load_ok": "Cloud save loaded successfully.",
        "cloud_save_ok": "Cloud save uploaded successfully.",
        "cloud_jsonbin_tutorial_btn": "Jsonbin Tutorial",
        "cloud_jsonbin_tutorial_title": "Jsonbin.io Setup",
        "cloud_jsonbin_tutorial_body": "1. Create an account at jsonbin.io and create a new bin.\n\n2. Save valid JSON, for example: {\"games\": []}\n(Do not use comments like // ...).\n\n3. Copy your Bin ID and set Cloud Save URL to:\nhttps://api.jsonbin.io/v3/b/YOUR_BIN_ID\n\n4. Copy your Master Key (or Access Key) from API Access.\n\n5. In Cloud Auth Header, paste one of these:\n- X-Master-Key <your_key>\n- X-Access-Key <your_key>\n- or just the key itself.\n\n6. Use 'Upload to Cloud' and then 'Load from Cloud' to verify sync.",
        "copy_text": "Copy",
        "close": "Close",
        "itad_key": "ITAD API Key",
        "itad_key_info": "API key required for bundle and price data. Register your app at isthereanydeal.com/apps/my/ to get a key.",
        "itad_country": "ITAD Country",
        "fallback": "Enable fallback provider",
        "fallback_url": "Fallback feed URL",
        "fallback_auth": "Fallback auth header",
        "save_settings": "Save Settings",
        "validate_itad": "Validate ITAD Key",
        "loading_catalog": "Loading Steam catalog...",
        "ready": "Ready",
        "warning": "Warning",
        "error": "Error",
        "ok": "OK",
        "in_stock": "In Stock",
        "sold": "Sold",
        "manual_bundle": "No bundle / manual",
        "fetch_online": "Fetch Online Data",
        "search_hint": "Type game name",
        "add_dialog_title": "Add Game",
        "game_name": "Game Name",
        "suggestions": "Suggestions",
        "confirm_add": "Add Game",
        "select_first": "Please select a game from suggestions or type a valid title.",
        "catalog_loading_wait": "Steam catalog is still loading. Please wait a moment.",
        "game_not_found": "Game not found on Steam.",
        "saved_settings": "Settings saved successfully.",
        "saved_game": "Game added successfully.",
        "removed_game": "Game removed.",
        "itad_key_missing": "ITAD API key is missing. Add it in Settings.",
        "itad_key_invalid": "ITAD key is invalid or expired.",
        "itad_no_bundles": "No bundles were returned for this game.",
        "keys_section": "Steam Keys",
        "add_key": "Add Key",
        "key_status_stock": "Not sold",
        "key_status_sold": "Sold",
        "key_status_listed": "Listed for sale",
        "confirm_remove_key_title": "Remove Key?",
        "confirm_remove_key": "Are you sure you want to remove this key?\nThis cannot be undone.",
        "tooltip_keys": "Each row is one Steam key.\n\n◻  Not sold (in stock)\n✓  Sold\n🛒  Listed for sale on a platform\n\nClick the icon to cycle between states.\nClick Show/Hide to reveal the key code.",
        "confirm_remove_title": "Remove Game?",
        "confirm_remove": "Are you sure you want to remove '{name}'?\nThis cannot be undone.",
        "tooltip_theme": "Select visual style.\nSteam: classic blue.\nDark: neutral dark.\nWhite: high-contrast light.",
        "tooltip_language": "UI language.\nUse en for English or pt-PT for Portuguese (Portugal).",
        "tooltip_currency": "Choose which currency to display for Steam regular and lowest-ever prices.",
        "tooltip_itad_key": "API key from isthereanydeal.com/apps/my/\nRequired for bundle history and Steam lowest price data.",
        "tooltip_itad_country": "Two-letter country code used by ITAD (examples: PT, US, GB).\nAffects regional store pricing and availability.",
        "tooltip_fallback": "Enable if you configured an authorised fallback bundle feed.\nOnly use sources you are allowed to access.",
        "tooltip_fallback_url": "URL to your authorised fallback JSON feed.\nSupported placeholders: {appid} and {title}.",
        "tooltip_fallback_auth": "Optional HTTP Authorization header for the fallback feed.\nExamples:\nBearer YOUR_TOKEN\nApiKey YOUR_KEY",
        "tooltip_save_mode": "local – save only on this PC\ncloud – save only to cloud URL\nboth – save locally and to cloud",
    },
    "pt-PT": {
        "title": "Steam Key Library",
        "subtitle": "Guarda chaves Steam, bundles, preços e notas num só local.",
        "tab_library": "Biblioteca",
        "tab_settings": "Definições",
        "search": "Procurar",
        "details": "Detalhes",
        "general": "Geral",
        "providers": "Fornecedores",
        "cloud": "Sincronização Cloud",
        "add_game": "Adicionar Jogo",
        "remove_game": "Remover Seleccionado",
        "save_changes": "Guardar Alterações",
        "show_key": "Mostrar Chave",
        "hide_key": "Ocultar Chave",
        "status": "Estado",
        "game": "Jogo",
        "note": "Nota",
        "bundle_dropdown": "Bundles",
        "platform": "Plataforma do Bundle",
        "bundle_name": "Nome do Bundle",
        "drm": "DRM",
        "steam_regular_eur": "Preço regular Steam EUR",
        "steam_regular_usd": "Preço regular Steam USD",
        "steam_lowest_eur": "Preço em saldo Steam EUR",
        "steam_lowest_usd": "Preço em saldo Steam USD",
        "steam_regular": "Preço regular Steam",
        "steam_lowest": "Preço mínimo histórico Steam",
        "best_price_shop": "Loja mais barata agora",
        "best_price_value": "Preço mais barato agora",
        "bundle_date": "Data do Bundle",
        "key_code": "Código da Chave Steam",
        "theme": "Tema",
        "language": "Idioma",
        "currency": "Moeda",
        "save_mode": "Modo de gravação",
        "save_mode_local": "Apenas local",
        "save_mode_cloud": "Apenas cloud",
        "save_mode_both": "Local e cloud",
        "cloud_url": "Link do save cloud",
        "cloud_auth": "Header de autenticação cloud",
        "cloud_download": "Carregar da cloud",
        "cloud_upload": "Enviar para a cloud",
        "cloud_missing_url": "O link da cloud está vazio. Define-o nas Definições.",
        "cloud_load_failed": "Falha ao carregar save da cloud.",
        "cloud_save_failed": "Falha ao enviar save para a cloud.",
        "cloud_load_ok": "Save cloud carregado com sucesso.",
        "cloud_save_ok": "Save cloud enviado com sucesso.",
        "cloud_jsonbin_tutorial_btn": "Tutorial Jsonbin",
        "cloud_jsonbin_tutorial_title": "Configuração Jsonbin.io",
        "cloud_jsonbin_tutorial_body": "1. Cria conta em jsonbin.io e cria um novo bin.\n\n2. Guarda JSON válido, por exemplo: {\"games\": []}\n(Não uses comentários como // ...).\n\n3. Copia o Bin ID e define o Link do save cloud como:\nhttps://api.jsonbin.io/v3/b/SEU_BIN_ID\n\n4. Copia a Master Key (ou Access Key) em API Access.\n\n5. Em Header de autenticação cloud, usa uma destas formas:\n- X-Master-Key <a_tua_key>\n- X-Access-Key <a_tua_key>\n- ou apenas a key.\n\n6. Usa 'Enviar para a cloud' e depois 'Carregar da cloud' para validar a sincronização.",
        "copy_text": "Copiar",
        "close": "Fechar",
        "itad_key": "Chave API ITAD",
        "itad_key_info": "Chave API necessária para dados de bundles e preços. Regista a tua app em isthereanydeal.com/apps/my/ para obter uma chave.",
        "itad_country": "País ITAD",
        "fallback": "Activar fornecedor fallback",
        "fallback_url": "URL feed fallback",
        "fallback_auth": "Header auth fallback",
        "save_settings": "Guardar Definições",
        "validate_itad": "Validar Chave ITAD",
        "loading_catalog": "A carregar catálogo Steam...",
        "ready": "Pronto",
        "warning": "Aviso",
        "error": "Erro",
        "ok": "OK",
        "in_stock": "Em Stock",
        "sold": "Vendido",
        "manual_bundle": "Sem bundle / manual",
        "fetch_online": "Procurar Dados Online",
        "search_hint": "Escreve o nome do jogo",
        "add_dialog_title": "Adicionar Jogo",
        "game_name": "Nome do Jogo",
        "suggestions": "Sugestões",
        "confirm_add": "Adicionar Jogo",
        "select_first": "Selecciona um jogo das sugestões ou escreve um título válido.",
        "catalog_loading_wait": "Catálogo Steam ainda a carregar. Tenta novamente daqui a pouco.",
        "game_not_found": "Jogo não encontrado na Steam.",
        "saved_settings": "Definições guardadas com sucesso.",
        "saved_game": "Jogo adicionado com sucesso.",
        "removed_game": "Jogo removido.",
        "itad_key_missing": "A chave API ITAD não está definida. Adiciona-a nas Definições.",
        "itad_key_invalid": "A chave ITAD é inválida ou expirou.",
        "itad_no_bundles": "Não foram devolvidos bundles para este jogo.",
        "keys_section": "Chaves Steam",
        "add_key": "Adicionar Chave",
        "key_status_stock": "Não vendida",
        "key_status_sold": "Vendida",
        "key_status_listed": "À venda",
        "confirm_remove_key_title": "Remover Chave?",
        "confirm_remove_key": "Tens a certeza que queres remover esta chave?\nEsta acção não pode ser desfeita.",
        "tooltip_keys": "Cada linha é uma chave Steam.\n\n◻  Não vendida (em stock)\n✓  Vendida\n🛒  Publicada à venda numa plataforma\n\nClica no ícone para mudar o estado.\nClica em Mostrar/Ocultar para revelar o código.",
        "confirm_remove_title": "Remover Jogo?",
        "confirm_remove": "Tens a certeza que queres remover '{name}'?\nEsta acção não pode ser desfeita.",
        "tooltip_theme": "Selecciona o estilo visual.\nSteam: azul clássico.\nDark: escuro neutro.\nWhite: claro de alto contraste.",
        "tooltip_language": "Idioma da interface.\nUsa en para inglês ou pt-PT para português (Portugal).",
        "tooltip_currency": "Escolhe a moeda para mostrar os preços regulares e o mínimo histórico da Steam.",
        "tooltip_itad_key": "Chave API em isthereanydeal.com/apps/my/\nNecessária para histórico de bundles e preço mínimo Steam.",
        "tooltip_itad_country": "Código de dois caracteres do país no ITAD (exemplos: PT, US, GB).\nAfecta preços e disponibilidade regionais.",
        "tooltip_fallback": "Activa se configuraste um feed fallback autorizado de bundles.\nUsa apenas fontes a que tens acesso.",
        "tooltip_fallback_url": "URL do teu feed JSON fallback autorizado.\nPlaceholders suportados: {appid} e {title}.",
        "tooltip_fallback_auth": "Header HTTP Authorization opcional para o feed fallback.\nExemplos:\nBearer TOKEN\nApiKey CHAVE",
        "tooltip_save_mode": "local – guarda só neste PC\ncloud – guarda só no URL cloud\nboth – guarda localmente e na cloud",
    },
}


THEMES = {
    "steam": {
        "name": "Steam",
        "bg": "#0b1a27",
        "surface": "#142433",
        "surface_alt": "#1a3147",
        "text": "#f1f5f9",
        "muted": "#9fb3c8",
        "accent": "#66c0f4",
        "danger": "#f87171",
    },
    "dark": {
        "name": "Dark",
        "bg": "#101114",
        "surface": "#1a1d24",
        "surface_alt": "#222733",
        "text": "#f5f5f5",
        "muted": "#b2b8c5",
        "accent": "#27c1a5",
        "danger": "#ef6a6a",
    },
    "light": {
        "name": "White",
        "bg": "#f4f6f8",
        "surface": "#ffffff",
        "surface_alt": "#e9edf2",
        "text": "#17212b",
        "muted": "#506174",
        "accent": "#0078d4",
        "danger": "#d13438",
    },
    "black_red": {
        "name": "Black/Red",
        "bg": "#070707",
        "surface": "#141414",
        "surface_alt": "#1f1f1f",
        "text": "#f5f5f5",
        "muted": "#b4b4b4",
        "accent": "#ef4444",
        "danger": "#ef4444",
    },
}


DEBUG_LOGS = []


class InfoTooltip:
    def __init__(self, root, widget, text, palette):
        self.root = root
        self.widget = widget
        self.text = text
        self.palette = palette
        self.tip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<Button-1>", self.toggle)

    def show(self, _event=None):
        if self.tip is not None:
            return
        self.tip = tk.Toplevel(self.root)
        self.tip.wm_overrideredirect(True)
        palette = getattr(self.root, "current_palette", self.palette)
        self.tip.configure(bg=palette["surface_alt"])
        display_text = self.text() if callable(self.text) else self.text
        label = tk.Label(
            self.tip,
            text=display_text,
            justify="left",
            wraplength=360,
            bg=palette["surface_alt"],
            fg=palette["text"],
            bd=1,
            relief="solid",
            padx=10,
            pady=8,
            font=("Segoe UI", 9),
        )
        label.pack()

        # Reposition tooltip so it always stays visible on-screen and inside app bounds.
        self.tip.update_idletasks()
        tip_w = self.tip.winfo_reqwidth()
        tip_h = self.tip.winfo_reqheight()

        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + 20

        app_left = self.root.winfo_rootx()
        app_top = self.root.winfo_rooty()
        app_right = app_left + self.root.winfo_width()
        app_bottom = app_top + self.root.winfo_height()

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        # Keep within application window first.
        if x + tip_w > app_right - 8:
            x = max(app_left + 8, app_right - tip_w - 8)
        if y + tip_h > app_bottom - 8:
            # Try placing above the icon when there is no room below.
            y = self.widget.winfo_rooty() - tip_h - 8
        if y < app_top + 8:
            y = app_top + 8

        # Final clamp to screen bounds for multi-window/fullscreen edge cases.
        x = max(8, min(x, screen_w - tip_w - 8))
        y = max(8, min(y, screen_h - tip_h - 8))

        self.tip.geometry(f"+{x}+{y}")

    def hide(self, _event=None):
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None

    def toggle(self, _event=None):
        if self.tip is None:
            self.show()
        else:
            self.hide()


def _log(message: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {message}"
    DEBUG_LOGS.append(line)
    try:
        print(line)
    except Exception:
        pass


def _set_itad_error(status: int, message: str):
    global ITAD_LAST_STATUS, ITAD_LAST_ERROR
    ITAD_LAST_STATUS = status or 0
    ITAD_LAST_ERROR = _safe_str(message)


def _extract_reason(response):
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return payload.get("reason_phrase") or payload.get("message") or response.text[:160]
    except Exception:
        pass
    return (response.text or "").strip()[:160]


def _load_json(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _save_json(path: str, payload):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        _log(f"Could not write {path}: {exc}")


def _safe_str(value) -> str:
    if value is None:
        return ""
    return str(value)


def _money(value):
    try:
        if value is None:
            return ""
        return f"{float(value):.2f}"
    except Exception:
        return ""


def default_settings():
    return {
        "language": "pt-PT",
        "theme": "steam",
        "display_currency": os.getenv("DISPLAY_CURRENCY", "EUR"),
        "save_mode": os.getenv("SAVE_MODE", "local"),
        "cloud_save_url": os.getenv("CLOUD_SAVE_URL", ""),
        "cloud_auth_header": os.getenv("CLOUD_AUTH_HEADER", ""),
        "ITAD_API_KEY": os.getenv("ITAD_API_KEY", ""),
        "ITAD_COUNTRY": os.getenv("ITAD_COUNTRY", "PT"),
        "fallback_enabled": bool(os.getenv("BARTER_BUNDLES_URL")),
        "fallback_url": os.getenv("BARTER_BUNDLES_URL", ""),
        "fallback_auth": os.getenv("BARTER_AUTH_HEADER", ""),
    }


def load_settings():
    cfg = default_settings()
    disk = _load_json(SETTINGS_FILE, {})
    if isinstance(disk, dict):
        cfg.update(disk)
    if cfg.get("theme") not in THEMES:
        cfg["theme"] = "steam"
    if cfg.get("language") not in TRANSLATIONS:
        cfg["language"] = "en"
    if _safe_str(cfg.get("display_currency", "EUR")).upper() not in ("EUR", "USD"):
        cfg["display_currency"] = "EUR"
    if _safe_str(cfg.get("save_mode", "local")) not in ("local", "cloud", "both"):
        cfg["save_mode"] = "local"
    return cfg


def load_games():
    payload = _load_json(DATA_FILE, [])
    if not isinstance(payload, list):
        return []
    return payload


def save_games(games):
    _save_json(DATA_FILE, games)


def cloud_download_games(url: str, auth_header: str = ""):
    if not url:
        return None, "Missing cloud URL"
    try:
        headers = dict(HTTP_HEADERS)
        if auth_header:
            headers["Authorization"] = auth_header

        if _is_jsonbin_url(url):
            download_url = _jsonbin_download_url(url)
            headers.update(_jsonbin_auth_headers(auth_header))
            headers["X-Bin-Meta"] = "false"
            r = requests.get(download_url, headers=headers, timeout=25)
            if r.status_code != 200:
                return None, f"HTTP {r.status_code}: {_extract_reason(r)}"
            return _parse_cloud_games_payload(r)

        drive_file_id = _extract_google_drive_file_id(url)
        if drive_file_id:
            # Google Drive share links are read-only by URL; convert to direct content URL.
            if auth_header.lower().startswith("bearer "):
                download_url = f"https://www.googleapis.com/drive/v3/files/{drive_file_id}?alt=media"
                r = requests.get(download_url, headers=headers, timeout=25)
            else:
                download_url = f"https://drive.google.com/uc?export=download&id={drive_file_id}"
                r = requests.get(download_url, headers=headers, timeout=25, allow_redirects=True)

            if r.status_code != 200:
                return None, f"HTTP {r.status_code}: {_extract_reason(r)}"

            content_type = _safe_str(r.headers.get("Content-Type", "")).lower()
            body = _safe_str(r.text)
            if "text/html" in content_type and ("<html" in body.lower() or "google drive" in body.lower()):
                return None, "Google Drive file is not publicly readable. Share it with 'Anyone with the link' or use Bearer auth."

            return _parse_cloud_games_payload(r)

        r = requests.get(url, headers=headers, timeout=25)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {_extract_reason(r)}"
        return _parse_cloud_games_payload(r)
    except Exception as exc:
        return None, str(exc)


def cloud_upload_games(url: str, auth_header: str, games: list):
    if not url:
        return False, "Missing cloud URL"
    try:
        headers = dict(HTTP_HEADERS)
        if auth_header:
            headers["Authorization"] = auth_header
        payload = {"games": games}

        if _is_jsonbin_url(url):
            upload_url = _jsonbin_upload_url(url)
            headers.update(_jsonbin_auth_headers(auth_header))
            headers["Content-Type"] = "application/json"
            r = requests.put(upload_url, json=payload, headers=headers, timeout=25)
            if r.status_code in (200, 201, 202, 204):
                return True, ""
            return False, f"HTTP {r.status_code}: {_extract_reason(r)}"

        drive_file_id = _extract_google_drive_file_id(url)
        if drive_file_id:
            if not auth_header.lower().startswith("bearer "):
                return (
                    False,
                    "Google Drive upload needs OAuth token. In 'Cloud Auth Header' use: Bearer <access_token>. "
                    "A normal shared Drive link alone cannot receive uploads.",
                )
            api_url = f"https://www.googleapis.com/upload/drive/v3/files/{drive_file_id}?uploadType=media"
            headers["Content-Type"] = "application/json; charset=utf-8"
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            r = requests.patch(api_url, data=raw, headers=headers, timeout=25)
            if r.status_code in (200, 201, 202, 204):
                return True, ""
            return False, f"HTTP {r.status_code}: {_extract_reason(r)}"

        # Try PUT first, then POST for endpoints that don't support PUT.
        r = requests.put(url, json=payload, headers=headers, timeout=25)
        if r.status_code in (200, 201, 202, 204):
            return True, ""
        r2 = requests.post(url, json=payload, headers=headers, timeout=25)
        if r2.status_code in (200, 201, 202, 204):
            return True, ""
        return False, f"HTTP {r2.status_code}: {_extract_reason(r2)}"
    except Exception as exc:
        return False, str(exc)


def _extract_google_drive_file_id(url: str) -> str:
    text = _safe_str(url).strip()
    if not text:
        return ""
    try:
        parsed = urlparse(text)
        host = parsed.netloc.lower()
        if "drive.google.com" not in host and "docs.google.com" not in host:
            return ""

        m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", parsed.path)
        if m:
            return m.group(1)

        query = parse_qs(parsed.query)
        if query.get("id"):
            return _safe_str(query["id"][0]).strip()
    except Exception:
        return ""
    return ""


def _is_jsonbin_url(url: str) -> bool:
    text = _safe_str(url).strip().lower()
    return "api.jsonbin.io" in text and "/v3/b/" in text


def _jsonbin_download_url(url: str) -> str:
    parsed = urlparse(_safe_str(url).strip())
    path = _safe_str(parsed.path).rstrip("/")
    if not path.endswith("/latest"):
        path = f"{path}/latest"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _jsonbin_upload_url(url: str) -> str:
    parsed = urlparse(_safe_str(url).strip())
    path = _safe_str(parsed.path).rstrip("/")
    if path.endswith("/latest"):
        path = path[:-7]
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _jsonbin_auth_headers(auth_header: str) -> dict:
    auth = _safe_str(auth_header).strip()
    if not auth:
        return {}

    low = auth.lower()
    if low.startswith("x-master-key "):
        return {"X-Master-Key": auth[len("x-master-key "):].strip()}
    if low.startswith("x-access-key "):
        return {"X-Access-Key": auth[len("x-access-key "):].strip()}
    if low.startswith("bearer "):
        token = auth[len("bearer "):].strip()
        return {"X-Access-Key": token}
    if auth.startswith("$2"):
        return {"X-Master-Key": auth}
    return {"X-Master-Key": auth}


def _parse_cloud_games_payload(response):
    try:
        payload = response.json()
    except Exception:
        text = _safe_str(response.text).strip()
        if not text:
            return None, "Cloud response is empty"
        try:
            payload = json.loads(text)
        except Exception:
            return None, "Cloud payload format is invalid"

    if isinstance(payload, list):
        return payload, ""
    if isinstance(payload, dict) and isinstance(payload.get("record"), list):
        return payload.get("record"), ""
    if isinstance(payload, dict) and isinstance(payload.get("record"), dict) and isinstance(payload.get("record").get("games"), list):
        return payload.get("record").get("games"), ""
    if isinstance(payload, dict) and isinstance(payload.get("games"), list):
        return payload.get("games"), ""
    return None, "Cloud payload format is invalid"


def get_steam_applist():
    stale_cache = []
    if os.path.exists(STEAM_APPLIST_CACHE_FILE):
        try:
            cached = _load_json(STEAM_APPLIST_CACHE_FILE, [])
            if isinstance(cached, list) and cached:
                stale_cache = cached
            mtime = os.path.getmtime(STEAM_APPLIST_CACHE_FILE)
            if time.time() - mtime < STEAM_APPLIST_CACHE_TTL:
                return stale_cache
        except Exception:
            pass
    urls = [
        "https://api.steampowered.com/ISteamApps/GetAppList/v0002/",
        "https://api.steampowered.com/ISteamApps/GetAppList/v2/",
    ]
    for url in urls:
        try:
            _log(f"GET {url}")
            r = requests.get(url, timeout=25, headers=HTTP_HEADERS)
            r.raise_for_status()
            apps = r.json().get("applist", {}).get("apps", [])
            if isinstance(apps, list) and apps:
                _save_json(STEAM_APPLIST_CACHE_FILE, apps)
                return apps
        except Exception as exc:
            _log(f"Steam applist failed for {url}: {exc}")
    if stale_cache:
        _log("Using stale local Steam applist cache as fallback.")
        return stale_cache
    return []


def steam_store_search(query: str, limit=15):
    q = (query or "").strip()
    if not q:
        return []
    try:
        url = "https://store.steampowered.com/api/storesearch"
        params = {"term": q, "l": "en", "cc": "pt"}
        r = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=20)
        r.raise_for_status()
        payload = r.json() if r.text else {}
        items = payload.get("items") or []
        out = []
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            appid = item.get("id")
            if name and appid:
                out.append((name, appid))
        return out
    except Exception as exc:
        _log(f"Steam store search failed: {exc}")
        return []


def search_steam_suggestions(query: str, applist, limit=15):
    q = (query or "").strip().lower()
    if not q:
        return []
    if not applist:
        return steam_store_search(query, limit=limit)
    starts = []
    contains = []
    for app in applist:
        name = app.get("name") or ""
        appid = app.get("appid")
        nl = name.lower()
        if nl.startswith(q):
            starts.append((name, appid))
        elif q in nl:
            contains.append((name, appid))
    result = starts + contains
    if len(result) < limit:
        names = [a.get("name", "") for a in applist if a.get("name")]
        fuzzy = difflib.get_close_matches(query, names, n=limit * 2, cutoff=0.78)
        for name in fuzzy:
            for app in applist:
                if app.get("name") == name:
                    pair = (name, app.get("appid"))
                    if pair not in result:
                        result.append(pair)
                    break
    return result[:limit]


def get_steam_appid_by_name(game_name: str, applist):
    if not game_name:
        return None
    if not applist:
        direct = steam_store_search(game_name, limit=8)
        if not direct:
            return None
        exact = next((a for a in direct if _safe_str(a[0]).lower() == game_name.strip().lower()), None)
        return (exact or direct[0])[1]
    gl = game_name.strip().lower()
    for app in applist:
        if (app.get("name") or "").lower() == gl:
            return app.get("appid")
    starts = [a for a in applist if (a.get("name") or "").lower().startswith(gl)]
    if starts:
        return starts[0].get("appid")
    contains = [a for a in applist if gl in (a.get("name") or "").lower()]
    if contains:
        return contains[0].get("appid")
    return None


def get_steam_store_snapshot(appid: int, cc: str):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={cc}&l=en"
        r = requests.get(url, timeout=25, headers=HTTP_HEADERS)
        data = r.json().get(str(appid), {})
        if not data.get("success"):
            return {}
        info = data.get("data") or {}
        price = info.get("price_overview") or {}
        final = (price.get("final", 0) or 0) / 100
        initial = (price.get("initial", 0) or 0) / 100
        if initial <= 0:
            initial = final
        return {
            "title": info.get("name") or "",
            "image_url": info.get("header_image")
            or f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg",
            "current": _money(final),
            "regular": _money(initial),
            "currency": (price.get("currency") or "").upper(),
        }
    except Exception as exc:
        _log(f"Steam store snapshot failed ({appid}, {cc}): {exc}")
        return {}


def _itad_request(url: str, params: dict, key: str):
    if not key:
        _set_itad_error(401, "Missing api key")
        return None
    try:
        req_params = dict(params)
        req_params["key"] = key
        r = requests.get(url, params=req_params, headers=HTTP_HEADERS, timeout=20)
        if r.status_code in (401, 403):
            _set_itad_error(r.status_code, _extract_reason(r))
        else:
            _set_itad_error(0, "")
        return r
    except Exception as exc:
        _set_itad_error(500, str(exc))
        return None


def _itad_post_request(url: str, params: dict, key: str, body):
    if not key:
        _set_itad_error(401, "Missing api key")
        return None
    try:
        req_params = dict(params)
        req_params["key"] = key
        r = requests.post(url, params=req_params, json=body, headers=HTTP_HEADERS, timeout=20)
        if r.status_code in (401, 403):
            _set_itad_error(r.status_code, _extract_reason(r))
        else:
            _set_itad_error(0, "")
        return r
    except Exception as exc:
        _set_itad_error(500, str(exc))
        return None


def _itad_public_post(url: str, body):
    """POST to a public ITAD endpoint that requires no API key."""
    try:
        r = requests.post(url, json=body, headers=HTTP_HEADERS, timeout=20)
        _set_itad_error(0, "")
        return r
    except Exception as exc:
        _set_itad_error(500, str(exc))
        return None


def get_itad_gid(appid: int, title: str, key: str = ""):
    """Resolve a game to an ITAD UUID.

    Uses the free (no-auth) public lookup endpoints first:
      1. POST /lookup/id/shop/{shopId}/v1  — lookup by Steam app ID (most reliable)
      2. POST /lookup/id/title/v1          — fallback lookup by title
    Both endpoints accept requests without an API key.
    The optional key param is kept for signature compatibility but is not used.
    """
    # --- Strategy 1: lookup by Steam shop ID (free, no key required) ---
    if appid:
        try:
            shop_ref = f"app/{int(appid)}"
            url = f"{ITAD_BASE_URL}/lookup/id/shop/{ITAD_STEAM_SHOP_ID}/v1"
            r = _itad_public_post(url, [shop_ref])
            if r and r.status_code == 200:
                payload = r.json()
                gid = payload.get(shop_ref) if isinstance(payload, dict) else None
                if gid:
                    _set_itad_error(0, "")
                    return gid
        except Exception as exc:
            _log(f"ITAD shop-id lookup failed: {exc}")

    # --- Strategy 2: lookup by game title (free, no key required) ---
    if title:
        try:
            url = f"{ITAD_BASE_URL}/lookup/id/title/v1"
            r = _itad_public_post(url, [title])
            if r and r.status_code == 200:
                payload = r.json()
                gid = payload.get(title) if isinstance(payload, dict) else None
                if gid:
                    _set_itad_error(0, "")
                    return gid
        except Exception as exc:
            _log(f"ITAD title lookup failed: {exc}")

    _set_itad_error(404, "Game not found in ITAD public lookup")
    return None


def _to_date(value):
    if not value:
        return ""
    s = _safe_str(value)
    return s[:10]


def normalize_bundle_item(raw: dict, source: str):
    # ITAD /games/bundles/v2 schema:
    #   id, title, page (shop info), url, details, publish (ISO str), expiry (ISO str), tiers
    title = raw.get("title") or raw.get("name") or "Unknown Bundle"
    # Platform / shop name comes from the "page" object
    page = raw.get("page") or raw.get("shop") or raw.get("store") or {}
    platform = ""
    if isinstance(page, dict):
        platform = page.get("name") or ""
    if not platform:
        platforms = raw.get("platforms")
        if isinstance(platforms, list) and platforms:
            platform = ", ".join([_safe_str(p) for p in platforms[:3]])
    # publish is an ISO 8601 datetime string, not a dict
    publish_raw = raw.get("publish") or raw.get("start") or raw.get("date") or raw.get("publishDate") or ""
    if isinstance(publish_raw, dict):
        # defensive: handle old/inconsistent shapes
        publish_raw = publish_raw.get("start") or publish_raw.get("date") or publish_raw.get("published") or ""
    date = _to_date(publish_raw)
    # For bundle platforms (Humble, Fanatical, etc.) DRM info is not provided by ITAD.
    # Use the platform name itself as the DRM hint, or fall back to "Steam".
    drm = _safe_str(raw.get("drm") or raw.get("activation") or platform or "Steam")
    return {
        "bundle_choice": f"{title} ({date})" if date else title,
        "platform": platform or source,
        "bundle_name": title,
        "drm": drm,
        "bundle_date": date,
        "source": source,
        "url": _safe_str(raw.get("url") or raw.get("details") or ""),
    }


def get_itad_bundles_by_gid(gid: str, key: str, country: str):
    if not gid:
        _set_itad_error(400, "Missing game id")
        return []
    if not key:
        _set_itad_error(401, "ITAD API key required for bundle data")
        return []
    cache_key = f"itad_bundles::{gid}::{country}"
    cache = _load_json(ITAD_CACHE_FILE, {"_ts": {}})
    ts = (cache.get("_ts") or {}).get(cache_key)
    if ts and (time.time() - ts) < ITAD_CACHE_TTL:
        cached = cache.get(cache_key)
        if isinstance(cached, list):
            return cached
    try:
        url = f"{ITAD_BASE_URL}/games/bundles/v2"
        # expired=true includes historical (expired) bundles, not just active ones
        params = {"id": gid, "country": country or "PT", "expired": "true"}
        r = _itad_request(url, params, key)
        if not r or r.status_code != 200:
            if r is not None:
                _set_itad_error(r.status_code, _extract_reason(r))
            return []
        payload = r.json()
        raw_items = payload if isinstance(payload, list) else payload.get("data") or payload.get("bundles") or []
        out = []
        for item in raw_items:
            if isinstance(item, dict):
                out.append(normalize_bundle_item(item, "ITAD"))
        uniq = []
        seen = set()
        for b in out:
            key_tuple = (b.get("bundle_name"), b.get("bundle_date"))
            if key_tuple in seen:
                continue
            seen.add(key_tuple)
            uniq.append(b)
        uniq.sort(key=lambda x: x.get("bundle_date") or "", reverse=True)
        cache[cache_key] = uniq
        cache.setdefault("_ts", {})[cache_key] = time.time()
        _save_json(ITAD_CACHE_FILE, cache)
        _set_itad_error(0, "")
        return uniq
    except Exception as exc:
        _set_itad_error(500, str(exc))
        _log(f"ITAD bundles failed: {exc}")
        return []


def _parse_barter_vg_html(html: str) -> list:
    """Parse bundle and special history from a barter.vg game page HTML response."""
    out = []

    provider_map = {
        "humblebundle": "Humble Bundle",
        "hb": "Humble Bundle",
        "fanatical": "Fanatical",
        "bundlestars": "Fanatical",
        "indiegala": "IndieGala",
        "greenmangaming": "Green Man Gaming",
        "gmg": "Green Man Gaming",
        "gamesplanet": "Gamesplanet",
        "gamersgate": "GamersGate",
        "wingamestore": "WinGameStore",
        "gog": "GOG",
        "epicgames": "Epic Games Store",
        "epicgamesstore": "Epic Games Store",
        "nvidia": "NVIDIA",
        "lootboy": "LootBoy",
        "oyvey2": "Oy Vey",
        "oyvey": "Oy Vey",
        "lequestore": "Leque Store",
        "steam": "Steam",
        "microsoftstore": "Microsoft Store",
        "amazon": "Amazon",
        "ubisoft": "Ubisoft Store",
        "ea": "EA App",
        "origin": "EA App",
    }

    def provider_from_slug(slug: str) -> str:
        s = _safe_str(slug).strip().lower()
        if not s:
            return "Barter.vg"
        if s in provider_map:
            return provider_map[s]
        # Fallback: convert unknown slugs like "some_store" -> "Some Store"
        human = s.replace("_", " ").replace("-", " ").strip()
        words = [w.capitalize() for w in human.split()]
        out_name = " ".join(words)
        if out_name == "Gmg":
            return "Green Man Gaming"
        if out_name == "Nvidia":
            return "NVIDIA"
        return out_name or "Barter.vg"

    # Locate every <h3> heading and record where each section starts and ends
    positions = []
    for m in re.finditer(r'<h3\b[^>]*>(.*?)</h3>', html, re.DOTALL):
        heading_text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        positions.append((m.start(), m.end(), heading_text))

    for i, (_, end_pos, heading) in enumerate(positions):
        if 'Bundle' not in heading and 'Special' not in heading:
            continue
        # Section content runs until the next h3 (or end of document)
        next_h3_start = positions[i + 1][0] if i + 1 < len(positions) else len(html)
        section_html = html[end_pos:next_h3_start]

        for tr_m in re.finditer(r'<tr\b[^>]*>(.*?)</tr>', section_html, re.DOTALL):
            row_html = tr_m.group(1)

            # Bundle link can be full URL (https://barter.vg/bundle/NNN/) or relative (/bundle/NNN/)
            link_m = re.search(r'href="(?:https://barter\.vg)?(/bundle/\d+/)"[^>]*>(.*?)</a>', row_html, re.DOTALL)
            if not link_m:
                continue

            bundle_href = link_m.group(1)
            link_html = link_m.group(2)
            # Strip img tags and other HTML from the link text to get the clean bundle name
            bundle_name = _html_unescape(re.sub(r'<[^>]+>', '', link_html)).strip()
            if not bundle_name:
                continue

            # The first icon inside the bundle anchor identifies the bundle provider.
            icon_m = re.search(r'/imgs/ico/([a-z0-9_\-]+)\.png', link_html, re.IGNORECASE)
            provider = provider_from_slug(icon_m.group(1) if icon_m else "")

            # Dates are in <td class="right"> cells.
            # The tier cell also has class="right" but contains "N of M" text, not a date.
            # End-date cells may wrap the date in <time class="remove">DATE</time>.
            # Strategy: take all class="right" cells, strip HTML, keep only pure YYYY-MM-DD values.
            right_tds = re.findall(r'<td\b[^>]*class="[^"]*right[^"]*"[^>]*>(.*?)</td>', row_html, re.DOTALL)
            pure_date_cells = []
            for td in right_tds:
                clean = re.sub(r'<[^>]+>', '', td).strip()
                if re.match(r'^\d{4}-\d{2}-\d{2}$', clean):
                    pure_date_cells.append(clean)

            if not pure_date_cells:
                continue  # Header row or row without dates — skip

            start_date = pure_date_cells[0]
            end_date = pure_date_cells[1] if len(pure_date_cells) > 1 else ""

            out.append(normalize_bundle_item(
                {
                    "title": bundle_name,
                    "publish": start_date,
                    "page": {"name": provider},
                    "url": f"https://barter.vg{bundle_href}",
                },
                "Barter.vg",
            ))

    # Deduplicate by bundle name, most recent first
    seen: set = set()
    unique = []
    for b in out:
        key = b.get("bundle_name", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(b)
    unique.sort(key=lambda x: x.get("bundle_date") or "", reverse=True)
    return unique


def get_barter_vg_bundles(appid: int) -> list:
    """Fetch bundle history from barter.vg. No authentication required."""
    if not appid:
        return []
    try:
        url = f"https://barter.vg/steam/app/{int(appid)}/"
        r = requests.get(url, headers=HTTP_HEADERS, timeout=25, allow_redirects=True)
        if r.status_code != 200:
            _log(f"barter.vg returned HTTP {r.status_code} for appid={appid}")
            return []
        return _parse_barter_vg_html(r.text)
    except Exception as exc:
        _log(f"barter.vg request failed (appid={appid}): {exc}")
        return []


def get_barter_bundles(appid: int, title: str, feed_url: str, auth_header: str):
    """Custom fallback bundle feed (user-configured URL)."""
    if not feed_url:
        return []
    url = feed_url.replace("{appid}", _safe_str(appid)).replace("{title}", requests.utils.quote(title or ""))
    headers = dict(HTTP_HEADERS)
    if auth_header:
        headers["Authorization"] = auth_header
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code != 200:
            return []
        payload = r.json()
        if isinstance(payload, dict):
            items = payload.get("data") or payload.get("bundles") or payload.get("list") or []
        else:
            items = payload
        out = []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    out.append(normalize_bundle_item(item, "Fallback"))
        return out
    except Exception as exc:
        _log(f"Fallback bundles failed: {exc}")
        return []


def _extract_price_amount(price_obj):
    if not isinstance(price_obj, dict):
        return None, ""
    amount = price_obj.get("amount")
    if amount is None and price_obj.get("amountInt") is not None:
        try:
            amount = float(price_obj.get("amountInt")) / 100.0
        except Exception:
            amount = None
    currency = _safe_str(price_obj.get("currency") or "").upper()
    return amount, currency


def get_itad_steam_lowest_prices(gid: str, key: str, country: str):
    if not gid or not key:
        return {"eur": "", "usd": ""}
    try:
        # POST /games/prices/v3 with shops=61 filters results to Steam only.
        # The top-level "historyLow" in each row is the Steam all-time low
        # for the requested country/currency.
        result = {"eur": "", "usd": ""}
        for cc, currency_key in (("PT", "eur"), ("US", "usd")):
            url = f"{ITAD_BASE_URL}/games/prices/v3"
            params = {"country": cc, "shops": str(ITAD_STEAM_SHOP_ID)}
            r = _itad_post_request(url, params, key, [gid])
            if not r or r.status_code != 200:
                _log(f"ITAD prices ({cc}) returned: {r.status_code if r else 'n/a'}")
                continue
            rows = r.json()
            if not isinstance(rows, list):
                rows = rows.get("data") or []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                hist = row.get("historyLow") or {}
                # historyLow is commonly nested as {"all": {...}, "y1": {...}}
                amount, currency = _extract_price_amount(hist)
                if amount is None and isinstance(hist, dict):
                    amount, currency = _extract_price_amount(hist.get("all") or {})
                if amount is not None:
                    result[currency_key] = _money(amount)
                    break
        return result
    except Exception as exc:
        _log(f"ITAD prices failed: {exc}")
        return {"eur": "", "usd": ""}


def get_itad_best_current_deal(gid: str, key: str, country: str):
    """Return the cheapest current deal (shop + price) for the configured country."""
    if not gid or not key:
        return {"shop": "", "price": ""}
    try:
        url = f"{ITAD_BASE_URL}/games/prices/v3"
        params = {"country": country or "PT"}
        r = _itad_post_request(url, params, key, [gid])
        if not r or r.status_code != 200:
            return {"shop": "", "price": ""}
        rows = r.json()
        if not isinstance(rows, list):
            rows = rows.get("data") or []

        best_amount = None
        best_currency = ""
        best_shop = ""
        for row in rows:
            if not isinstance(row, dict):
                continue
            for deal in row.get("deals") or []:
                if not isinstance(deal, dict):
                    continue
                amount, currency = _extract_price_amount(deal.get("price") or {})
                if amount is None:
                    continue
                shop_obj = deal.get("shop") or {}
                shop_name = _safe_str(shop_obj.get("name") if isinstance(shop_obj, dict) else "")
                if best_amount is None or amount < best_amount:
                    best_amount = amount
                    best_currency = currency
                    best_shop = shop_name

        if best_amount is None:
            return {"shop": "", "price": ""}
        price_text = f"{_money(best_amount)} {best_currency}".strip()
        return {"shop": best_shop, "price": price_text}
    except Exception as exc:
        _log(f"ITAD best deal failed: {exc}")
        return {"shop": "", "price": ""}


def get_itad_steam_current_prices(gid: str, key: str, country: str):
    """Return Steam current and regular prices for selected country when available."""
    if not gid or not key:
        return {"current": "", "regular": "", "currency": ""}
    try:
        url = f"{ITAD_BASE_URL}/games/prices/v3"
        params = {"country": country or "PT", "shops": str(ITAD_STEAM_SHOP_ID)}
        r = _itad_post_request(url, params, key, [gid])
        if not r or r.status_code != 200:
            return {"current": "", "regular": "", "currency": ""}
        rows = r.json()
        if not isinstance(rows, list):
            rows = rows.get("data") or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            for deal in row.get("deals") or []:
                if not isinstance(deal, dict):
                    continue
                shop_obj = deal.get("shop") or {}
                if (shop_obj.get("id") if isinstance(shop_obj, dict) else None) != ITAD_STEAM_SHOP_ID:
                    continue
                current, cur1 = _extract_price_amount(deal.get("price") or {})
                regular, cur2 = _extract_price_amount(deal.get("regular") or {})
                if current is None:
                    continue
                if regular is None:
                    regular = current
                return {
                    "current": _money(current),
                    "regular": _money(regular),
                    "currency": cur1 or cur2,
                }
        return {"current": "", "regular": "", "currency": ""}
    except Exception as exc:
        _log(f"ITAD Steam current prices failed: {exc}")
        return {"current": "", "regular": "", "currency": ""}


def ensure_game_defaults(game: dict):
    out = dict(game)
    out.setdefault("title", "")
    out.setdefault("appid", "")
    out.setdefault("bundle_choice", "")
    out.setdefault("platform", "")
    out.setdefault("bundle_name", "")
    out.setdefault("drm", "")
    out.setdefault("steam_regular_eur", "")
    out.setdefault("steam_regular_usd", "")
    out.setdefault("steam_lowest_eur", "")
    out.setdefault("steam_lowest_usd", "")
    out.setdefault("best_price_shop", "")
    out.setdefault("best_price_value", "")
    out.setdefault("bundle_date", "")
    out.setdefault("key", "")
    out.setdefault("keys", [])
    out.setdefault("status", "In Stock")
    out.setdefault("note", "")
    out.setdefault("image_url", "")
    out.setdefault("bundle_options", [])
    # migrate legacy single "key" field to the new "keys" list
    if out["key"] and not out["keys"]:
        out["keys"] = [{"code": out["key"], "key_status": "stock"}]
    return out


class SteamKeyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self._icon_image = None
        self.settings = load_settings()
        self.lang = self.settings.get("language", "en")
        self.games = [ensure_game_defaults(g) for g in self._load_initial_games()]
        self.applist = []
        self.selected_index = None
        self.current_palette = THEMES["steam"]
        self.tooltips = []
        self.detail_cover_image = None
        self.oauth_code_verifier = ""
        self.oauth_state = ""
        self.oauth_url = ""

        self.style = ttk.Style(self)
        self._apply_theme(self.settings.get("theme", "steam"))
        self._apply_app_icon()

        self.geometry("1400x860")
        self.minsize(1160, 720)

        self._build_ui()
        self._refresh_tree()
        self._load_applist_async()

    def _apply_app_icon(self):
        """Apply a custom icon for the title bar and Windows taskbar when available."""
        if not os.path.exists(APP_ICON_FILE):
            return
        try:
            # Windows taskbar and title icon path-based API.
            self.iconbitmap(APP_ICON_FILE)
        except Exception:
            pass
        try:
            # Fallback API used across Tk platforms.
            self._icon_image = ImageTk.PhotoImage(Image.open(APP_ICON_FILE))
            self.iconphoto(True, self._icon_image)
        except Exception:
            pass

    def t(self, key):
        pack = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])
        return pack.get(key, TRANSLATIONS["en"].get(key, key))

    def _load_initial_games(self):
        mode = _safe_str(self.settings.get("save_mode", "local"))
        cloud_url = _safe_str(self.settings.get("cloud_save_url", "")).strip()
        cloud_auth = _safe_str(self.settings.get("cloud_auth_header", "")).strip()

        if mode in ("cloud", "both") and cloud_url:
            remote_games, err = cloud_download_games(cloud_url, cloud_auth)
            if isinstance(remote_games, list):
                if mode == "both":
                    save_games(remote_games)
                return remote_games
            _log(f"Cloud load failed at startup: {err}")

        return load_games()

    def _persist_games(self, show_errors=True):
        mode = _safe_str(self.settings.get("save_mode", "local"))
        cloud_url = _safe_str(self.settings.get("cloud_save_url", "")).strip()
        cloud_auth = _safe_str(self.settings.get("cloud_auth_header", "")).strip()

        if mode in ("local", "both"):
            save_games(self.games)

        if mode in ("cloud", "both"):
            ok, err = cloud_upload_games(cloud_url, cloud_auth, self.games)
            if not ok and show_errors:
                messagebox.showwarning(self.t("warning"), f"{self.t('cloud_save_failed')}\n\n{err}")

    def cloud_upload_now(self):
        cloud_url = _safe_str(self.ent_cloud_url.get() if hasattr(self, "ent_cloud_url") else self.settings.get("cloud_save_url", "")).strip()
        cloud_auth = _safe_str(self.ent_cloud_auth.get() if hasattr(self, "ent_cloud_auth") else self.settings.get("cloud_auth_header", "")).strip()
        if not cloud_url:
            messagebox.showwarning(self.t("warning"), self.t("cloud_missing_url"))
            return
        ok, err = cloud_upload_games(cloud_url, cloud_auth, self.games)
        if ok:
            messagebox.showinfo(self.t("ok"), self.t("cloud_save_ok"))
        else:
            messagebox.showerror(self.t("error"), f"{self.t('cloud_save_failed')}\n\n{err}")

    def cloud_download_now(self):
        cloud_url = _safe_str(self.ent_cloud_url.get() if hasattr(self, "ent_cloud_url") else self.settings.get("cloud_save_url", "")).strip()
        cloud_auth = _safe_str(self.ent_cloud_auth.get() if hasattr(self, "ent_cloud_auth") else self.settings.get("cloud_auth_header", "")).strip()
        if not cloud_url:
            messagebox.showwarning(self.t("warning"), self.t("cloud_missing_url"))
            return
        remote_games, err = cloud_download_games(cloud_url, cloud_auth)
        if not isinstance(remote_games, list):
            messagebox.showerror(self.t("error"), f"{self.t('cloud_load_failed')}\n\n{err}")
            return
        self.games = [ensure_game_defaults(g) for g in remote_games]
        save_games(self.games)
        self.selected_index = None
        self._refresh_tree()
        self._clear_details()
        messagebox.showinfo(self.t("ok"), self.t("cloud_load_ok"))

    def _selected_currency(self):
        cur = _safe_str(self.settings.get("display_currency", "EUR")).upper()
        return cur if cur in ("EUR", "USD") else "EUR"

    def _game_price_value(self, game: dict, prefix: str):
        # prefix is one of: steam_regular, steam_lowest
        cur = self._selected_currency().lower()
        return _safe_str(game.get(f"{prefix}_{cur}") or "")

    def _set_detail_image(self, image_url: str):
        if not hasattr(self, "lbl_cover"):
            return
        if not image_url:
            self.detail_cover_image = None
            self.lbl_cover.configure(image="", text="")
            return
        try:
            r = requests.get(image_url, headers=HTTP_HEADERS, timeout=20)
            if r.status_code != 200:
                self.detail_cover_image = None
                self.lbl_cover.configure(image="", text="")
                return
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            img.thumbnail((320, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.detail_cover_image = photo
            self.lbl_cover.configure(image=photo, text="")
        except Exception:
            self.detail_cover_image = None
            self.lbl_cover.configure(image="", text="")

    def _apply_theme(self, theme_key):
        palette = THEMES.get(theme_key, THEMES["steam"])
        self.current_palette = palette
        bg = palette["bg"]
        sf = palette["surface"]
        sa = palette["surface_alt"]
        tx = palette["text"]
        muted = palette["muted"]
        accent = palette["accent"]

        self.configure(bg=bg)
        self.style.theme_use("clam")

        self.style.configure("TFrame", background=bg)
        self.style.configure("Surface.TFrame", background=sf)
        self.style.configure("AltSurface.TFrame", background=sa)
        self.style.configure("Card.TFrame", background=sf, relief="flat")
        self.style.configure("TLabel", background=bg, foreground=tx, font=("Segoe UI", 10))
        self.style.configure("Surface.TLabel", background=sf, foreground=tx, font=("Segoe UI", 10))
        self.style.configure("Muted.TLabel", background=sf, foreground=muted, font=("Segoe UI", 9))
        self.style.configure("Hero.TLabel", background=sf, foreground=tx, font=("Segoe UI Semibold", 20))
        self.style.configure("Section.TLabel", background=sf, foreground=tx, font=("Segoe UI Semibold", 12))
        self.style.configure("Help.TLabel", background=sf, foreground=accent, font=("Segoe UI Semibold", 10))
        self.style.configure(
            "TButton",
            background=sa,
            foreground=tx,
            borderwidth=0,
            focusthickness=0,
            padding=(12, 8),
            font=("Segoe UI Semibold", 10),
        )
        self.style.map("TButton", background=[("active", accent)])
        self.style.configure("Accent.TButton", background=accent, foreground="#ffffff")
        self.style.map("Accent.TButton", background=[("active", sa)])

        self.style.configure("Treeview", background=sf, fieldbackground=sf, foreground=tx, rowheight=28)
        self.style.configure("Treeview.Heading", background=sa, foreground=tx, font=("Segoe UI Semibold", 10))
        self.style.map("Treeview", background=[("selected", accent)], foreground=[("selected", "#ffffff")])

        self.style.configure("TNotebook", background=bg, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=sa, foreground=tx, padding=(14, 8), font=("Segoe UI Semibold", 10))
        self.style.map("TNotebook.Tab", background=[("selected", accent)], foreground=[("selected", "#ffffff")])

        self.style.configure("TCombobox", fieldbackground=sf, background=sa, foreground=tx, arrowcolor=tx)
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", sa), ("focus", sf)],
            foreground=[("readonly", tx), ("!disabled", tx)],
            selectbackground=[("readonly", accent)],
            selectforeground=[("readonly", "#ffffff")],
        )
        self.style.configure("TEntry", fieldbackground=sf, foreground=tx, insertcolor=tx)
        self.style.map(
            "TEntry",
            fieldbackground=[("readonly", sa), ("disabled", sa)],
            foreground=[("readonly", tx), ("disabled", muted)],
        )
        self.style.configure("TCheckbutton", background=sf, foreground=tx)
        self.style.map("TCheckbutton", background=[("active", sf)], foreground=[("active", tx)])

        self.option_add("*TCombobox*Listbox.background", sa)
        self.option_add("*TCombobox*Listbox.foreground", tx)
        self.option_add("*TCombobox*Listbox.selectBackground", accent)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    def _build_ui(self):
        self.title(self.t("title"))

        self.header = ttk.Frame(self, style="Surface.TFrame", padding=12)
        self.header.pack(fill="x")
        left_header = ttk.Frame(self.header, style="Surface.TFrame")
        left_header.pack(side="left", fill="x", expand=True)
        self.lbl_title = ttk.Label(left_header, text=self.t("title"), style="Hero.TLabel")
        self.lbl_title.pack(anchor="w")
        self.lbl_subtitle = ttk.Label(
            left_header,
            text=self.t("subtitle"),
            style="Muted.TLabel",
        )
        self.lbl_subtitle.pack(anchor="w", pady=(2, 0))
        self.lbl_status = ttk.Label(self.header, text=self.t("loading_catalog"), style="Muted.TLabel")
        self.lbl_status.pack(side="right", padx=(12, 4))

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_library = ttk.Frame(self.nb, style="TFrame")
        self.tab_settings = ttk.Frame(self.nb, style="TFrame")
        self.nb.add(self.tab_library, text=self.t("tab_library"))
        self.nb.add(self.tab_settings, text=self.t("tab_settings"))

        self._build_library_tab()
        self._build_settings_tab()

    def _build_library_tab(self):
        toolbar = ttk.Frame(self.tab_library, style="Surface.TFrame", padding=10)
        toolbar.pack(fill="x", pady=(0, 10))

        self.btn_add = ttk.Button(toolbar, text=self.t("add_game"), style="Accent.TButton", command=self.open_add_game_dialog)
        self.btn_add.pack(side="left", padx=(0, 8))
        self.btn_remove = ttk.Button(toolbar, text=self.t("remove_game"), command=self.remove_selected_game)
        self.btn_remove.pack(side="left")

        self.lbl_search = ttk.Label(toolbar, text=self.t("search"), style="Surface.TLabel")
        self.lbl_search.pack(side="left", padx=(18, 6))
        self.var_filter = tk.StringVar()
        self.ent_filter = ttk.Entry(toolbar, textvariable=self.var_filter, width=34)
        self.ent_filter.pack(side="left")
        self.var_filter.trace_add("write", lambda *_: self._refresh_tree())

        stats = ttk.Frame(toolbar, style="Surface.TFrame")
        stats.pack(side="right")
        self.lbl_stats = ttk.Label(stats, text="0 games", style="Muted.TLabel")
        self.lbl_stats.pack(side="right")

        body = ttk.Panedwindow(self.tab_library, orient="horizontal")
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body, style="Surface.TFrame", padding=8)
        right = ttk.Frame(body, style="Surface.TFrame", padding=12)
        body.add(left, weight=7)
        body.add(right, weight=4)
        self.after(50, lambda: body.sashpos(0, max(700, self.winfo_width() - 430)))

        columns = (
            "title",
            "bundle_choice",
            "platform",
            "bundle_name",
            "drm",
            "steam_regular",
            "steam_lowest",
            "best_price_shop",
            "best_price_value",
            "bundle_date",
            "status",
        )
        self.tree = ttk.Treeview(left, columns=columns, show="headings")
        self.tree.pack(fill="both", expand=True)
        x_scroll = ttk.Scrollbar(left, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=x_scroll.set)
        x_scroll.pack(fill="x", side="bottom")
        self.tree.bind("<<TreeviewSelect>>", self.on_select_game)
        self.tree.tag_configure("even", background=self.current_palette["surface"])
        self.tree.tag_configure("odd", background=self.current_palette["surface_alt"])

        headings = {
            "title": self.t("game"),
            "bundle_choice": self.t("bundle_dropdown"),
            "platform": self.t("platform"),
            "bundle_name": self.t("bundle_name"),
            "drm": self.t("drm"),
            "steam_regular": f"{self.t('steam_regular')} {self._selected_currency()}",
            "steam_lowest": f"{self.t('steam_lowest')} {self._selected_currency()}",
            "best_price_shop": self.t("best_price_shop"),
            "best_price_value": self.t("best_price_value"),
            "bundle_date": self.t("bundle_date"),
            "status": self.t("status"),
        }
        widths = {
            "title": 220,
            "bundle_choice": 240,
            "platform": 140,
            "bundle_name": 170,
            "drm": 90,
            "steam_regular": 95,
            "steam_lowest": 95,
            "best_price_shop": 140,
            "best_price_value": 110,
            "bundle_date": 100,
            "status": 90,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        self._build_details_panel(right)

    def _build_details_panel(self, parent):
        self.lbl_details_title = ttk.Label(parent, text=self.t("details"), style="Section.TLabel")
        self.lbl_details_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.lbl_cover = ttk.Label(parent, style="Surface.TLabel", anchor="center")
        self.lbl_cover.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.var_title = tk.StringVar()
        self.var_bundle_choice = tk.StringVar()
        self.var_platform = tk.StringVar()
        self.var_bundle_name = tk.StringVar()
        self.var_drm = tk.StringVar()
        self.var_regular = tk.StringVar()
        self.var_lowest = tk.StringVar()
        self.var_best_price_shop = tk.StringVar()
        self.var_best_price_value = tk.StringVar()
        self.var_bundle_date = tk.StringVar()
        self.var_status = tk.StringVar(value="In Stock")
        self.var_note = tk.StringVar()

        row = 2
        row = self._detail_entry(parent, row, self.t("game_name"), self.var_title, readonly=True)

        ttk.Label(parent, text=self.t("bundle_dropdown"), style="Surface.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        self.cmb_bundle = ttk.Combobox(parent, textvariable=self.var_bundle_choice, state="readonly")
        self.cmb_bundle.grid(row=row, column=1, sticky="ew", pady=4)
        self.cmb_bundle.bind("<<ComboboxSelected>>", self.on_bundle_change)
        row += 1

        row = self._detail_entry(parent, row, self.t("platform"), self.var_platform, readonly=True)
        row = self._detail_entry(parent, row, self.t("bundle_name"), self.var_bundle_name, readonly=True)
        row = self._detail_entry(parent, row, self.t("drm"), self.var_drm, readonly=True)
        row = self._detail_entry(parent, row, self.t("steam_regular"), self.var_regular, readonly=True)
        row = self._detail_entry(parent, row, self.t("steam_lowest"), self.var_lowest, readonly=True)
        row = self._detail_entry(parent, row, self.t("best_price_shop"), self.var_best_price_shop, readonly=True)
        row = self._detail_entry(parent, row, self.t("best_price_value"), self.var_best_price_value, readonly=True)
        row = self._detail_entry(parent, row, self.t("bundle_date"), self.var_bundle_date, readonly=True)

        ttk.Label(parent, text=self.t("status"), style="Surface.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        self.ent_status = ttk.Entry(parent, textvariable=self.var_status, state="readonly")
        self.ent_status.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        ttk.Label(parent, text=self.t("note"), style="Surface.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        self.ent_note = ttk.Entry(parent, textvariable=self.var_note)
        self.ent_note.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        self._build_keys_widget(parent, row)
        # keys widget uses: header row, list row, add-row
        row += 3

        actions = ttk.Frame(parent, style="Surface.TFrame")
        actions.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.btn_save_changes = ttk.Button(actions, text=self.t("save_changes"), style="Accent.TButton", command=self.save_current_changes)
        self.btn_save_changes.pack(side="right")

        parent.columnconfigure(1, weight=1)

    def _detail_entry(self, parent, row, label, var, readonly=False):
        ttk.Label(parent, text=label, style="Surface.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        state = "readonly" if readonly else "normal"
        ttk.Entry(parent, textvariable=var, state=state).grid(row=row, column=1, sticky="ew", pady=4)
        return row + 1

    def _build_settings_tab(self):
        panel = ttk.Frame(self.tab_settings, style="Surface.TFrame", padding=16)
        panel.pack(fill="both", expand=True)

        self.lbl_general_title = ttk.Label(panel, text=self.t("general"), style="Section.TLabel")
        self.lbl_general_title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(panel, text=self.t("theme"), style="Surface.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.cmb_theme = ttk.Combobox(panel, state="readonly", values=list(THEMES.keys()))
        self.cmb_theme.set(self.settings.get("theme", "steam"))
        self.cmb_theme.grid(row=1, column=1, sticky="ew", pady=6)
        self._add_help_icon(panel, 1, 2, lambda: self.t("tooltip_theme"))

        ttk.Label(panel, text=self.t("language"), style="Surface.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        self.cmb_lang = ttk.Combobox(panel, state="readonly", values=["en", "pt-PT"])
        self.cmb_lang.set(self.settings.get("language", "en"))
        self.cmb_lang.grid(row=2, column=1, sticky="ew", pady=6)
        self._add_help_icon(panel, 2, 2, lambda: self.t("tooltip_language"))

        ttk.Label(panel, text=self.t("currency"), style="Surface.TLabel").grid(row=3, column=0, sticky="w", pady=6)
        self.cmb_currency = ttk.Combobox(panel, state="readonly", values=["EUR", "USD"])
        self.cmb_currency.set(_safe_str(self.settings.get("display_currency", "EUR")).upper())
        self.cmb_currency.grid(row=3, column=1, sticky="ew", pady=6)
        self._add_help_icon(panel, 3, 2, lambda: self.t("tooltip_currency"))

        ttk.Separator(panel).grid(row=4, column=0, columnspan=3, sticky="ew", pady=12)
        self.lbl_providers_title = ttk.Label(panel, text=self.t("providers"), style="Section.TLabel")
        self.lbl_providers_title.grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(panel, text=self.t("itad_key"), style="Surface.TLabel").grid(row=6, column=0, sticky="w", pady=6)
        self.ent_itad_key = ttk.Entry(panel)
        self.ent_itad_key.insert(0, self.settings.get("ITAD_API_KEY", ""))
        self.ent_itad_key.grid(row=6, column=1, sticky="ew", pady=6)
        self._add_help_icon(panel, 6, 2, lambda: self.t("tooltip_itad_key"))

        lbl_itad_info = ttk.Label(panel, text=self.t("itad_key_info"), style="Muted.TLabel", wraplength=420, justify="left")
        lbl_itad_info.grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(panel, text=self.t("itad_country"), style="Surface.TLabel").grid(row=8, column=0, sticky="w", pady=6)
        self.ent_itad_country = ttk.Entry(panel)
        self.ent_itad_country.insert(0, self.settings.get("ITAD_COUNTRY", "PT"))
        self.ent_itad_country.grid(row=8, column=1, sticky="ew", pady=6)
        self._add_help_icon(panel, 8, 2, lambda: self.t("tooltip_itad_country"))

        self.var_fallback_enabled = tk.BooleanVar(value=bool(self.settings.get("fallback_enabled", False)))
        ttk.Checkbutton(panel, text=self.t("fallback"), variable=self.var_fallback_enabled).grid(row=9, column=0, columnspan=2, sticky="w", pady=6)
        self._add_help_icon(panel, 9, 2, lambda: self.t("tooltip_fallback"))

        ttk.Label(panel, text=self.t("fallback_url"), style="Surface.TLabel").grid(row=10, column=0, sticky="w", pady=6)
        self.ent_fallback_url = ttk.Entry(panel)
        self.ent_fallback_url.insert(0, self.settings.get("fallback_url", ""))
        self.ent_fallback_url.grid(row=10, column=1, sticky="ew", pady=6)
        self._add_help_icon(panel, 10, 2, lambda: self.t("tooltip_fallback_url"))

        ttk.Label(panel, text=self.t("fallback_auth"), style="Surface.TLabel").grid(row=11, column=0, sticky="w", pady=6)
        self.ent_fallback_auth = ttk.Entry(panel)
        self.ent_fallback_auth.insert(0, self.settings.get("fallback_auth", ""))
        self.ent_fallback_auth.grid(row=11, column=1, sticky="ew", pady=6)
        self._add_help_icon(panel, 11, 2, lambda: self.t("tooltip_fallback_auth"))

        ttk.Separator(panel).grid(row=12, column=0, columnspan=3, sticky="ew", pady=12)
        self.lbl_cloud_title = ttk.Label(panel, text=self.t("cloud"), style="Section.TLabel")
        self.lbl_cloud_title.grid(row=13, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(panel, text=self.t("save_mode"), style="Surface.TLabel").grid(row=14, column=0, sticky="w", pady=6)
        self.save_mode_map = {
            self.t("save_mode_local"): "local",
            self.t("save_mode_cloud"): "cloud",
            self.t("save_mode_both"): "both",
        }
        self.cmb_save_mode = ttk.Combobox(panel, state="readonly", values=list(self.save_mode_map.keys()))
        current_mode = _safe_str(self.settings.get("save_mode", "local"))
        current_label = next((label for label, value in self.save_mode_map.items() if value == current_mode), self.t("save_mode_local"))
        self.cmb_save_mode.set(current_label)
        self.cmb_save_mode.grid(row=14, column=1, sticky="ew", pady=6)
        self._add_help_icon(panel, 14, 2, lambda: self.t("tooltip_save_mode"))
        self.cmb_save_mode.bind("<<ComboboxSelected>>", lambda _e: self._on_save_mode_changed())

        self.lbl_cloud_url = ttk.Label(panel, text=self.t("cloud_url"), style="Surface.TLabel")
        self.lbl_cloud_url.grid(row=15, column=0, sticky="w", pady=6)
        self.ent_cloud_url = ttk.Entry(panel)
        self.ent_cloud_url.insert(0, self.settings.get("cloud_save_url", ""))
        self.ent_cloud_url.grid(row=15, column=1, sticky="ew", pady=6)

        self.lbl_cloud_auth = ttk.Label(panel, text=self.t("cloud_auth"), style="Surface.TLabel")
        self.lbl_cloud_auth.grid(row=16, column=0, sticky="w", pady=6)
        self.ent_cloud_auth = ttk.Entry(panel)
        self.ent_cloud_auth.insert(0, self.settings.get("cloud_auth_header", ""))
        self.ent_cloud_auth.grid(row=16, column=1, sticky="ew", pady=6)

        self.frm_cloud_actions = ttk.Frame(panel, style="Surface.TFrame")
        self.frm_cloud_actions.grid(row=17, column=1, sticky="w", pady=(4, 0))
        self.btn_cloud_download = ttk.Button(self.frm_cloud_actions, text=self.t("cloud_download"), command=self.cloud_download_now)
        self.btn_cloud_download.pack(side="left", padx=(0, 8))
        self.btn_cloud_upload = ttk.Button(self.frm_cloud_actions, text=self.t("cloud_upload"), command=self.cloud_upload_now)
        self.btn_cloud_upload.pack(side="left")
        self.btn_cloud_tutorial = ttk.Button(
            self.frm_cloud_actions,
            text=self.t("cloud_jsonbin_tutorial_btn"),
            command=self.show_jsonbin_tutorial,
        )
        self.btn_cloud_tutorial.pack(side="left", padx=(8, 0))

        # Apply initial visibility based on saved save_mode
        self._on_save_mode_changed()

        self.btn_save_settings = ttk.Button(panel, text=self.t("save_settings"), style="Accent.TButton", command=self.save_settings_from_ui)
        self.btn_save_settings.grid(row=18, column=1, sticky="e", pady=(16, 0))

        self.btn_validate_itad = ttk.Button(panel, text=self.t("validate_itad"), command=self.validate_itad_key)
        self.btn_validate_itad.grid(row=18, column=0, sticky="w", pady=(16, 0))

        panel.columnconfigure(1, weight=1)

    def validate_itad_key(self):
        key = (self.ent_itad_key.get().strip() if hasattr(self, "ent_itad_key") else self.settings.get("ITAD_API_KEY", "").strip())
        if not key:
            messagebox.showwarning(self.t("warning"), self.t("itad_key_missing"))
            return
        # Step 1: look up Dota 2 GID via the free public endpoint
        gid = get_itad_gid(570, "Dota 2")
        if not gid:
            reason = ITAD_LAST_ERROR or "Network error during GID lookup"
            messagebox.showerror(self.t("error"), f"Could not look up test game: {reason}")
            return
        # Step 2: call a key-required endpoint (bundles) to verify the key
        try:
            url = f"{ITAD_BASE_URL}/games/bundles/v2"
            params = {"id": gid, "key": key}
            r = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=15)
            if r.status_code == 200:
                messagebox.showinfo(self.t("ok"), f"ITAD key is valid. Test GID: {gid}")
            else:
                reason = _extract_reason(r)
                messagebox.showerror(self.t("error"), f"{self.t('itad_key_invalid')} (HTTP {r.status_code})\n{reason}")
        except Exception as exc:
            messagebox.showerror(self.t("error"), f"Network error: {exc}")

    def show_jsonbin_tutorial(self):
        dlg = tk.Toplevel(self)
        dlg.title(self.t("cloud_jsonbin_tutorial_title"))
        dlg.transient(self)
        dlg.grab_set()
        dlg.geometry("720x420")
        dlg.minsize(560, 320)
        dlg.configure(bg=self.current_palette["surface"])

        wrap = ttk.Frame(dlg, style="Surface.TFrame", padding=12)
        wrap.pack(fill="both", expand=True)

        text_frame = ttk.Frame(wrap, style="Surface.TFrame")
        text_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        tutorial_text = tk.Text(
            text_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            bg=self.current_palette["surface_alt"],
            fg=self.current_palette["text"],
            insertbackground=self.current_palette["text"],
            selectbackground=self.current_palette["accent"],
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10,
        )
        scrollbar.config(command=tutorial_text.yview)
        tutorial_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tutorial_body = self.t("cloud_jsonbin_tutorial_body")
        tutorial_text.insert("1.0", tutorial_body)
        tutorial_text.config(state="disabled")

        def copy_tutorial(event=None):
            try:
                text_to_copy = tutorial_text.get("sel.first", "sel.last")
            except tk.TclError:
                text_to_copy = tutorial_body
            self.clipboard_clear()
            self.clipboard_append(text_to_copy)
            return "break"

        def select_all(event=None):
            tutorial_text.tag_add("sel", "1.0", "end-1c")
            tutorial_text.mark_set("insert", "1.0")
            tutorial_text.see("insert")
            return "break"

        tutorial_text.bind("<Control-c>", copy_tutorial)
        tutorial_text.bind("<Control-C>", copy_tutorial)
        tutorial_text.bind("<Control-a>", select_all)
        tutorial_text.bind("<Control-A>", select_all)
        tutorial_text.focus_set()

        actions = ttk.Frame(wrap, style="Surface.TFrame")
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text=self.t("copy_text"), command=copy_tutorial).pack(side="left")
        ttk.Button(actions, text=self.t("close"), command=dlg.destroy).pack(side="right")

    def _add_help_icon(self, parent, row, col, text):
        help_lbl = ttk.Label(parent, text="(?)", style="Help.TLabel", cursor="hand2")
        help_lbl.grid(row=row, column=col, sticky="w", padx=(8, 0))
        self.tooltips.append(InfoTooltip(self, help_lbl, text, self.current_palette))

    # ------------------------------------------------------------------ keys
    _KEY_STATUS_ICONS = {"stock": "◻", "sold": "✓", "listed": "🛒"}
    _KEY_STATUS_ORDER = ["stock", "sold", "listed"]

    def _key_status_icon(self, key_status: str) -> str:
        return self._KEY_STATUS_ICONS.get(key_status, "◻")

    def _build_keys_widget(self, parent, start_row):
        """Builds the multi-key section spanning both columns in the details grid."""
        self._key_row_data = []

        # header: label + (?) tooltip
        hdr = ttk.Frame(parent, style="Surface.TFrame")
        hdr.grid(row=start_row, column=0, columnspan=2, sticky="ew", pady=(8, 2))
        self.lbl_keys_section = ttk.Label(hdr, text=self.t("keys_section"), style="Surface.TLabel")
        self.lbl_keys_section.pack(side="left")
        help_lbl = ttk.Label(hdr, text="(?)", style="Help.TLabel", cursor="hand2")
        help_lbl.pack(side="left", padx=(6, 0))
        self.tooltips.append(InfoTooltip(self, help_lbl, lambda: self.t("tooltip_keys"), self.current_palette))

        # container for individual key rows
        self.frm_keys_list = ttk.Frame(parent, style="Surface.TFrame")
        self.frm_keys_list.grid(row=start_row + 1, column=0, columnspan=2, sticky="ew")

        # add-key row
        add_row = ttk.Frame(parent, style="Surface.TFrame")
        add_row.grid(row=start_row + 2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.ent_new_key = ttk.Entry(add_row, font=("Consolas", 10))
        self.ent_new_key.pack(side="left", fill="x", expand=True)
        self.ent_new_key.bind("<Return>", lambda _e: self._add_key_row_from_entry())
        self.btn_add_key = ttk.Button(add_row, text=self.t("add_key"), command=self._add_key_row_from_entry)
        self.btn_add_key.pack(side="left", padx=(4, 0))

    def _add_key_display_row(self, code: str, key_status: str):
        palette = self.current_palette
        row_frame = tk.Frame(self.frm_keys_list, bg=palette["surface"])
        row_frame.pack(fill="x", pady=2)

        status_state = {"value": key_status}

        def cycle_status():
            idx = self._KEY_STATUS_ORDER.index(status_state["value"])
            status_state["value"] = self._KEY_STATUS_ORDER[(idx + 1) % 3]
            status_btn.config(text=self._key_status_icon(status_state["value"]))
            self._refresh_status_from_widget()

        status_btn = tk.Button(
            row_frame,
            text=self._key_status_icon(key_status),
            width=3,
            command=cycle_status,
            bg=palette["surface_alt"],
            fg=palette["text"],
            activebackground=palette["accent"],
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI Emoji", 11),
            cursor="hand2",
        )
        status_btn.pack(side="left", padx=(0, 4))

        visible_state = {"visible": False, "code": code}
        code_var = tk.StringVar(value=self._masked_key(code))
        lbl_key = tk.Label(
            row_frame,
            textvariable=code_var,
            bg=palette["surface"],
            fg=palette["text"],
            font=("Consolas", 10),
            anchor="w",
        )
        lbl_key.pack(side="left", fill="x", expand=True, padx=(0, 4))

        def toggle_visibility():
            if visible_state["visible"]:
                code_var.set(self._masked_key(visible_state["code"]))
                toggle_btn.config(text=self.t("show_key"))
                visible_state["visible"] = False
            else:
                code_var.set(visible_state["code"])
                toggle_btn.config(text=self.t("hide_key"))
                visible_state["visible"] = True

        toggle_btn = ttk.Button(row_frame, text=self.t("show_key"), command=toggle_visibility)
        toggle_btn.pack(side="left", padx=(0, 4))

        row_data = {"frame": row_frame, "status_state": status_state, "visible_state": visible_state, "code_var": code_var}

        def remove_key():
            if not messagebox.askyesno(self.t("confirm_remove_key_title"), self.t("confirm_remove_key"), default="no"):
                return
            if row_data in self._key_row_data:
                self._key_row_data.remove(row_data)
            row_frame.destroy()
            self._refresh_status_from_widget()

        remove_btn = ttk.Button(row_frame, text="✕", width=3, command=remove_key)
        remove_btn.pack(side="right")

        self._key_row_data.append(row_data)

    def _add_key_row_from_entry(self):
        code = self.ent_new_key.get().strip()
        if not code:
            return
        self._add_key_display_row(code, "stock")
        self.ent_new_key.delete(0, tk.END)
        self._refresh_status_from_widget()

    def _status_from_keys(self, keys: list) -> str:
        """Return game status derived strictly from key states."""
        if keys and all(_safe_str(k.get("key_status", "stock")) == "sold" for k in keys):
            return "Sold"
        return "In Stock"

    def _refresh_status_from_widget(self):
        self.var_status.set(self._status_from_keys(self._collect_keys()))

    def _collect_keys(self) -> list:
        keys = []
        for row in self._key_row_data:
            code = row["visible_state"]["code"].strip()
            if code:
                keys.append({"code": code, "key_status": row["status_state"]["value"]})
        return keys

    def _clear_keys_widget(self):
        """Destroy all existing key rows from the keys list frame."""
        if hasattr(self, "frm_keys_list"):
            for child in self.frm_keys_list.winfo_children():
                child.destroy()
        if hasattr(self, "_key_row_data"):
            self._key_row_data.clear()
        if hasattr(self, "ent_new_key"):
            self.ent_new_key.delete(0, tk.END)

    def _on_save_mode_changed(self):
        """Show or hide cloud URL/auth/action widgets depending on the selected save mode."""
        if not hasattr(self, "cmb_save_mode"):
            return
        mode_label = self.cmb_save_mode.get()
        mode = self.save_mode_map.get(mode_label, "local") if hasattr(self, "save_mode_map") else "local"
        cloud_visible = mode in ("cloud", "both")
        cloud_widgets = [
            getattr(self, w, None) for w in (
                "lbl_cloud_url", "ent_cloud_url",
                "lbl_cloud_auth", "ent_cloud_auth",
                "frm_cloud_actions",
            )
        ]
        for w in cloud_widgets:
            if w is None:
                continue
            if cloud_visible:
                w.grid()
            else:
                w.grid_remove()

    def _load_applist_async(self):
        def worker():
            apps = get_steam_applist()
            self.after(0, lambda: self._on_applist_loaded(apps))

        threading.Thread(target=worker, daemon=True).start()

    def _on_applist_loaded(self, apps):
        self.applist = apps
        self.lbl_status.config(text=self.t("ready"))

    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        filter_text = (self.var_filter.get().strip().lower() if hasattr(self, "var_filter") else "")
        visible = []
        for index, game in enumerate(self.games):
            g = ensure_game_defaults(game)
            self.games[index] = g
            if filter_text:
                hay = " ".join(
                    [
                        _safe_str(g.get("title")),
                        _safe_str(g.get("bundle_choice")),
                        _safe_str(g.get("platform")),
                        _safe_str(g.get("bundle_name")),
                    ]
                ).lower()
                if filter_text not in hay:
                    continue
            visible.append(index)

        for row_no, index in enumerate(visible):
            g = self.games[index]
            values = (
                g.get("title"),
                g.get("bundle_choice"),
                g.get("platform"),
                g.get("bundle_name"),
                g.get("drm"),
                self._game_price_value(g, "steam_regular"),
                self._game_price_value(g, "steam_lowest"),
                g.get("best_price_shop"),
                g.get("best_price_value"),
                g.get("bundle_date"),
                g.get("status"),
            )
            tag = "even" if row_no % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=str(index), values=values, tags=(tag,))

        if hasattr(self, "lbl_stats"):
            total = len(self.games)
            stock = len([g for g in self.games if _safe_str(g.get("status")) == "In Stock"])
            sold = total - stock
            if self.lang == "pt-PT":
                self.lbl_stats.config(text=f"{total} jogos | {stock} em stock | {sold} vendidos")
            else:
                self.lbl_stats.config(text=f"{total} games | {stock} in stock | {sold} sold")

    def on_select_game(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        self.selected_index = idx
        game = ensure_game_defaults(self.games[idx])
        self.games[idx] = game

        self.var_title.set(game.get("title", ""))
        self.var_platform.set(game.get("platform", ""))
        self.var_bundle_name.set(game.get("bundle_name", ""))
        self.var_drm.set(game.get("drm", ""))
        self.var_regular.set(self._game_price_value(game, "steam_regular"))
        self.var_lowest.set(self._game_price_value(game, "steam_lowest"))
        self.var_best_price_shop.set(game.get("best_price_shop", ""))
        self.var_best_price_value.set(game.get("best_price_value", ""))
        self.var_bundle_date.set(game.get("bundle_date", ""))
        self.var_note.set(game.get("note", ""))
        self._set_detail_image(game.get("image_url", ""))
        # populate multi-key widget
        self._clear_keys_widget()
        for k in game.get("keys", []):
            self._add_key_display_row(_safe_str(k.get("code", "")), _safe_str(k.get("key_status", "stock")))
        game["status"] = self._status_from_keys(game.get("keys", []))
        self.var_status.set(game["status"])

        options = game.get("bundle_options") or []
        labels = [o.get("bundle_choice", "") for o in options if o.get("bundle_choice")]
        if not labels and game.get("bundle_choice"):
            labels = [game.get("bundle_choice")]
        self.cmb_bundle["values"] = labels
        self.var_bundle_choice.set(game.get("bundle_choice", ""))

    def _masked_key(self, key: str):
        key = _safe_str(key)
        if not key:
            return ""
        # Hide the entire key by default, preserving separators like '-'.
        return "".join("-" if ch == "-" else "*" for ch in key)

    def on_bundle_change(self, _event=None):
        if self.selected_index is None:
            return
        game = self.games[self.selected_index]
        target = self.var_bundle_choice.get()
        for option in game.get("bundle_options", []):
            if option.get("bundle_choice") == target:
                self.var_platform.set(option.get("platform", ""))
                self.var_bundle_name.set(option.get("bundle_name", ""))
                self.var_drm.set(option.get("drm", ""))
                self.var_bundle_date.set(option.get("bundle_date", ""))
                return

    def save_current_changes(self):
        if self.selected_index is None:
            return
        game = ensure_game_defaults(self.games[self.selected_index])
        game["bundle_choice"] = self.var_bundle_choice.get()
        game["platform"] = self.var_platform.get()
        game["bundle_name"] = self.var_bundle_name.get()
        game["drm"] = self.var_drm.get()
        game["bundle_date"] = self.var_bundle_date.get()
        game["note"] = self.var_note.get()
        game["keys"] = self._collect_keys()
        game["status"] = self._status_from_keys(game["keys"])
        self.var_status.set(game["status"])

        self.games[self.selected_index] = game
        self._persist_games()
        self._refresh_tree()
        self.tree.selection_set(str(self.selected_index))
        self.tree.see(str(self.selected_index))

    def remove_selected_game(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        game_name = _safe_str(self.games[idx].get("title", "")).strip() or f"#{idx + 1}"
        msg = self.t("confirm_remove").format(name=game_name)
        if not messagebox.askyesno(self.t("confirm_remove_title"), msg, default="no"):
            return
        del self.games[idx]
        self._persist_games()
        self.selected_index = None
        self._refresh_tree()
        self._clear_details()
        messagebox.showinfo(self.t("ok"), self.t("removed_game"))

    def _clear_details(self):
        self.var_title.set("")
        self.var_bundle_choice.set("")
        self.cmb_bundle["values"] = []
        self.var_platform.set("")
        self.var_bundle_name.set("")
        self.var_drm.set("")
        self.var_regular.set("")
        self.var_lowest.set("")
        self.var_best_price_shop.set("")
        self.var_best_price_value.set("")
        self.var_bundle_date.set("")
        self.var_status.set("In Stock")
        self.var_note.set("")
        self._set_detail_image("")
        self._clear_keys_widget()

    def open_add_game_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title(self.t("add_dialog_title"))
        dlg.transient(self)
        dlg.grab_set()
        dlg.geometry("780x620")
        dlg.configure(bg=THEMES[self.settings.get("theme", "steam")]["surface"])

        wrap = ttk.Frame(dlg, style="Surface.TFrame", padding=12)
        wrap.pack(fill="both", expand=True)

        palette = self.current_palette

        ttk.Label(wrap, text=self.t("game_name"), style="Surface.TLabel").grid(row=0, column=0, sticky="w")
        ent_name = ttk.Entry(wrap)
        ent_name.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        name_help = ttk.Label(wrap, text="(?)", style="Help.TLabel", cursor="hand2")
        name_help.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.tooltips.append(
            InfoTooltip(
                self,
                name_help,
                "Type the exact game name.\nTip: choose one suggestion with AppID for better bundle and price accuracy.",
                palette,
            )
        )

        ttk.Label(wrap, text=self.t("key_code"), style="Surface.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ent_key = ttk.Entry(wrap)
        ent_key.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        key_help = ttk.Label(wrap, text="(?)", style="Help.TLabel", cursor="hand2")
        key_help.grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(8, 0))
        self.tooltips.append(
            InfoTooltip(
                self,
                key_help,
                "Paste your Steam key code for this game.\nCommon format: XXXXX-XXXXX-XXXXX.",
                palette,
            )
        )

        ttk.Label(wrap, text=self.t("suggestions"), style="Surface.TLabel").grid(row=2, column=0, sticky="w", pady=(10, 0))
        list_suggestions = tk.Listbox(
            wrap,
            height=8,
            bg=palette["surface_alt"],
            fg=palette["text"],
            selectbackground=palette["accent"],
            selectforeground="#ffffff",
            highlightthickness=0,
            relief="flat",
        )
        list_suggestions.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(4, 0))

        state = {
            "appid": None,
            "steam_title": "",
            "image_url": "",
            "price_data": {},
            "bundle_options": [],
            "history_low": {"eur": "", "usd": ""},
        }

        frame_bundle = ttk.Frame(wrap, style="AltSurface.TFrame", padding=10)
        frame_bundle.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(frame_bundle, text=self.t("bundle_dropdown"), style="Surface.TLabel").grid(row=0, column=0, sticky="w")
        var_bundle_choice = tk.StringVar()
        cmb_bundle = ttk.Combobox(frame_bundle, textvariable=var_bundle_choice, state="readonly")
        cmb_bundle.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        bundle_help = ttk.Label(frame_bundle, text="(?)", style="Help.TLabel", cursor="hand2")
        bundle_help.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.tooltips.append(
            InfoTooltip(
                self,
                bundle_help,
                "After clicking 'Fetch Online Data', choose the bundle where you got the key.\nSelecting a bundle auto-fills platform, DRM and date.",
                palette,
            )
        )

        detail_vars = {
            "platform": tk.StringVar(),
            "bundle_name": tk.StringVar(),
            "drm": tk.StringVar(),
            "steam_regular": tk.StringVar(),
            "steam_lowest": tk.StringVar(),
            "best_price_shop": tk.StringVar(),
            "best_price_value": tk.StringVar(),
            "bundle_date": tk.StringVar(),
        }

        row = 1
        for key in [
            "platform",
            "bundle_name",
            "drm",
            "steam_regular",
            "steam_lowest",
            "best_price_shop",
            "best_price_value",
            "bundle_date",
        ]:
            ttk.Label(frame_bundle, text=self.t(key), style="Surface.TLabel").grid(row=row, column=0, sticky="w", pady=3)
            ttk.Entry(frame_bundle, textvariable=detail_vars[key], state="readonly").grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=3)
            row += 1

        frame_bundle.columnconfigure(1, weight=1)

        def on_suggestion_key(_event=None):
            query = ent_name.get().strip()
            list_suggestions.delete(0, tk.END)
            if not query:
                return
            if not self.applist:
                list_suggestions.insert(tk.END, self.t("catalog_loading_wait"))
                return
            for name, appid in search_steam_suggestions(query, self.applist, limit=12):
                list_suggestions.insert(tk.END, f"{name} (AppID: {appid})")

        def on_pick_suggestion(_event=None):
            sel = list_suggestions.curselection()
            if not sel:
                return
            value = list_suggestions.get(sel[0])
            if "(AppID:" not in value:
                return
            name = value[: value.rfind(" (AppID:")]
            appid_txt = value[value.rfind(":") + 1 : -1].strip()
            ent_name.delete(0, tk.END)
            ent_name.insert(0, name)
            try:
                state["appid"] = int(appid_txt)
            except Exception:
                state["appid"] = None

        def update_bundle_preview(choice_label):
            found = None
            for item in state["bundle_options"]:
                if item.get("bundle_choice") == choice_label:
                    found = item
                    break
            if not found:
                return
            detail_vars["platform"].set(found.get("platform", ""))
            detail_vars["bundle_name"].set(found.get("bundle_name", ""))
            detail_vars["drm"].set(found.get("drm", ""))
            detail_vars["bundle_date"].set(found.get("bundle_date", ""))
            currency = self._selected_currency().lower()
            detail_vars["steam_regular"].set(state["price_data"].get(f"regular_{currency}", ""))
            detail_vars["steam_lowest"].set(state["history_low"].get(currency, ""))
            detail_vars["best_price_shop"].set(state["best_price"].get("shop", ""))
            detail_vars["best_price_value"].set(state["best_price"].get("price", ""))

        def on_bundle_selected(_event=None):
            update_bundle_preview(var_bundle_choice.get())

        def fetch_online_data():
            if not self.applist:
                messagebox.showinfo(self.t("warning"), self.t("catalog_loading_wait"))
                return

            game_name = ent_name.get().strip()
            if not game_name:
                messagebox.showwarning(self.t("warning"), self.t("select_first"))
                return

            appid = state.get("appid") or get_steam_appid_by_name(game_name, self.applist)
            if not appid:
                messagebox.showerror(self.t("error"), self.t("game_not_found"))
                return

            state["appid"] = appid
            eur = get_steam_store_snapshot(appid, "pt")
            usd = get_steam_store_snapshot(appid, "us")

            state["steam_title"] = eur.get("title") or usd.get("title") or game_name
            state["image_url"] = eur.get("image_url") or usd.get("image_url") or ""
            state["price_data"] = {
                "regular_eur": eur.get("regular", ""),
                "regular_usd": usd.get("regular", ""),
                "current_eur": eur.get("current", ""),
                "current_usd": usd.get("current", ""),
            }

            cfg = self.settings
            itad_key = (cfg.get("ITAD_API_KEY") or "").strip()
            itad_country = (cfg.get("ITAD_COUNTRY") or "PT").strip().upper()

            # GID lookup uses free public endpoints — no API key required
            gid = get_itad_gid(appid, state["steam_title"])

            best_price = {"shop": "", "price": ""}
            history_low = {"eur": "", "usd": ""}

            # Barter.vg: comprehensive bundle history, no API key needed
            bundles = get_barter_vg_bundles(appid)

            # ITAD: supplementary bundle data + Steam lowest price (requires API key)
            if gid and itad_key:
                itad_bundles = get_itad_bundles_by_gid(gid, itad_key, itad_country)
                best_price = get_itad_best_current_deal(gid, itad_key, itad_country)
                history_low = get_itad_steam_lowest_prices(gid, itad_key, itad_country)

                # Fallback for Steam regular/current when Store API data is missing or flat.
                # ITAD exposes both current and regular for Steam deals.
                itad_steam_pt = get_itad_steam_current_prices(gid, itad_key, "PT")
                if itad_steam_pt.get("current"):
                    state["price_data"]["current_eur"] = itad_steam_pt.get("current")
                if itad_steam_pt.get("regular"):
                    state["price_data"]["regular_eur"] = itad_steam_pt.get("regular")

                itad_steam_us = get_itad_steam_current_prices(gid, itad_key, "US")
                if itad_steam_us.get("current"):
                    state["price_data"]["current_usd"] = itad_steam_us.get("current")
                if itad_steam_us.get("regular"):
                    state["price_data"]["regular_usd"] = itad_steam_us.get("regular")

                seen_names = {b.get("bundle_name", "") for b in bundles}
                for b in itad_bundles:
                    if b.get("bundle_name", "") not in seen_names:
                        bundles.append(b)
            elif not gid:
                reason = ITAD_LAST_ERROR or "Unknown ITAD lookup error"
                _log(f"ITAD GID lookup failed: {reason}")

            if not bundles and cfg.get("fallback_enabled"):
                bundles = get_barter_bundles(
                    appid,
                    state["steam_title"],
                    cfg.get("fallback_url") or "",
                    cfg.get("fallback_auth") or "",
                )

            if not bundles:
                _log(f"No bundles found for appid={appid} from any source")

            manual_option = {
                "bundle_choice": self.t("manual_bundle"),
                "platform": "",
                "bundle_name": self.t("manual_bundle"),
                "drm": "Steam",
                "bundle_date": "",
                "source": "Manual",
            }

            state["bundle_options"] = [manual_option] + bundles
            state["best_price"] = best_price
            state["history_low"] = history_low

            labels = [b.get("bundle_choice") for b in state["bundle_options"]]
            cmb_bundle["values"] = labels
            var_bundle_choice.set(labels[0] if labels else "")
            if labels:
                update_bundle_preview(labels[0])

        def confirm_add():
            game_name = ent_name.get().strip()
            if not game_name:
                messagebox.showwarning(self.t("warning"), self.t("select_first"))
                return
            if not state.get("appid"):
                messagebox.showwarning(self.t("warning"), self.t("select_first"))
                return

            selected_label = var_bundle_choice.get() or self.t("manual_bundle")
            selected_bundle = None
            for b in state["bundle_options"]:
                if b.get("bundle_choice") == selected_label:
                    selected_bundle = b
                    break
            if not selected_bundle:
                selected_bundle = {
                    "bundle_choice": selected_label,
                    "platform": "",
                    "bundle_name": selected_label,
                    "drm": "Steam",
                    "bundle_date": "",
                }

            game = ensure_game_defaults(
                {
                    "title": state.get("steam_title") or game_name,
                    "appid": state.get("appid"),
                    "bundle_choice": selected_bundle.get("bundle_choice", ""),
                    "platform": selected_bundle.get("platform", ""),
                    "bundle_name": selected_bundle.get("bundle_name", ""),
                    "drm": selected_bundle.get("drm", ""),
                    "steam_regular_eur": state["price_data"].get("regular_eur", ""),
                    "steam_regular_usd": state["price_data"].get("regular_usd", ""),
                    "steam_lowest_eur": state.get("history_low", {}).get("eur", ""),
                    "steam_lowest_usd": state.get("history_low", {}).get("usd", ""),
                    "best_price_shop": state.get("best_price", {}).get("shop", ""),
                    "best_price_value": state.get("best_price", {}).get("price", ""),
                    "bundle_date": selected_bundle.get("bundle_date", ""),
                    "key": ent_key.get().strip(),
                    "status": "In Stock",
                    "note": "",
                    "image_url": state.get("image_url", ""),
                    "bundle_options": state.get("bundle_options", []),
                }
            )

            self.games.append(game)
            self._persist_games()
            self._refresh_tree()
            self.tree.selection_set(str(len(self.games) - 1))
            self.tree.see(str(len(self.games) - 1))
            self.on_select_game()
            messagebox.showinfo(self.t("ok"), self.t("saved_game"))
            dlg.destroy()

        ent_name.bind("<KeyRelease>", on_suggestion_key)
        list_suggestions.bind("<Double-Button-1>", on_pick_suggestion)
        list_suggestions.bind("<<ListboxSelect>>", on_pick_suggestion)
        cmb_bundle.bind("<<ComboboxSelected>>", on_bundle_selected)

        actions = ttk.Frame(wrap, style="Surface.TFrame")
        actions.grid(row=5, column=0, columnspan=2, sticky="e")
        ttk.Button(actions, text=self.t("fetch_online"), command=fetch_online_data).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text=self.t("confirm_add"), style="Accent.TButton", command=confirm_add).pack(side="left")

        wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(3, weight=1)

    def save_settings_from_ui(self):
        new_theme = self.cmb_theme.get().strip() or "steam"
        new_lang = self.cmb_lang.get().strip() or "en"
        new_currency = _safe_str(self.cmb_currency.get()).upper() or "EUR"
        save_mode_label = _safe_str(self.cmb_save_mode.get()).strip()
        new_save_mode = (self.save_mode_map.get(save_mode_label) if hasattr(self, "save_mode_map") else None) or "local"

        self.settings["theme"] = new_theme if new_theme in THEMES else "steam"
        self.settings["language"] = new_lang if new_lang in TRANSLATIONS else "en"
        self.settings["display_currency"] = new_currency if new_currency in ("EUR", "USD") else "EUR"
        self.settings["save_mode"] = new_save_mode if new_save_mode in ("local", "cloud", "both") else "local"
        self.settings["cloud_save_url"] = self.ent_cloud_url.get().strip()
        self.settings["cloud_auth_header"] = self.ent_cloud_auth.get().strip()
        self.settings["ITAD_API_KEY"] = self.ent_itad_key.get().strip()
        self.settings["ITAD_COUNTRY"] = self.ent_itad_country.get().strip().upper() or "PT"
        self.settings["fallback_enabled"] = bool(self.var_fallback_enabled.get())
        self.settings["fallback_url"] = self.ent_fallback_url.get().strip()
        self.settings["fallback_auth"] = self.ent_fallback_auth.get().strip()

        _save_json(SETTINGS_FILE, self.settings)

        self.lang = self.settings["language"]
        self._apply_theme(self.settings["theme"])
        self._refresh_static_texts()
        self._refresh_tree()
        if self.selected_index is not None and 0 <= self.selected_index < len(self.games):
            self.tree.selection_set(str(self.selected_index))
            self.on_select_game()

        self._persist_games(show_errors=False)
        messagebox.showinfo(self.t("ok"), self.t("saved_settings"))

    def _refresh_static_texts(self):
        self.title(self.t("title"))
        self.lbl_title.config(text=self.t("title"))
        self.lbl_subtitle.config(text=self.t("subtitle"))
        if not self.applist:
            self.lbl_status.config(text=self.t("loading_catalog"))
        self.nb.tab(0, text=self.t("tab_library"))
        self.nb.tab(1, text=self.t("tab_settings"))

        self.btn_add.config(text=self.t("add_game"))
        self.btn_remove.config(text=self.t("remove_game"))
        self.btn_save_changes.config(text=self.t("save_changes"))
        if hasattr(self, "lbl_keys_section"):
            self.lbl_keys_section.config(text=self.t("keys_section"))
        if hasattr(self, "btn_add_key"):
            self.btn_add_key.config(text=self.t("add_key"))
        self.btn_save_settings.config(text=self.t("save_settings"))
        if hasattr(self, "btn_validate_itad"):
            self.btn_validate_itad.config(text=self.t("validate_itad"))
        if hasattr(self, "btn_cloud_download"):
            self.btn_cloud_download.config(text=self.t("cloud_download"))
        if hasattr(self, "btn_cloud_upload"):
            self.btn_cloud_upload.config(text=self.t("cloud_upload"))
        if hasattr(self, "btn_cloud_tutorial"):
            self.btn_cloud_tutorial.config(text=self.t("cloud_jsonbin_tutorial_btn"))
        if hasattr(self, "lbl_search"):
            self.lbl_search.config(text=self.t("search"))
        if hasattr(self, "lbl_details_title"):
            self.lbl_details_title.config(text=self.t("details"))
        if hasattr(self, "lbl_general_title"):
            self.lbl_general_title.config(text=self.t("general"))
        if hasattr(self, "lbl_providers_title"):
            self.lbl_providers_title.config(text=self.t("providers"))
        if hasattr(self, "lbl_cloud_title"):
            self.lbl_cloud_title.config(text=self.t("cloud"))
        if hasattr(self, "cmb_save_mode"):
            self.save_mode_map = {
                self.t("save_mode_local"): "local",
                self.t("save_mode_cloud"): "cloud",
                self.t("save_mode_both"): "both",
            }
            self.cmb_save_mode.configure(values=list(self.save_mode_map.keys()))
            current_mode = _safe_str(self.settings.get("save_mode", "local"))
            current_label = next((label for label, value in self.save_mode_map.items() if value == current_mode), self.t("save_mode_local"))
            self.cmb_save_mode.set(current_label)
            self._on_save_mode_changed()
        if hasattr(self, "lbl_cloud_url"):
            self.lbl_cloud_url.config(text=self.t("cloud_url"))
        if hasattr(self, "lbl_cloud_auth"):
            self.lbl_cloud_auth.config(text=self.t("cloud_auth"))

        self.tree.heading("title", text=self.t("game"))
        self.tree.heading("bundle_choice", text=self.t("bundle_dropdown"))
        self.tree.heading("platform", text=self.t("platform"))
        self.tree.heading("bundle_name", text=self.t("bundle_name"))
        self.tree.heading("drm", text=self.t("drm"))
        currency = self._selected_currency()
        self.tree.heading("steam_regular", text=f"{self.t('steam_regular')} {currency}")
        self.tree.heading("steam_lowest", text=f"{self.t('steam_lowest')} {currency}")
        self.tree.heading("best_price_shop", text=self.t("best_price_shop"))
        self.tree.heading("best_price_value", text=self.t("best_price_value"))
        self.tree.heading("bundle_date", text=self.t("bundle_date"))
        self.tree.heading("status", text=self.t("status"))

        if hasattr(self, "ent_filter"):
            self.ent_filter.delete(0, tk.END)


if __name__ == "__main__":
    app = SteamKeyApp()
    app.mainloop()
