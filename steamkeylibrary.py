import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
import json
import os
import io

# --- Constants ---
DATA_FILE = 'games.json'
ITAD_API_KEY = "566d3cdbf46de940ccda93b954bb5d18dbf1d053"

# --- API Interaction Functions ---

def get_steam_appid_by_name(game_name):
    """Fetches the Steam AppID for a given game name from the Steam API."""
    try:
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        response = requests.get(url)
        data = response.json()
        for app in data['applist']['apps']:
            if app['name'].lower() == game_name.lower():
                return app['appid']
        return None
    except Exception as e:
        print(f"Erro ao obter AppID: {e}")
        return None

def get_steam_price_and_image(appid, cc="pt"):
    """Fetches price details and header image URL from the Steam store API."""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={cc}&l=en"
        response = requests.get(url)
        data = response.json()
        info = data[str(appid)]['data']
        price_data = info.get("price_overview", {})
        final = price_data.get("final", 0) / 100
        regular = price_data.get("initial", final * 100) / 100
        image_url = info.get("header_image", f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg")
        return {
            "steam_price": f"{final:.2f}",
            "regular_price": f"{regular:.2f}",
            "image_url": image_url
        }
    except Exception as e:
        print(f"Erro ao obter preços/imagem da Steam: {e}")
        return {
            "steam_price": "0.00",
            "regular_price": "0.00",
            "image_url": None
        }

def get_itad_plain_id(appid):
    """Gets the IsThereAnyDeal (ITAD) 'plain' ID for a game using its Steam AppID."""
    try:
        url = f"https://api.isthereanydeal.com/v02/game/plain/id/?key={ITAD_API_KEY}&shop=steam&ids=app/{appid}"
        response = requests.get(url)
        data = response.json()

        if 'data' not in data or not data['data']:
            print("Resposta da API ITAD não contém dados válidos.")
            return None

        return list(data['data'].values())[0]
    except Exception as e:
        print(f"Erro ao obter plain ID do ITAD: {e}")
        return None

def get_bundles_for_game(itad_plain):
    """Fetches a list of historical bundles a game was included in from the ITAD API."""
    try:
        url = f"https://api.isthereanydeal.com/v1/game/bundles/?key={ITAD_API_KEY}&plain={itad_plain}&expired=1"
        response = requests.get(url)
        bundles = response.json()['data']['bundles']
        return [
            {
                "title": bundle['title'],
                "date": bundle.get('start', '')[:10]
            }
            for bundle in bundles
        ]
    except Exception as e:
        print(f"Erro ao obter bundles do ITAD: {e}")
        return []

# --- GUI Helper Functions ---

def select_bundle_popup(bundle_list, callback):
    """Creates a popup window for the user to select a bundle from a list."""
    popup = tk.Toplevel()
    popup.title("Select Bundle")
    popup.configure(bg="#1b2838")
    popup.geometry("400x300")
    tk.Label(popup, text="Choose the bundle this game came from:", bg="#1b2838", fg="white").pack(pady=10)
    listbox = tk.Listbox(popup, height=10, width=50)
    listbox.pack(padx=10, pady=5)
    for bundle in bundle_list:
        listbox.insert(tk.END, f"{bundle['title']} ({bundle['date']})")
    def on_select():
        index = listbox.curselection()
        if index:
            selected = bundle_list[index[0]]
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
        self.games = load_games()
        
        # Setup for scrollable frame
        self.canvas = tk.Canvas(self, bg='#171a21')
        self.frame = tk.Frame(self.canvas, bg='#171a21')
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.frame, anchor='nw')
        
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Main UI elements
        tk.Button(self, text="Add Game", command=self.add_game_workflow, bg="#66C0F4").pack(fill="x")
        
        # Load and display existing games
        for game in self.games:
            self.add_card(game)

    def add_game_workflow(self):
        """Guides the user through the multi-step process of adding a new game."""
        add_win = tk.Toplevel(self)
        add_win.title("Add Game")
        add_win.configure(bg="#1b2838")
        
        tk.Label(add_win, text="Game Name:", bg="#1b2838", fg="white").pack(pady=5)
        name_entry = tk.Entry(add_win, width=40)
        name_entry.pack(pady=5)
        
        def continue_process():
            game_name = name_entry.get()
            if not game_name:
                messagebox.showerror("Error", "Please enter a game name.")
                return
            
            appid = get_steam_appid_by_name(game_name)
            if not appid:
                messagebox.showerror("Error", "Game not found on Steam.")
                return
                
            steam_data = get_steam_price_and_image(appid)
            itad_plain = get_itad_plain_id(appid)
            if not itad_plain:
                messagebox.showerror("Error", "Could not find game on IsThereAnyDeal.")
                return
            
            bundle_list = get_bundles_for_game(itad_plain)
            if not bundle_list:
                messagebox.showerror("Error", "No bundles found for this game.")
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

            select_bundle_popup(bundle_list, after_bundle_selected)

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
