import tkinter as tk
from tkinter import ttk
import os
import json
import re
import requests
from PIL import Image, ImageTk
from bs4 import BeautifulSoup
import urllib.parse


class SteamKeyLibrary:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Steam Key Library")
        self.root.configure(bg="#1b2838")
        self.root.geometry("1000x700")

        self.games = []
        self.data_file = "games_data.json"
        self.load_data()

        self.create_ui()
        self.root.mainloop()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as file:
                self.games = json.load(file)
        else:
            self.games = []

    def save_data(self):
        with open(self.data_file, "w") as file:
            json.dump(self.games, file, indent=4)

    def create_ui(self):
        top_frame = tk.Frame(self.root, bg="#1b2838")
        top_frame.pack(pady=10)

        add_button = tk.Button(
            top_frame,
            text="+ Add Game",
            command=self.open_add_game_window,
            relief="flat",
            bg="#1b2838",
            fg="#66C0F4",
            activebackground="#1b2838",
            activeforeground="#FFFFFF",
            borderwidth=0,
            font=("Segoe UI", 11, "bold")
        )
        add_button.pack()

        self.games_frame = tk.Frame(self.root, bg="#1b2838")
        self.games_frame.pack(fill="both", expand=True)

        self.refresh_games()

    def refresh_games(self):
        for widget in self.games_frame.winfo_children():
            widget.destroy()

        for index, game in enumerate(self.games):
            frame = tk.Frame(self.games_frame, bg="#2a475e", padx=10, pady=10)
            frame.pack(padx=10, pady=8, fill="x")

            # Fetch and display game image if AppID is known
            appid_match = re.search(r"AppID: (\d+)", game.get("name", ""))
            image_url = None
            if appid_match:
                appid = appid_match.group(1)
                image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/capsule_231x87.jpg"
                try:
                    from io import BytesIO
                    response = requests.get(image_url)
                    image_data = Image.open(BytesIO(response.content)).resize((231, 87))
                    img = ImageTk.PhotoImage(image_data)
                    img_label = tk.Label(frame, image=img, bg="#2a475e")
                    img_label.image = img
                    img_label.pack(side="left", padx=(0, 10))
                except Exception as e:
                    print(f"[ERROR] Failed to load image: {e}")

            info_frame = tk.Frame(frame, bg="#2a475e")
            info_frame.pack(side="left", fill="both", expand=True)

            tk.Label(info_frame, text=f"{index + 1}. {game['name']}", font=("Segoe UI", 12, "bold"), bg="#2a475e", fg="white").pack(anchor="w")
            tk.Label(info_frame, text=f"Bundle: {game['bundle']}", font=("Segoe UI", 10), bg="#2a475e", fg="#c7d5e0").pack(anchor="w")
            tk.Label(info_frame, text=f"Steam Price: {game['steam_price']} | Sale: {game['sale_price']}", font=("Segoe UI", 9), bg="#2a475e", fg="#c7d5e0").pack(anchor="w")
            tk.Label(info_frame, text=f"Status: {game.get('status', 'In Stock')} | Key: {game['key']}", font=("Segoe UI", 9), bg="#2a475e", fg="#b8b8b8").pack(anchor="w")
    def open_add_game_window(self):
        add_win = tk.Toplevel(self.root)
        add_win.title("Add Game")
        add_win.configure(bg="#1b2838")
        add_win.geometry("500x550")

        tk.Label(add_win, text="Game Name", bg="#1b2838", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(10, 2))
        self.game_name_var = tk.StringVar()
        tk.Entry(add_win, textvariable=self.game_name_var, width=40).pack(pady=(0, 10))

        search_btn = tk.Button(
            add_win,
            text="🔍 Search Game",
            command=self.search_steam_game,
            relief="flat",
            bg="#1b2838",
            fg="#66C0F4",
            activebackground="#1b2838",
            activeforeground="#ffffff",
            borderwidth=0
        )
        search_btn.pack()

        self.search_results = tk.Listbox(add_win, width=55, height=5)
        self.search_results.pack(pady=(5, 15))

        load_bundles_btn = tk.Button(
            add_win,
            text="📦 Load Bundles",
            command=self.load_bundles,
            relief="flat",
            bg="#1b2838",
            fg="#66C0F4",
            activebackground="#1b2838",
            activeforeground="#ffffff",
            borderwidth=0
        )
        load_bundles_btn.pack()

        tk.Label(add_win, text="Select Bundle", bg="#1b2838", fg="white", font=("Segoe UI", 10)).pack(pady=(10, 2))
        self.bundle_var = tk.StringVar()
        self.bundle_dropdown = ttk.Combobox(add_win, textvariable=self.bundle_var, width=50, state="readonly")
        self.bundle_dropdown.pack(pady=(0, 15))

        tk.Label(add_win, text="Key", bg="#1b2838", fg="white").pack()
        self.key_var = tk.StringVar()
        tk.Entry(add_win, textvariable=self.key_var, width=40).pack(pady=(0, 15))

        save_btn = tk.Button(
            add_win,
            text="💾 Save Game",
            command=self.save_game,
            relief="flat",
            bg="#1b2838",
            fg="#66C0F4",
            activebackground="#1b2838",
            activeforeground="#ffffff",
            borderwidth=0
        )
        save_btn.pack(pady=10)

    def search_steam_game(self):
        game_name = self.game_name_var.get()
        if not game_name:
            return

        try:
            url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&cc=US&l=en"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            data = response.json()

            self.search_results.delete(0, tk.END)

            for item in data.get("items", []):
                display_text = f"{item['name']} | AppID: {item['id']}"
                self.search_results.insert(tk.END, display_text)

        except Exception as e:
            print(f"[ERROR] Steam search failed: {e}")

    def load_bundles(self):

        game_name = self.search_results.get(tk.ACTIVE).split(" |")[0].strip()
        if not game_name:
            print("[ERROR] No game name provided.")
            return

        try:
            search_url = f"https://isthereanydeal.com/search/?q={urllib.parse.quote(game_name)}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")

            first_result = soup.select_one("a.search__result__title")
            if not first_result:
                print("[ERROR] Game not found on ITAD.")
                return

            slug = first_result.get("href")  # e.g. /game/griftlands/
            bundle_url = f"https://isthereanydeal.com{slug}bundles/"

            res = requests.get(bundle_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")

            bundle_list = soup.select("li.bundle")
            bundles = []

            for bundle in bundle_list:
                name = bundle.select_one("strong")
                date = bundle.select_one("span.date")
                if name and "humble" in name.text.lower():
                    bundle_name = name.text.strip()
                    bundle_date = date.text.strip() if date else ""
                    bundles.append(f"{bundle_name} - {bundle_date}")

            if not bundles:
                bundles = ["No Humble bundles found"]

            self.bundle_dropdown["values"] = bundles
            self.bundle_dropdown.current(0)

        except Exception as e:
            print(f"[ERROR] Bundle scraping failed: {e}")


    def save_game(self):
        name = self.game_name_var.get().strip()
        key = self.key_var.get().strip()
        bundle = self.bundle_var.get().strip()

        if not name or not key:
            print("[INFO] Name and key are required.")
            return

        game_data = {
            "name": name,
            "bundle": bundle,
            "bundle_date": bundle.split(" - ")[-1] if " - " in bundle else "",
            "steam_price": "N/A",
            "sale_price": "N/A",
            "key": key,
            "status": "In Stock",
            "notes": ""
        }

        self.games.append(game_data)
        self.save_data()
        self.refresh_games()

if __name__ == "__main__":
    SteamKeyLibrary()
