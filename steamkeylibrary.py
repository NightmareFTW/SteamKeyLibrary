import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
import json
import os
import io
import time
import difflib
import threading
from datetime import datetime

# --- Debug logging ---
DEBUG_LOGS: list[str] = []

def _log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    DEBUG_LOGS.append(line)
    try:
        print(line)
    except Exception:
        pass

def _redact_params(params: dict | None):
    if not isinstance(params, dict):
        return params
    safe = dict(params)
    if 'key' in safe:
        safe['key'] = '***'
    if 'Authorization' in safe:
        safe['Authorization'] = '***'
    return safe

def _itad_request(url: str, params: dict, extra_headers: dict | None = None):
    """Make a GET request to ITAD with retries across auth styles.

    Tries in order:
    1) key as query param (current default)
    2) Authorization: key <KEY>
    3) Authorization: Bearer <KEY> (and removes key from query)

    Returns the requests.Response (or raises if requests itself fails).
    """
    headers = dict(HTTP_HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    # Attempt 1: key in query
    try:
        _log(f"GET {url} params={_redact_params(params)} attempt=1")
        r1 = requests.get(url, params=params, timeout=15, headers=headers)
        _log(f"ITAD status {r1.status_code} body={r1.text[:200]}")
        if r1.status_code not in (401, 403):
            return r1
    except Exception as e:
        _log(f"Erro ITAD attempt=1: {e}")

    # Attempt 2: Authorization: key <KEY>
    try:
        headers2 = dict(headers)
        headers2['Authorization'] = f"key {ITAD_API_KEY}"
        _log(f"GET {url} params={_redact_params(params)} headers={{'Authorization':'***'}} attempt=2")
        r2 = requests.get(url, params=params, timeout=15, headers=headers2)
        _log(f"ITAD status {r2.status_code} body={r2.text[:200]}")
        if r2.status_code not in (401, 403):
            return r2
    except Exception as e:
        _log(f"Erro ITAD attempt=2: {e}")

    # Attempt 3: Authorization: Bearer <KEY> and remove key from query
    try:
        headers3 = dict(headers)
        headers3['Authorization'] = f"Bearer {ITAD_API_KEY}"
        p3 = dict(params)
        p3.pop('key', None)
        _log(f"GET {url} params={_redact_params(p3)} headers={{'Authorization':'***'}} attempt=3")
        r3 = requests.get(url, params=p3, timeout=15, headers=headers3)
        _log(f"ITAD status {r3.status_code} body={r3.text[:200]}")
        if r3.status_code not in (401, 403):
            return r3
    except Exception as e:
        _log(f"Erro ITAD attempt=3: {e}")
    
    # Attempt 4: X-Api-Key header (some deployments accept this)
    try:
        headers4 = dict(headers)
        headers4['X-Api-Key'] = f"{ITAD_API_KEY}"
        p4 = dict(params)
        p4.pop('key', None)
        _log(f"GET {url} params={_redact_params(p4)} headers={{'X-Api-Key':'***'}} attempt=4")
        r4 = requests.get(url, params=p4, timeout=15, headers=headers4)
        _log(f"ITAD status {r4.status_code} body={r4.text[:200]}")
        return r4
    except Exception as e:
        _log(f"Erro ITAD attempt=4: {e}")
        raise

# --- Constants ---
DATA_FILE = 'games.json'
STEAM_APPLIST_CACHE_FILE = 'steam_applist.json'
STEAM_APPLIST_CACHE_TTL = 60 * 60 * 24  # 24 hours
ITAD_CACHE_FILE = 'itad_cache.json'
ITAD_CACHE_TTL = 60 * 60 * 12  # 12 hours
# Settings persistence (stores API keys and preferences)
SETTINGS_FILE = 'settings.json'
# Optional provider: Barter.vg authorized feed/template URL.
# Set an environment variable BARTER_BUNDLES_URL with placeholders {appid} and/or {title}
# Example (if such a feed is available to you):
#   https://barter.vg/feeds/bundles?appid={appid}&format=json
BARTER_BUNDLES_URL = os.getenv('BARTER_BUNDLES_URL')
BARTER_AUTH_HEADER = os.getenv('BARTER_AUTH_HEADER')  # optional auth header value
# Require environment variable for ITAD API key. No hardcoded default to avoid confusion.
ITAD_API_KEY = os.getenv("ITAD_API_KEY")
ITAD_BASE_URL = "https://api.isthereanydeal.com"
ITAD_COUNTRY = os.getenv("ITAD_COUNTRY")  # optional ISO 3166-1 alpha-2 (e.g., US, PT)
HTTP_HEADERS = {
    "User-Agent": "SteamKeyLibrary/0.1 (+https://github.com/NightmareFTW/SteamKeyLibrary)",
}
# Runtime flags for provider health
ITAD_KEY_INVALID = False
ITAD_LAST_ERROR = ""

# --- API Interaction Functions ---

def get_steam_applist():
    """Fetch or load cached Steam applist. Returns list of dicts with 'appid' and 'name'."""
    try:
        if os.path.exists(STEAM_APPLIST_CACHE_FILE):
            mtime = os.path.getmtime(STEAM_APPLIST_CACHE_FILE)
            if time.time() - mtime < STEAM_APPLIST_CACHE_TTL:
                with open(STEAM_APPLIST_CACHE_FILE, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    if isinstance(cached, list) and cached:
                        return cached
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        _log(f"GET {url}")
        response = requests.get(url, timeout=20, headers=HTTP_HEADERS)
        _log(f"Steam applist status {response.status_code}")
        response.raise_for_status()
        data = response.json()
        apps = data.get('applist', {}).get('apps', [])
        # Cache to disk for faster subsequent searches
        try:
            with open(STEAM_APPLIST_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(apps, f)
        except Exception:
            pass
        return apps
    except Exception as e:
        _log(f"Erro ao obter lista de apps da Steam: {e}")
        return []

def get_steam_appid_by_name(game_name, applist=None):
    """Find Steam AppID by (fuzzy) game name using cached applist for better matching."""
    try:
        apps = applist if applist is not None else get_steam_applist()
        if not apps:
            return None
        name_norm = (game_name or "").strip()
        if not name_norm:
            return None
        name_low = name_norm.lower()
        # 1) Exact, case-insensitive match
        for app in apps:
            if app.get('name', '').lower() == name_low:
                return app.get('appid')
        # 2) Startswith match
        starts = [a for a in apps if a.get('name', '').lower().startswith(name_low)]
        if starts:
            return starts[0].get('appid')
        # 3) Substring match
        contains = [a for a in apps if name_low in a.get('name', '').lower()]
        if contains:
            return contains[0].get('appid')
        # 4) Fuzzy match via difflib
        names = [a.get('name', '') for a in apps if a.get('name')]
        best = difflib.get_close_matches(name_norm, names, n=1, cutoff=0.8)
        if best:
            best_name = best[0]
            for a in apps:
                if a.get('name') == best_name:
                    return a.get('appid')
        return None
    except Exception as e:
        print(f"Erro ao procurar AppID: {e}")
        return None

def search_steam_suggestions(query, applist=None, limit=12):
    """Return up to 'limit' (name, appid) suggestions for the given query."""
    apps = applist if applist is not None else get_steam_applist()
    q = (query or '').strip().lower()
    if not q:
        return []
    # Prioritize startswith, then contains, then fuzzy
    starts = [(a.get('name'), a.get('appid')) for a in apps if a.get('name', '').lower().startswith(q)]
    contains = [(a.get('name'), a.get('appid')) for a in apps if q in a.get('name', '').lower() and (a.get('name'), a.get('appid')) not in starts]
    results = starts + contains
    if len(results) < limit:
        names = [a.get('name', '') for a in apps if a.get('name')]
        fuzzy = difflib.get_close_matches(query, names, n=limit*2, cutoff=0.75)
        for name in fuzzy:
            # find corresponding appid
            for a in apps:
                if a.get('name') == name:
                    tup = (name, a.get('appid'))
                    if tup not in results:
                        results.append(tup)
                    break
    return results[:limit]

def get_steam_price_and_image(appid, cc="pt"):
    """Fetches price details and header image URL from the Steam store API."""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={cc}&l=en"
        _log(f"GET {url}")
        response = requests.get(url, timeout=20, headers=HTTP_HEADERS)
        _log(f"Steam appdetails status {response.status_code}")
        data = response.json()
        entry = data.get(str(appid), {})
        if not entry or not entry.get('success'):
            raise ValueError("Steam store returned no data for appid")
        info = entry.get('data', {})
        price_data = info.get("price_overview", {})
        final = price_data.get("final", 0) / 100
        regular = price_data.get("initial", final * 100) / 100
        image_url = info.get("header_image", f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg")
        title = info.get("name") or ""
        return {
            "steam_price": f"{final:.2f}",
            "regular_price": f"{regular:.2f}",
            "image_url": image_url,
            "title": title
        }
    except Exception as e:
        _log(f"Erro ao obter preços/imagem da Steam: {e}")
        return {
            "steam_price": "0.00",
            "regular_price": "0.00",
            "image_url": None
        }

def get_itad_plain_id(appid, title: str | None = None):
    """Legacy v02 flow: map Steam appid/title to ITAD 'plain' id.

    Kept for backward-compatibility. Returns plain or None.
    """
    if not ITAD_API_KEY:
        _log("ITAD_API_KEY não definido. Configure a variável de ambiente ITAD_API_KEY.")
        return None
    try:
        url = "https://api.isthereanydeal.com/v02/game/plain/id/"
        ids = f"app/{appid}"
        params = {"key": ITAD_API_KEY, "shop": "steam", "ids": ids}
        _log(f"GET {url} params={_redact_params(params)}")
        response = requests.get(url, params=params, timeout=15, headers=HTTP_HEADERS)
        _log(f"ITAD plain/id status {response.status_code} body={response.text[:200]}")
        if response.status_code == 200:
            data = response.json()
            plain = data.get("data", {}).get(ids)
        else:
            plain = None
        if not plain and title:
            try:
                url_title = "https://api.isthereanydeal.com/v02/game/plain/list/"
                params = {"key": ITAD_API_KEY, "title": title, "limit": 5}
                _log(f"GET {url_title} params={_redact_params(params)}")
                r2 = requests.get(url_title, params=params, timeout=15, headers=HTTP_HEADERS)
                _log(f"ITAD plain/list status {r2.status_code} body={r2.text[:200]}")
                if r2.status_code == 200:
                    j2 = r2.json()
                    candidates = ((j2.get('data') or []) if isinstance(j2, dict) else [])
                    if candidates:
                        exact = next((c for c in candidates if c.get('title','').lower()==(title or '').lower()), None)
                        plain = (exact or candidates[0]).get('plain')
            except Exception as ie:
                _log(f"Erro fallback plain por título: {ie}")
        if not plain:
            _log("ITAD v02: 'plain' não encontrado.")
            return None
        return plain
    except Exception as e:
        _log(f"Erro ao obter plain ID do ITAD: {e}")
        return None

def get_itad_gid(appid: int | None = None, title: str | None = None):
    """Use new OpenAPI endpoint to lookup ITAD Game ID (UUID) by appid or title.

    Returns dict { 'id': <uuid>, 'title': <str> } or None.
    """
    if not ITAD_API_KEY:
        _log("ITAD_API_KEY não definido. Configure a variável de ambiente ITAD_API_KEY.")
        return None
    try:
        url = f"{ITAD_BASE_URL}/games/lookup/v1"
        params = {"key": ITAD_API_KEY}
        if appid is not None:
            params["appid"] = int(appid)
        elif title:
            params["title"] = title
        else:
            _log("get_itad_gid: é necessário appid ou title")
            return None
        # Use resilient requester to try multiple auth styles
        r = _itad_request(url, params)
        if r.status_code == 403:
            # mark key invalid for UI feedback
            try:
                j = r.json()
                msg = j.get('reason_phrase') or 'Invalid or expired api key'
            except Exception:
                msg = 'Invalid or expired api key'
            global ITAD_KEY_INVALID, ITAD_LAST_ERROR
            ITAD_KEY_INVALID = True
            ITAD_LAST_ERROR = msg
            return None
        if r.status_code != 200:
            return None
        j = r.json() if r.text else {}
        if not isinstance(j, dict) or not j.get('found'):
            return None
        game = j.get('game') or {}
        gid = game.get('id') or game.get('gid')
        gtitle = game.get('title') or title or ''
        if not gid:
            return None
        return {"id": gid, "title": gtitle}
    except Exception as e:
        _log(f"Erro ITAD games/lookup: {e}")
        return None

def _load_json_file(path, default):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default

def _save_json_file(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# --- App Settings (persisted) ---

def load_settings():
    """Load app settings (like ITAD_API_KEY) from disk.

    Returns a dict. Missing file → {}.
    """
    return _load_json_file(SETTINGS_FILE, {}) or {}

def save_settings(cfg: dict):
    """Persist settings to disk."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg or {}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def apply_settings(cfg: dict | None):
    """Apply settings to runtime globals (e.g., ITAD_API_KEY, ITAD_COUNTRY)."""
    if not isinstance(cfg, dict):
        return
    global ITAD_API_KEY, ITAD_COUNTRY
    if cfg.get('ITAD_API_KEY'):
        ITAD_API_KEY = cfg['ITAD_API_KEY']
    if cfg.get('ITAD_COUNTRY'):
        ITAD_COUNTRY = cfg['ITAD_COUNTRY']

def _normalize_itad_bundles(j):
    """Normalize legacy v02 bundle response into [{title, date}]."""
    if isinstance(j, list):
        payload = j
    elif isinstance(j, dict):
        d = j.get("data", {}) if isinstance(j, dict) else {}
        payload = d.get("bundles") or d.get("list") or (d if isinstance(d, list) else [])
    else:
        payload = []
    result = []
    for b in payload or []:
        if not isinstance(b, dict):
            continue
        title = b.get("title") or b.get("name") or "Unknown Bundle"
        start = b.get("start") or b.get("date") or ""
        result.append({
            "title": title,
            "date": (start or "")[:10]
        })
    return result

def _normalize_itad_bundles_v2(items):
    """Normalize /games/bundles/v2 array into [{title, date}]."""
    payload = items
    if isinstance(items, dict):
        # Sometimes APIs still wrap arrays
        payload = items.get('data') or items.get('list') or items.get('bundles') or []
    result = []
    if not isinstance(payload, list):
        payload = []
    for b in payload:
        if not isinstance(b, dict):
            continue
        title = b.get('title') or b.get('name') or 'Unknown Bundle'
        date = ''
        pub = b.get('publish')
        if isinstance(pub, dict):
            date = pub.get('start') or pub.get('date') or pub.get('published') or ''
        elif isinstance(pub, str):
            date = pub
        if not date:
            date = b.get('start') or b.get('date') or b.get('publishDate') or ''
        result.append({
            'title': title,
            'date': (date or '')[:10]
        })
    return result

def _normalize_generic_bundles(j):
    """Try to normalize a generic JSON response into our bundle schema.

    Accepts formats like:
    - { data: [ { title, date }, ... ] }
    - [ { title, date }, ... ]
    - { list: [ { name/title, start/date }, ... ] }
    """
    if isinstance(j, dict):
        payload = j.get('data') if 'data' in j else j.get('list') if 'list' in j else j
    else:
        payload = j
    if isinstance(payload, dict):
        # sometimes nested again
        payload = payload.get('list') or payload.get('bundles') or payload
    out = []
    if isinstance(payload, list):
        for b in payload:
            if not isinstance(b, dict):
                continue
            title = b.get('title') or b.get('name') or 'Unknown Bundle'
            start = b.get('date') or b.get('start') or ''
            out.append({ 'title': title, 'date': (start or '')[:10] })
    return out

def get_itad_bundles(itad_plain, include_expired=True, use_cache=True):
    """Fetch ITAD bundles (current and/or historical). Returns list sorted by date desc.

    Caches results for a short period to avoid rate limits and speed up UI.
    """
    if not ITAD_API_KEY:
        _log("ITAD_API_KEY não definido. Configure a variável de ambiente ITAD_API_KEY.")
        return []
    cache_key = f"bundles::{itad_plain}::expired={'1' if include_expired else '0'}"
    now = time.time()
    if use_cache:
        cache = _load_json_file(ITAD_CACHE_FILE, {"_ts": {}})
        ts = cache.get("_ts", {}).get(cache_key)
        if ts and (now - ts) < ITAD_CACHE_TTL:
            cached = cache.get(cache_key, [])
            if isinstance(cached, list):
                return cached

    base = "https://api.isthereanydeal.com/v02/game/bundles/"
    result = []
    try:
        # Current bundles
        params_cur = {"key": ITAD_API_KEY, "plain": itad_plain, "expired": 0}
        _log(f"GET {base} params={_redact_params(params_cur)}")
        r1 = requests.get(base, params=params_cur, timeout=15, headers=HTTP_HEADERS)
        _log(f"ITAD bundles current status {r1.status_code} body={r1.text[:200]}")
        if r1.status_code == 200:
            result.extend(_normalize_itad_bundles(r1.json()))
        else:
            _log(f"ITAD bundles (current) falhou: {r1.status_code}")
    except Exception as e:
        _log(f"Erro ITAD bundles (current): {e}")
    try:
        if include_expired:
            params_exp = {"key": ITAD_API_KEY, "plain": itad_plain, "expired": 1}
            _log(f"GET {base} params={_redact_params(params_exp)}")
            r2 = requests.get(base, params=params_exp, timeout=15, headers=HTTP_HEADERS)
            _log(f"ITAD bundles expired status {r2.status_code} body={r2.text[:200]}")
            if r2.status_code == 200:
                result.extend(_normalize_itad_bundles(r2.json()))
            else:
                _log(f"ITAD bundles (expired) falhou: {r2.status_code}")
    except Exception as e:
        _log(f"Erro ITAD bundles (expired): {e}")

    # Dedupe and sort by date desc
    seen = set()
    deduped = []
    for b in result:
        key = (b.get('title'), b.get('date'))
        if key not in seen:
            seen.add(key)
            deduped.append(b)
    def sort_key(b):
        return b.get('date') or ''
    deduped.sort(key=sort_key, reverse=True)

    if use_cache:
        cache = _load_json_file(ITAD_CACHE_FILE, {"_ts": {}})
        cache[cache_key] = deduped
        cache.setdefault("_ts", {})[cache_key] = now
    _save_json_file(ITAD_CACHE_FILE, cache)

    return deduped

def get_itad_bundles_by_gid(gid: str, use_cache: bool = True):
    """Use new OpenAPI /games/bundles/v2 to get bundles by ITAD Game ID (uuid)."""
    if not ITAD_API_KEY:
        _log("ITAD_API_KEY não definido. Configure a variável de ambiente ITAD_API_KEY.")
        return []
    cache_key = f"bundles_gid::{gid}::country={(ITAD_COUNTRY or 'default')}"
    now = time.time()
    if use_cache:
        cache = _load_json_file(ITAD_CACHE_FILE, {"_ts": {}})
        ts = cache.get("_ts", {}).get(cache_key)
        if ts and (now - ts) < ITAD_CACHE_TTL:
            cached = cache.get(cache_key, [])
            if isinstance(cached, list):
                return cached
    try:
        url = f"{ITAD_BASE_URL}/games/bundles/v2"
        params = {"key": ITAD_API_KEY, "id": gid}
        if ITAD_COUNTRY:
            params["country"] = ITAD_COUNTRY
        r = _itad_request(url, params)
        if r.status_code == 403:
            try:
                j = r.json()
                msg = j.get('reason_phrase') or 'Invalid or expired api key'
            except Exception:
                msg = 'Invalid or expired api key'
            global ITAD_KEY_INVALID, ITAD_LAST_ERROR
            ITAD_KEY_INVALID = True
            ITAD_LAST_ERROR = msg
            return []
        if r.status_code != 200:
            return []
        bundles = _normalize_itad_bundles_v2(r.json())
        # dedupe and sort by date desc
        seen = set()
        out = []
        for b in bundles:
            key = (b.get('title'), b.get('date'))
            if key not in seen:
                seen.add(key)
                out.append(b)
        out.sort(key=lambda b: b.get('date') or '', reverse=True)
        if use_cache:
            cache = _load_json_file(ITAD_CACHE_FILE, {"_ts": {}})
            cache[cache_key] = out
            cache.setdefault("_ts", {})[cache_key] = now
            _save_json_file(ITAD_CACHE_FILE, cache)
        return out
    except Exception as e:
        _log(f"Erro ITAD bundles by gid: {e}")
        return []

def get_bundles_for_game(itad_plain):
    """Public wrapper used by UI: fetch both current and historical bundles from ITAD."""
    return get_itad_bundles(itad_plain, include_expired=True, use_cache=True)

def get_barter_bundles(appid: int, title: str | None = None, use_cache: bool = True):
    """Fetch bundles from Barter.vg authorized feed if configured via env.

    Respects site ToS by only calling an explicitly configured feed URL.
    Returns normalized list or empty if not configured/failed.
    """
    if not BARTER_BUNDLES_URL:
        return []
    cache_key = f"barter::{appid}::{(title or '').lower()}"
    now = time.time()
    if use_cache:
        cache = _load_json_file(ITAD_CACHE_FILE, {"_ts": {}})
        ts = cache.get("_ts", {}).get(cache_key)
        if ts and (now - ts) < ITAD_CACHE_TTL:
            cached = cache.get(cache_key, [])
            if isinstance(cached, list):
                return cached
    try:
        url = BARTER_BUNDLES_URL
        try:
            url = url.replace('{appid}', str(appid))
        except Exception:
            pass
        if title:
            try:
                url = url.replace('{title}', requests.utils.quote(title))
            except Exception:
                pass
        headers = dict(HTTP_HEADERS)
        if BARTER_AUTH_HEADER:
            headers['Authorization'] = BARTER_AUTH_HEADER
        _log(f"GET {url}")
        r = requests.get(url, timeout=20, headers=headers)
        _log(f"Barter feed status {r.status_code} body={r.text[:200]}")
        if r.status_code != 200:
            _log(f"Barter feed falhou: {r.status_code}")
            return []
        bundles = _normalize_generic_bundles(r.json())
        # Tag source for UI display
        for b in bundles:
            b['source'] = 'Barter'
        cache = _load_json_file(ITAD_CACHE_FILE, {"_ts": {}})
        cache[cache_key] = bundles
        cache.setdefault("_ts", {})[cache_key] = now
        _save_json_file(ITAD_CACHE_FILE, cache)
        return bundles
    except Exception as e:
        _log(f"Erro a obter bundles via Barter: {e}")
        return []

def get_bundles_via_providers(appid: int, title: str | None, allow_barter: bool = True):
    """Try multiple providers to get bundles: ITAD (new API), ITAD (legacy), then Barter.

    allow_barter controls whether the Barter fallback is used.
    """
    # ITAD new API flow: lookup GID then bundles/v2
    info = get_itad_gid(appid=appid, title=title or '')
    if info and info.get('id'):
        bundles = get_itad_bundles_by_gid(info['id'])
        if bundles:
            for b in bundles:
                b['source'] = 'ITAD'
            return bundles
    # ITAD legacy flow as backup (plain -> v02 bundles)
    itad_plain = get_itad_plain_id(appid, title=title or '')
    if itad_plain:
        bundles = get_bundles_for_game(itad_plain)
        if bundles:
            for b in bundles:
                b['source'] = 'ITAD'
            return bundles
    # Barter fallback
    if allow_barter:
        barter = get_barter_bundles(appid, title)
        if barter:
            return barter
    return []

# --- GUI Helper Functions ---

def select_bundle_popup(bundle_list, callback, include_none_option=True):
    """Creates a popup window for the user to select a bundle from a list.

    If include_none_option is True, a "No bundle / manual" option is added.
    """
    popup = tk.Toplevel()
    popup.title("Select Bundle")
    popup.configure(bg="#1b2838")
    popup.geometry("400x300")
    tk.Label(popup, text="Choose the bundle this game came from:", bg="#1b2838", fg="white").pack(pady=10)
    listbox = tk.Listbox(popup, height=10, width=50)
    listbox.pack(padx=10, pady=5)
    effective_list = list(bundle_list)
    if include_none_option:
        effective_list = ([{"title": "No bundle / manual", "date": ""}] + effective_list)
    for bundle in effective_list:
        src = f" [{bundle.get('source')}]" if bundle.get('source') else ""
        listbox.insert(tk.END, f"{bundle['title']} ({bundle['date']}){src}")
    def on_select():
        index = listbox.curselection()
        if index:
            selected = effective_list[index[0]]
            callback(selected)
            popup.destroy()
        else:
            messagebox.showwarning("Warning", "Please select a bundle.")
    tk.Button(popup, text="Confirm", command=on_select, bg="#66C0F4").pack(pady=10)

# --- Data Handling ---

def load_games():
    """Loads the list of games from the JSON data file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_games(game_list):
    """Saves the list of games to the JSON data file."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(game_list, f, ensure_ascii=False, indent=4)

# --- Main Application Class ---

class SteamKeyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Steam Key Library")
        self.configure(bg='#171a21')
        # Load settings and apply (ITAD key, country, etc.)
        self.settings = load_settings()
        apply_settings(self.settings)
        self.games = load_games()
        # We'll load the Steam applist asynchronously and show a small loading indicator
        self.applist = []

        # Menu bar (Settings → ITAD API Key)
        menubar = tk.Menu(self)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Set ITAD API Key…", command=self.prompt_itad_key)
        settings_menu.add_command(label="Set ITAD Country…", command=self.prompt_itad_country)
        settings_menu.add_separator()
        settings_menu.add_command(label="Validate ITAD Key…", command=self.validate_itad_key)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        self.config(menu=menubar)
        
        # Setup for scrollable frame
        self.canvas = tk.Canvas(self, bg='#171a21')
        self.frame = tk.Frame(self.canvas, bg='#171a21')
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.frame, anchor='nw')
        
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Loading indicator for Steam applist
        self.status_frame = tk.Frame(self, bg="#1b2838")
        self.status_label = tk.Label(self.status_frame, text="Loading Steam catalog...", bg="#1b2838", fg="white")
        self.status_label.pack(side='left', padx=10, pady=4)
        self.status_pb = ttk.Progressbar(self.status_frame, mode='indeterminate', length=150)
        self.status_pb.pack(side='left', padx=10)
        self.status_pb.start(10)
        self.status_frame.pack(fill='x')

        # Main UI elements
        tk.Button(self, text="Add Game", command=self.add_game_workflow, bg="#66C0F4").pack(fill="x")

        # Providers debug/settings bar
        prov_frame = tk.Frame(self, bg="#1b2838")
        prov_frame.pack(fill='x', pady=2)
        tk.Label(prov_frame, text="Providers:", bg="#1b2838", fg="white").pack(side='left', padx=8)
        self.lbl_itad_status = tk.Label(prov_frame, bg="#1b2838", fg="gray")
        self.lbl_itad_status.pack(side='left', padx=6)
        barter_ok = "Yes" if BARTER_BUNDLES_URL else "No"
        shown_url = (BARTER_BUNDLES_URL or "").split('?')[0][:48] + ("…" if BARTER_BUNDLES_URL and len(BARTER_BUNDLES_URL)>48 else "")
        tk.Label(prov_frame, text=f"Barter feed: {barter_ok} {shown_url}", bg="#1b2838", fg="gray").pack(side='left', padx=6)
        self.enable_fallback = tk.BooleanVar(value=bool(BARTER_BUNDLES_URL))
        tk.Checkbutton(prov_frame, text="Enable fallback", variable=self.enable_fallback, bg="#1b2838", fg="white", selectcolor="#1b2838", activebackground="#1b2838").pack(side='left', padx=6)
        tk.Button(prov_frame, text="Test Providers", command=self.open_provider_test_dialog, bg="#2A475E", fg="white").pack(side='right', padx=8)
        # Initial provider status
        self.refresh_provider_status()
        
        # Load and display existing games
        for game in self.games:
            self.add_card(game)

        # Preload applist asynchronously after UI is ready
        def _load_applist_worker():
            apps = get_steam_applist()
            def on_done():
                self.applist = apps
                try:
                    self.status_pb.stop()
                except Exception:
                    pass
                try:
                    self.status_frame.destroy()
                except Exception:
                    pass
            self.after(0, on_done)

        threading.Thread(target=_load_applist_worker, daemon=True).start()

    # --- Settings Dialogs ---

    def validate_itad_key(self):
        if not ITAD_API_KEY:
            messagebox.showwarning("ITAD", "No API key configured. Go to Settings → Set ITAD API Key…")
            return
        info = get_itad_gid(appid=570)
        if info and info.get('id'):
            messagebox.showinfo("ITAD", "Key looks valid for OpenAPI endpoints (lookup passed).")
        else:
            reason = globals().get('ITAD_LAST_ERROR') or 'Unknown error'
            messagebox.showerror(
                "ITAD",
                f"Lookup failed. Server replied: {reason}.\n\n"
                "If the key is new, it may need activation/approval or a short propagation period."
            )

    def refresh_provider_status(self):
        # Update ITAD key status label based on current globals/flags
        status = 'No'
        color = 'gray'
        if ITAD_API_KEY:
            status = 'Yes'
        if 'ITAD_KEY_INVALID' in globals() and ITAD_KEY_INVALID:
            status = 'Invalid'
            color = 'orange'
        extra = f" — {ITAD_LAST_ERROR}" if status == 'Invalid' and (globals().get('ITAD_LAST_ERROR') or '') else ''
        self.lbl_itad_status.config(text=f"ITAD key: {status}{extra}", fg=color)

    def prompt_itad_key(self):
        win = tk.Toplevel(self)
        win.title("Set ITAD API Key")
        win.configure(bg="#1b2838")
        win.geometry("520x140")
        tk.Label(win, text="Enter your ITAD API Key:", bg="#1b2838", fg="white").pack(pady=8)
        entry = tk.Entry(win, width=60)
        entry.pack(pady=4)
        current = (self.settings.get('ITAD_API_KEY') or ITAD_API_KEY or '')
        entry.insert(0, current)
        info = tk.Label(win, text="You can create a key at https://isthereanydeal.com/apps/my/", bg="#1b2838", fg="gray")
        info.pack(pady=2)

        def save_key():
            key = (entry.get() or '').strip()
            if len(key) < 20:
                messagebox.showerror("Invalid Key", "Please paste a valid ITAD API key.")
                return
            self.settings['ITAD_API_KEY'] = key
            save_settings(self.settings)
            apply_settings(self.settings)
            # Update Providers bar label
            global ITAD_KEY_INVALID, ITAD_LAST_ERROR
            ITAD_KEY_INVALID = False
            ITAD_LAST_ERROR = ''
            self.refresh_provider_status()
            messagebox.showinfo("Saved", "ITAD API key saved and applied.")
            win.destroy()

        tk.Button(win, text="Save", command=save_key, bg="#66C0F4").pack(pady=8)

    def prompt_itad_country(self):
        win = tk.Toplevel(self)
        win.title("Set ITAD Country")
        win.configure(bg="#1b2838")
        win.geometry("420x140")
        tk.Label(win, text="Country code (ISO 3166-1 alpha-2, e.g., US, PT):", bg="#1b2838", fg="white").pack(pady=8)
        entry = tk.Entry(win, width=16)
        entry.pack(pady=4)
        current = (self.settings.get('ITAD_COUNTRY') or ITAD_COUNTRY or '')
        entry.insert(0, current)

        def save_country():
            cc = (entry.get() or '').strip().upper()
            if cc and len(cc) != 2:
                messagebox.showerror("Invalid Country", "Please enter a 2-letter country code (e.g., US, PT).")
                return
            if cc:
                self.settings['ITAD_COUNTRY'] = cc
            else:
                self.settings.pop('ITAD_COUNTRY', None)
            save_settings(self.settings)
            apply_settings(self.settings)
            messagebox.showinfo("Saved", "Country setting saved.")
            win.destroy()

        tk.Button(win, text="Save", command=save_country, bg="#66C0F4").pack(pady=8)

    def open_provider_test_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Test Providers")
        dlg.configure(bg="#1b2838")
        dlg.geometry("480x420")
        tk.Label(dlg, text="Enter game name to test bundle providers:", bg="#1b2838", fg="white").pack(pady=8)
        entry = tk.Entry(dlg, width=45)
        entry.pack(pady=4)
        result_box = tk.Listbox(dlg, height=14, width=64)
        result_box.pack(padx=8, pady=8)

        def run_test():
            result_box.delete(0, tk.END)
            name = entry.get().strip()
            if not name:
                result_box.insert(tk.END, "Please enter a game name.")
                return
            appid = get_steam_appid_by_name(name, self.applist)
            if not appid:
                result_box.insert(tk.END, "Could not resolve AppID from Steam.")
                return
            steam = get_steam_price_and_image(appid)
            lookup_title = steam.get('title') or name
            bundles = get_bundles_via_providers(appid, lookup_title, allow_barter=self.enable_fallback.get())
            if not bundles:
                # Provide a more actionable message by checking ITAD directly
                info = get_itad_gid(appid=appid, title=lookup_title)
                if info and info.get('id'):
                    only_itad = get_itad_bundles_by_gid(info['id'])
                    if not only_itad:
                        result_box.insert(tk.END, "ITAD: game found but no bundles recorded.")
                    else:
                        result_box.insert(tk.END, f"ITAD: {len(only_itad)} bundles, but filtering returned none.")
                else:
                    result_box.insert(tk.END, "ITAD: game not found via lookup.")
                if self.enable_fallback.get() and BARTER_BUNDLES_URL:
                    alt = get_barter_bundles(appid, lookup_title)
                    if not alt:
                        result_box.insert(tk.END, "Fallback provider: no bundles.")
                if result_box.size() == 0:
                    result_box.insert(tk.END, "No bundles found across configured providers.")
                return
            for b in bundles[:50]:
                src = b.get('source') or ''
                result_box.insert(tk.END, f"{b.get('title')} ({b.get('date','')}) [{src}]")

        tk.Button(dlg, text="Run", command=run_test, bg="#66C0F4").pack(pady=6)
        tk.Button(dlg, text="Close", command=dlg.destroy, bg="#2A475E", fg="white").pack(pady=4)

    def add_game_workflow(self):
        """Guides the user through the multi-step process of adding a new game."""
        add_win = tk.Toplevel(self)
        add_win.title("Add Game")
        add_win.configure(bg="#1b2838")
        
        tk.Label(add_win, text="Game Name:", bg="#1b2838", fg="white").pack(pady=5)
        name_entry = tk.Entry(add_win, width=40)
        name_entry.pack(pady=5)

        # Autocomplete suggestions
        sugg_frame = tk.Frame(add_win, bg="#1b2838")
        sugg_frame.pack(fill='both', expand=False, padx=5)
        tk.Label(sugg_frame, text="Suggestions:", bg="#1b2838", fg="gray").pack(anchor='w')
        sugg_list = tk.Listbox(sugg_frame, height=8, width=50)
        sugg_list.pack(padx=0, pady=5, fill='both')
        selected = {"name": None, "appid": None}

        def update_suggestions(*args):
            sugg_list.delete(0, tk.END)
            query = name_entry.get()
            if not self.applist:
                sugg_list.insert(tk.END, "Loading catalogue...")
                return
            for name, appid in search_steam_suggestions(query, self.applist, limit=12):
                sugg_list.insert(tk.END, f"{name} (AppID: {appid})")

        def on_sugg_select(event=None):
            idx = sugg_list.curselection()
            if not idx:
                return
            label = sugg_list.get(idx[0])
            try:
                # parse 'Name (AppID: 123)'
                if label.endswith(')') and '(AppID:' in label:
                    name = label[:label.rfind(' (AppID:')]
                    appid_str = label[label.rfind(':')+1:-1].strip()
                    selected["name"] = name
                    selected["appid"] = int(appid_str)
                    name_entry.delete(0, tk.END)
                    name_entry.insert(0, name)
            except Exception:
                pass

        sugg_list.bind('<Double-Button-1>', on_sugg_select)
        name_entry.bind('<KeyRelease>', update_suggestions)
        
        def continue_process():
            game_name = name_entry.get()
            if not game_name:
                messagebox.showerror("Error", "Please enter a game name.")
                return
            if not (selected["appid"] or self.applist):
                messagebox.showinfo("Please wait", "Steam catalog is still loading. Try again in a moment.")
                return
            
            # Prefer selected suggestion's appid, fallback to fuzzy search
            appid = selected["appid"] or get_steam_appid_by_name(game_name, self.applist)
            if not appid:
                messagebox.showerror("Error", "Game not found on Steam.")
                return
                
            steam_data = get_steam_price_and_image(appid)
            # Prefer official Steam title for lookups
            lookup_title = steam_data.get("title") or game_name

            # Try providers in order (ITAD first, then Barter if configured)
            provider_bundles = get_bundles_via_providers(appid, lookup_title)
            if not provider_bundles:
                proceed = messagebox.askyesno(
                    "No bundles found",
                    "No bundles were found across providers. Do you want to continue and enter bundle info manually?"
                )
                if not proceed:
                    return
                # Manual flow: skip bundle lookup and go straight to key entry
                def manual_entry():
                    key_win = tk.Toplevel()
                    key_win.title("Enter Steam Key & Bundle")
                    key_win.configure(bg="#1b2838")

                    tk.Label(key_win, text="Steam Key Code:", bg="#1b2838", fg="white").pack(pady=5)
                    key_entry = tk.Entry(key_win, width=40)
                    key_entry.pack(pady=5)

                    tk.Label(key_win, text="Bundle (optional):", bg="#1b2838", fg="white").pack(pady=5)
                    bundle_entry = tk.Entry(key_win, width=40)
                    bundle_entry.pack(pady=5)

                    tk.Label(key_win, text="Date (YYYY-MM-DD, optional):", bg="#1b2838", fg="white").pack(pady=5)
                    date_entry = tk.Entry(key_win, width=20)
                    date_entry.pack(pady=5)

                    def finalize_manual():
                        game = {
                            "title": game_name,
                            "appid": appid,
                            "steam_price": steam_data.get("steam_price", "0.00"),
                            "lowest_price": steam_data.get("regular_price", "0.00"),
                            "image_url": steam_data.get("image_url"),
                            "bundle": bundle_entry.get().strip() or "No bundle / manual",
                            "date": date_entry.get().strip(),
                            "key": key_entry.get(),
                            "status": "In Stock",
                            "note": ""
                        }
                        self.games.append(game)
                        save_games(self.games)
                        self.add_card(game)
                        key_win.destroy()
                        add_win.destroy()

                    tk.Button(key_win, text="Add Game", command=finalize_manual, bg="#66C0F4").pack(pady=10)

                manual_entry()
                return
            
            # Use the provider results when available
            bundle_list = provider_bundles or []
            if not bundle_list:
                # Allow proceeding without bundle selection
                proceed = messagebox.askyesno("No bundles found", "No bundles found on ITAD for this game. Do you want to continue without selecting a bundle?")
                if proceed:
                    # proceed to key entry with default 'No bundle' selection
                    return after_bundle_selected({"title": "No bundle / manual", "date": ""})
                return
            
            def after_bundle_selected(bundle):
                key_win = tk.Toplevel()
                key_win.title("Enter Steam Key")
                key_win.configure(bg="#1b2838")
                
                tk.Label(key_win, text="Steam Key Code:", bg="#1b2838", fg="white").pack(pady=5)
                key_entry = tk.Entry(key_win, width=40)
                key_entry.pack(pady=5)
                
                def finalize():
                    game = {
                        "title": game_name,
                        "appid": appid,
                        "steam_price": steam_data["steam_price"],
                        "lowest_price": steam_data["regular_price"],
                        "image_url": steam_data["image_url"],
                        "bundle": bundle["title"],
                        "date": bundle["date"],
                        "key": key_entry.get(),
                        "status": "In Stock",
                        "note": ""
                    }
                    self.games.append(game)
                    save_games(self.games)
                    self.add_card(game)
                    key_win.destroy()
                    add_win.destroy()

                tk.Button(key_win, text="Add Game", command=finalize, bg="#66C0F4").pack(pady=10)

            select_bundle_popup(bundle_list, after_bundle_selected, include_none_option=True)

        tk.Button(add_win, text="Search", command=continue_process, bg="#66C0F4").pack(pady=10)

    def add_card(self, game):
        """Creates and displays a 'card' for a single game in the main window."""
        card = tk.Frame(self.frame, bg='#1b2838', bd=1, relief="solid", padx=10, pady=10)
        card.pack(fill='x', pady=5, padx=10)
        
        # Game Image
        try:
            response = requests.get(game['image_url'])
            image_data = Image.open(io.BytesIO(response.content)).resize((150, 70))
            photo = ImageTk.PhotoImage(image_data)
            tk.Label(card, image=photo, bg='#1b2838').grid(row=0, column=0, rowspan=4)
            card.image = photo  # Keep a reference to avoid garbage collection
        except:
            pass # Fails silently if image can't be loaded
            
        # Game Details
        tk.Label(card, text=game['title'], font=('Segoe UI', 14, 'bold'),
                 bg='#1b2838', fg='white').grid(row=0, column=1, sticky='w')
        tk.Label(card, text=f"Bundle: {game['bundle']} ({game['date']})",
                 font=('Segoe UI', 10), bg='#1b2838', fg='white').grid(row=1, column=1, sticky='w')
        tk.Label(card, text=f"Steam Price: €{game['steam_price']} | Lowest: €{game['lowest_price']}",
                 bg='#1b2838', fg='white').grid(row=2, column=1, sticky='w')
        
        # Key display and toggle
        key_var = tk.StringVar(value='XXXXX-XXXXX-XXXXX')
        def toggle_key():
            key_var.set(game['key'] if key_var.get().startswith('X') else 'XXXXX-XXXXX-XXXXX')
        
        tk.Label(card, textvariable=key_var, fg='#66C0F4', bg='#1b2838').grid(row=3, column=1, sticky='w')
        tk.Button(card, text="Show Key", command=toggle_key, bg="#2A475E", fg="white").grid(row=3, column=2)
        
        # Status and Note
        tk.Label(card, text="Status:", bg='#1b2838', fg='white').grid(row=0, column=3)
        status = ttk.Combobox(card, values=["In Stock", "Sold"])
        status.set(game.get("status", "In Stock"))
        status.grid(row=0, column=4)
        tk.Label(card, text=f"Note: {game.get('note', '')}", font=('Segoe UI', 9, 'italic'),
                 bg='#1b2838', fg='gray').grid(row=1, column=3, columnspan=2)

# --- Application Entry Point ---

if __name__ == '__main__':
    app = SteamKeyApp()
    app.mainloop()