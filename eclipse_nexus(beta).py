import os, sys, json, socket, threading, time, string, random, secrets, base64, hashlib, re, subprocess
from datetime import datetime, timezone
from urllib.parse import quote
import hmac

# --- AUTO-INSTALLATION ---
try:
    import requests
    import urllib3
    import phonenumbers
    from phonenumbers import geocoder, carrier
    import customtkinter as ctk
    from PIL import Image
    from PIL.ExifTags import TAGS
    from concurrent.futures import ThreadPoolExecutor

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    print("[!] Dépendances manquantes. Installation en cours...")
    os.system(f"{sys.executable} -m pip install requests urllib3 phonenumbers customtkinter pillow")
    print("[+] Relance le script !")
    sys.exit(0)

# --- CONFIGURATION GUI ---
CTK_BG = "#0B131C"
CTK_PANEL = "#111C26"
CTK_ACCENT = "#00D2FF"
CTK_HOVER = "#0099CC"
CTK_TEXT = "#E0E0E0"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# --- MOTEUR CENTRAL OSINT ---
class EclipseNexus(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ECLIPSE NEXUS // CYBER SUITE 24.0")
        self.geometry("1200x800")
        self.configure(fg_color=CTK_BG)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        
        self.local_ip = self.get_local_ip()
        self.public_ip = "Recherche..."
        self.start_time = time.time()
        self.temp_mail = None
        self.mail_token = None

        self.setup_ui()
        
        # Threads de fond
        threading.Thread(target=self.fetch_public_ip, daemon=True).start()
        self.update_clock()
        self.show_dashboard()

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except: return "127.0.0.1"

    def fetch_public_ip(self):
        try:
            r = self.session.get("https://api64.ipify.org?format=json", timeout=5).json()
            self.public_ip = r["ip"]
            if hasattr(self, 'lbl_public_ip'): self.lbl_public_ip.configure(text=self.public_ip)
        except: pass

    def update_clock(self):
        now = datetime.now(timezone.utc).strftime("%d %b %Y  •  %H:%M:%S UTC")
        if hasattr(self, 'clock_label'): self.clock_label.configure(text=now)
        elapsed = int(time.time() - self.start_time)
        hrs, rem = divmod(elapsed, 3600)
        mins, secs = divmod(rem, 60)
        self.status_label.configure(text=f"PANEL ACTIF  |  IP LOCALE : {self.local_ip}  |  SESSION {hrs:02}:{mins:02}:{secs:02}")
        self.after(1000, self.update_clock)

    def log(self, text, console=None):
        target_console = console if console else self.osint_console
        self.after(0, lambda: target_console.insert("end", str(text) + "\n"))
        self.after(0, lambda: target_console.see("end"))

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=250, fg_color=CTK_PANEL, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(self.sidebar, text="DATA PANEL", font=ctk.CTkFont(size=28, weight="bold"), text_color=CTK_ACCENT).grid(row=0, column=0, padx=20, pady=(20, 5))
        ctk.CTkLabel(self.sidebar, text="CYBER SUITE • 24.0", font=ctk.CTkFont(size=10), text_color="grey").grid(row=1, column=0, padx=20, pady=(0, 20))

        self.btn_dash = self.create_nav_button("Dashboard", 2, self.show_dashboard)
        self.btn_osint = self.create_nav_button("OSINT Universel", 3, self.show_osint)
        self.btn_gen = self.create_nav_button("Générateurs & Lab", 4, self.show_generators)
        self.btn_mail = self.create_nav_button("Boîte Mail Jetable", 5, self.show_mail)

        # 2. MAIN CONTAINER
        self.main_container = ctk.CTkFrame(self, fg_color=CTK_BG, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.setup_dashboard()
        self.setup_osint()
        self.setup_generators()
        self.setup_mail()

        # 3. STATUS BAR
        self.statusbar = ctk.CTkFrame(self, height=30, fg_color=CTK_PANEL, corner_radius=0)
        self.statusbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_label = ctk.CTkLabel(self.statusbar, text="CHARGEMENT...", font=ctk.CTkFont(size=11), text_color=CTK_ACCENT)
        self.status_label.pack(pady=5)

    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=CTK_TEXT, hover_color=CTK_PANEL, anchor="w", command=command, font=ctk.CTkFont(size=14))
        btn.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        return btn

    def show_frame(self, frame_name):
        for frame in self.frames.values(): frame.grid_forget()
        self.frames[frame_name].grid(row=0, column=0, sticky="nsew")

    def show_dashboard(self): self.show_frame("Dashboard")
    def show_osint(self): self.show_frame("OSINT")
    def show_generators(self): self.show_frame("Generators")
    def show_mail(self): self.show_frame("Mail")

    # ================== DASHBOARD ==================
    def setup_dashboard(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Dashboard"] = f
        f.grid_columnconfigure((0,1,2,3), weight=1)
        
        ctk.CTkLabel(f, text="> Dashboard_", font=ctk.CTkFont(size=32, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        self.clock_label = ctk.CTkLabel(f, text="", font=ctk.CTkFont(size=14), text_color=CTK_ACCENT)
        self.clock_label.grid(row=0, column=2, columnspan=2, sticky="e", pady=(0, 20))

        self.lbl_public_ip = self.create_info_panel(f, "MON IPv4", self.public_ip, 1, 0)
        self.create_info_panel(f, "IP LOCALE", self.local_ip, 1, 1)
        self.create_info_panel(f, "MOTEUR", "Red Dead Money", 1, 2)
        self.create_info_panel(f, "MODULES", "34 Actifs", 1, 3)

        radar = ctk.CTkFrame(f, fg_color=CTK_PANEL, border_color=CTK_ACCENT, border_width=1)
        radar.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=20, ipady=80)
        ctk.CTkLabel(radar, text="CYBER DEFENSE // GLOBE TERRESTRE ANIMÉ", text_color=CTK_ACCENT).pack(pady=10)
        self.canvas = ctk.CTkCanvas(radar, width=250, height=250, bg=CTK_PANEL, highlightthickness=0)
        self.canvas.pack(expand=True)
        self.draw_radar()

    def create_info_panel(self, parent, title, value, row, col):
        p = ctk.CTkFrame(parent, fg_color=CTK_PANEL, border_width=1, border_color="#2A3B4C")
        p.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(p, text=title, font=ctk.CTkFont(size=11), text_color="grey").pack(pady=(15, 0))
        val_lbl = ctk.CTkLabel(p, text=value, font=ctk.CTkFont(size=18, weight="bold"))
        val_lbl.pack(pady=(5, 15))
        return val_lbl

    def draw_radar(self):
        w, h = 250, 250
        self.canvas.create_oval(20, 20, w-20, h-20, outline=CTK_ACCENT, width=1)
        self.canvas.create_oval(50, 50, w-50, h-50, outline=CTK_ACCENT, width=1, dash=(2, 4))
        self.canvas.create_oval(80, 80, w-80, h-80, outline=CTK_ACCENT, width=1)
        self.canvas.create_line(w/2, 20, w/2, h-20, fill=CTK_ACCENT, dash=(2,2))
        self.canvas.create_line(20, h/2, w-20, h/2, fill=CTK_ACCENT, dash=(2,2))

    # ================== OSINT UNIVERSEL ==================
    def setup_osint(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["OSINT"] = f
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(f, text="> OSINT & Investigations", font=ctk.CTkFont(size=28, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Outils map
        self.osint_tools = {
            "🌐 Réseau & IP": ["IP Intelligence", "Port Scanner", "Sous-domaines (crt.sh)", "Minecraft Server", "Phone OSINT", "MAC Lookup"],
            "👾 Social & Fuites": ["Username Tracker", "Discord Snowflake", "Discord Invite", "Roblox Tracker", "Minecraft Names", "Steam Tracker", "GTA Online Tracker", "Webhook Analyzer", "Breach Checker (Emails)"],
            "🛠 Web & Forensics": ["Tech Detect", "Unshortener", "Wayback Machine", "Google Dorks", "GitHub Radar", "EXIF Extractor", "Wi-Fi Forensics", "Wordlist Gen"],
            "🎲 Crypto & Avancé": ["Hash & Base64", "JWT Decode", "Crypto Wallet (BTC)", "YT/Twitch OSINT"]
        }

        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=1, column=0, sticky="ew", pady=5)

        self.cat_var = ctk.StringVar(value="🌐 Réseau & IP")
        self.cat_menu = ctk.CTkOptionMenu(top, variable=self.cat_var, values=list(self.osint_tools.keys()), command=self.update_tool_menu, fg_color=CTK_PANEL, button_color=CTK_ACCENT)
        self.cat_menu.pack(side="left", padx=(0, 10))

        self.tool_var = ctk.StringVar()
        self.tool_menu = ctk.CTkOptionMenu(top, variable=self.tool_var, values=self.osint_tools[self.cat_var.get()], fg_color=CTK_PANEL, button_color=CTK_ACCENT)
        self.tool_menu.pack(side="left", padx=10)
        self.update_tool_menu(self.cat_var.get())

        self.target_entry = ctk.CTkEntry(top, placeholder_text="Cible (IP, Domaine, Pseudo, Email, Chemin...)", width=400)
        self.target_entry.pack(side="left", padx=10)

        ctk.CTkButton(top, text="LANCER", fg_color=CTK_ACCENT, text_color="black", hover_color=CTK_HOVER, command=self.execute_osint).pack(side="left", padx=10)

        self.osint_console = ctk.CTkTextbox(f, fg_color=CTK_PANEL, text_color=CTK_ACCENT, font=ctk.CTkFont(family="Consolas", size=13))
        self.osint_console.grid(row=2, column=0, sticky="nsew", pady=10)
        self.log("[*] Console prête. Moteur Red Dead Money initialisé.")

    def update_tool_menu(self, choice):
        self.tool_menu.configure(values=self.osint_tools[choice])
        self.tool_var.set(self.osint_tools[choice][0])

    def execute_osint(self):
        tool = self.tool_var.get()
        target = self.target_entry.get().strip()
        if not target and tool not in ["Wi-Fi Forensics", "Wordlist Gen"]:
            self.log("\n[!] Erreur : Cible manquante.")
            return

        self.log(f"\n[{datetime.now().strftime('%H:%M:%S')}] Exécution : {tool} -> {target if target else 'Local'}")
        self.log("=" * 60)
        threading.Thread(target=self._osint_router, args=(tool, target), daemon=True).start()

    def _osint_router(self, tool, target):
        try:
            # === RÉSEAU ===
            if tool == "IP Intelligence":
                r = self.session.get(f"https://ipwho.is/{target}", timeout=5).json()
                if not r.get("success"): self.log("[-] IP/Domaine invalide.")
                else:
                    self.log(f"IP/Type     : {r.get('ip')} ({r.get('type')})")
                    self.log(f"Localisation: {r.get('city')}, {r.get('region')}, {r.get('country')}")
                    self.log(f"ISP / Org   : {r.get('connection', {}).get('isp')} / {r.get('connection', {}).get('org')}")

            elif tool == "Port Scanner":
                ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389, 8080, 25565]
                self.log("Scan des ports critiques...")
                for p in ports:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    if s.connect_ex((target, p)) == 0: self.log(f"[+] Port {p} OUVERT")
                    s.close()
                self.log("Scan terminé.")

            elif tool == "Sous-domaines (crt.sh)":
                r = self.session.get(f"https://crt.sh/?q=%25.{target}&output=json", timeout=15).json()
                subs = sorted({n.strip().lstrip("*.") for e in r for n in e["name_value"].split("\n")})
                for s in subs[:50]: self.log(s)
                if len(subs) > 50: self.log(f"... et {len(subs)-50} autres trouvés.")

            elif tool == "Minecraft Server":
                r = self.session.get(f"https://api.mcsrvstat.us/2/{target}", timeout=5).json()
                if not r.get("online"): self.log("[-] Serveur hors ligne.")
                else:
                    self.log(f"Version : {r.get('version', 'Inconnue')}")
                    self.log(f"Joueurs : {r.get('players', {}).get('online', 0)} / {r.get('players', {}).get('max', 0)}")
                    self.log(f"Motd    : {' '.join(r.get('motd', {}).get('clean', []))}")

            elif tool == "Phone OSINT":
                p = phonenumbers.parse(target)
                if phonenumbers.is_valid_number(p):
                    self.log(f"Format Int. : {phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}")
                    self.log(f"Pays        : {geocoder.description_for_number(p, 'fr')}")
                    self.log(f"Opérateur   : {carrier.name_for_number(p, 'fr') or 'Fixe/Inconnu'}")
                else: self.log("[-] Numéro invalide.")

            elif tool == "MAC Lookup":
                r = self.session.get(f"https://api.macvendors.com/{quote(target)}", timeout=5)
                if r.status_code == 200: self.log(f"[+] Constructeur : {r.text}")
                else: self.log("[-] MAC inconnue.")

            # === SOCIAL ===
            elif tool == "Username Tracker":
                sites = {
                    "GitHub": f"https://github.com/{target}", "TikTok": f"https://www.tiktok.com/@{target}",
                    "Reddit": f"https://www.reddit.com/user/{target}", "Twitch": f"https://www.twitch.tv/{target}",
                    "Steam": f"https://steamcommunity.com/id/{target}", "Spotify": f"https://open.spotify.com/user/{target}"
                }
                def check(url):
                    try: return url if self.session.get(url, timeout=3).status_code == 200 else None
                    except: return None
                self.log("Scan multi-plateformes en cours...")
                with ThreadPoolExecutor(max_workers=10) as ex:
                    results = ex.map(check, sites.values())
                    for url in results:
                        if url: self.log(f"[+] Trouvé : {url}")
                self.log("Recherche terminée.")

            elif tool == "Discord Snowflake":
                if not target.isdigit(): return self.log("[-] ID invalide.")
                ts = ((int(target) >> 22) + 1420070400000) / 1000
                self.log(f"Création : {datetime.fromtimestamp(ts, timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')}")

            elif tool == "Discord Invite":
                code = target.split("/")[-1]
                r = self.session.get(f"https://discord.com/api/v9/invites/{code}?with_counts=true", timeout=5)
                if r.status_code == 200:
                    d = r.json()
                    self.log(f"Serveur   : {d.get('guild', {}).get('name')}")
                    self.log(f"Membres   : {d.get('approximate_member_count')} (En ligne: {d.get('approximate_presence_count')})")
                else: self.log("[-] Code invalide/expiré.")

            elif tool == "Roblox Tracker":
                r = self.session.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [target], "excludeBannedUsers": False}).json()
                if not r.get("data"): self.log("[-] Joueur introuvable.")
                else:
                    pid = r["data"][0]["id"]
                    i = self.session.get(f"https://users.roblox.com/v1/users/{pid}").json()
                    self.log(f"ID     : {pid}")
                    self.log(f"Pseudo : {i.get('displayName')}")
                    self.log(f"Créé le: {i.get('created', '').split('T')[0]}")
                    self.log(f"Banni  : {'Oui' if i.get('isBanned') else 'Non'}")

            elif tool == "Minecraft Names":
                r = self.session.get(f"https://api.mojang.com/users/profiles/minecraft/{target}", timeout=5)
                if r.status_code != 200: return self.log("[-] Joueur introuvable.")
                uuid, cur = r.json().get("id"), r.json().get("name")
                r2 = self.session.get(f"https://api.mojang.com/user/profiles/{uuid}/names", timeout=5)
                for entry in (r2.json() if r2.status_code==200 else [{"name": cur}]):
                    ts = "Origine" if "changedToAt" not in entry else datetime.fromtimestamp(entry["changedToAt"]/1000, timezone.utc).strftime('%d/%m/%Y')
                    self.log(f"- {entry['name']} ({ts})")

            elif tool == "Steam Tracker":
                url = f"https://steamcommunity.com/profiles/{target}/?xml=1" if target.isdigit() else f"https://steamcommunity.com/id/{target}/?xml=1"
                r = self.session.get(url, timeout=5)
                if "<profile>" in r.text:
                    for k, rgx in [("Nom", r'<steamID><!\[CDATA\[(.*?)\]\]>'), ("SteamID64", r'<steamID64>(.*?)</steamID64>'), ("VAC", r'<vacBanned>(.*?)</vacBanned>')]:
                        m = re.search(rgx, r.text)
                        if m: self.log(f"{k} : {'Banni!' if k=='VAC' and m.group(1)=='1' else m.group(1)}")
                else: self.log("[-] Profil privé ou introuvable.")

            elif tool == "GTA Online Tracker":
                r = self.session.get(f"https://socialclub.rockstargames.com/member/{quote(target)}", timeout=5)
                if r.status_code == 200 and "Page Not Found" not in r.text:
                    self.log("[+] Compte Existant & Actif")
                    self.log(f"URL : https://socialclub.rockstargames.com/member/{quote(target)}")
                else: self.log("[-] Profil introuvable.")

            elif tool == "Webhook Analyzer":
                r = self.session.get(target, timeout=5)
                if r.status_code == 200:
                    d = r.json()
                    self.log(f"Nom      : {d.get('name')}")
                    self.log(f"ServeurID: {d.get('guild_id')} | SalonID: {d.get('channel_id')}")
                else: self.log("[-] Webhook invalide.")

            elif tool == "Breach Checker (Emails)":
                r = self.session.get(f"https://api.xposedornot.com/v1/check-email/{target}", timeout=5)
                if r.status_code == 404: self.log("[+] Email propre, aucune fuite détectée.")
                elif r.status_code == 200:
                    b = r.json().get("breaches", [[]])[0]
                    self.log(f"[!] {len(b)} FUITE(S) DETECTEE(S):")
                    for i in b[:10]: self.log(f"  - {i}")
                else: self.log("[-] Erreur API.")

            # === WEB ===
            elif tool == "Tech Detect":
                if not target.startswith("http"): target = "https://" + target
                r = self.session.get(target, timeout=5)
                blob = (r.text + str(r.headers)).lower()
                sigs = {"WordPress": "wp-content", "Shopify": "cdn.shopify.com", "React": "data-reactroot", "Cloudflare": "cloudflare"}
                found = [n for n, s in sigs.items() if s in blob]
                for h in ("Server", "X-Powered-By"):
                    if h in r.headers: found.append(f"{h}: {r.headers[h]}")
                self.log(f"Tech: {', '.join(found) if found else 'Rien de spécifique'}")

            elif tool == "Unshortener":
                if not target.startswith("http"): target = "https://" + target
                r = self.session.head(target, allow_redirects=True, timeout=5)
                for i, h in enumerate(r.history): self.log(f"Redirection {i+1} : {h.url}")
                self.log(f"Destination Finale : {r.url}")

            elif tool == "Wayback Machine":
                r = self.session.get(f"https://archive.org/wayback/available?url={quote(target)}").json()
                s = r.get("archived_snapshots", {}).get("closest")
                if s: self.log(f"[+] Archive ({s['timestamp']}): {s['url']}")
                else: self.log("[-] Aucune archive.")

            elif tool == "Google Dorks":
                self.log(f"Docs : site:{target} ext:pdf OR ext:doc OR ext:txt")
                self.log(f"SQL  : site:{target} intext:\"sql dump\" OR ext:sql")
                self.log(f"MDP  : site:{target} intext:\"password\"")
                self.log(f"Index: site:{target} intitle:\"index of\"")

            elif tool == "GitHub Radar":
                r = self.session.get(f"https://api.github.com/users/{target}", timeout=5)
                if r.status_code == 200:
                    d = r.json()
                    self.log(f"Nom : {d.get('name')} | Localisation : {d.get('location')}")
                    self.log(f"Dépôts : {d.get('public_repos')} | Email : {d.get('email')}")
                else: self.log("[-] Dev introuvable.")

            elif tool == "EXIF Extractor":
                target = target.strip('"\'')
                if os.path.exists(target):
                    img = Image.open(target)
                    exif = img._getexif()
                    if exif:
                        for tag_id, val in exif.items():
                            tag = TAGS.get(tag_id, tag_id)
                            if tag in ["Make", "Model", "DateTimeOriginal", "Software", "GPSInfo"]:
                                self.log(f"{tag} : {val}")
                    else: self.log("[-] Aucune donnée EXIF.")
                else: self.log("[-] Fichier introuvable.")

            elif tool == "Wi-Fi Forensics":
                if os.name != "nt": return self.log("[-] Exclusif Windows.")
                self.log("Extraction des profils Wi-Fi locaux...")
                raw = subprocess.check_output('netsh wlan show profiles', shell=True).decode('utf-8', errors="backslashreplace")
                profiles = [i.split(":")[1][1:-1] for i in raw.split('\n') if "Profil Tous les utilisateurs" in i or "All User Profile" in i]
                for p in profiles:
                    try:
                        r = subprocess.check_output(f'netsh wlan show profile name="{p}" key=clear', shell=True).decode('utf-8', errors="backslashreplace")
                        pw = [b.split(":")[1][1:-1] for b in r.split('\n') if "Contenu de la cl" in b or "Key Content" in b]
                        self.log(f"SSID: {p} | MDP: {pw[0] if pw else 'Ouvert'}")
                    except: pass
                self.log("Extraction terminée.")

            elif tool == "Wordlist Gen":
                path = os.path.join(os.path.expanduser("~"), ".smart_wordlist.txt")
                with open(path, "w") as f:
                    for i in range(50): f.write(f"wifi{i}2024\n") # Simplifié pour la GUI
                self.log(f"[+] Wordlist basique générée dans {path}")

            # === CRYPTO ===
            elif tool == "Hash & Base64":
                self.log(f"MD5    : {hashlib.md5(target.encode()).hexdigest()}")
                self.log(f"SHA256 : {hashlib.sha256(target.encode()).hexdigest()}")
                self.log(f"B64 Enc: {base64.b64encode(target.encode()).decode()}")

            elif tool == "JWT Decode":
                for i, part in enumerate(target.split(".")[:2]):
                    data = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
                    self.log(f"Partie {i+1} : {json.dumps(data)}")

            elif tool == "Crypto Wallet (BTC)":
                r = self.session.get(f"https://blockchain.info/rawaddr/{target}", timeout=5)
                if r.status_code == 200:
                    d = r.json()
                    self.log(f"Transactions : {d.get('n_tx')}")
                    self.log(f"Solde Actuel : {d.get('final_balance', 0) / 100000000} BTC")
                else: self.log("[-] Adresse invalide.")

            elif tool == "YT/Twitch OSINT":
                for plat, url in [("Twitch", f"https://www.twitch.tv/{target}"), ("YouTube", f"https://www.youtube.com/@{target}")]:
                    try:
                        r = self.session.get(url, timeout=5)
                        if r.status_code == 200 and "is not available" not in r.text and "404 Not Found" not in r.text:
                            self.log(f"[+] {plat} : Trouvé ({url})")
                        else: self.log(f"[-] {plat} : Introuvable")
                    except: self.log(f"[!] Erreur connexion {plat}")

        except Exception as e:
            self.log(f"[!] Erreur critique : {str(e)}")

    # ================== GÉNÉRATEURS & LAB ==================
    def setup_generators(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Generators"] = f
        f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(f, text="> Cyber Lab & Générateurs", font=ctk.CTkFont(size=28, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Box Password & PIN
        b1 = ctk.CTkFrame(f, fg_color=CTK_PANEL)
        b1.grid(row=1, column=0, sticky="ew", pady=10, ipady=10)
        ctk.CTkLabel(b1, text="Générateurs Sécurisés (MDP & PIN)").pack(pady=5)
        self.gen_len = ctk.CTkSlider(b1, from_=4, to=64, number_of_steps=60)
        self.gen_len.set(16)
        self.gen_len.pack(pady=10)
        
        btn_frame = ctk.CTkFrame(b1, fg_color="transparent")
        btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="MDP", fg_color=CTK_ACCENT, text_color="black", command=lambda: self.run_gen("mdp")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="PIN", fg_color=CTK_ACCENT, text_color="black", command=lambda: self.run_gen("pin")).pack(side="left", padx=5)
        
        self.gen_output = ctk.CTkEntry(b1, width=300, justify="center")
        self.gen_output.pack(pady=10)

        # Box Pseudo & Identity
        b2 = ctk.CTkFrame(f, fg_color=CTK_PANEL)
        b2.grid(row=2, column=0, sticky="ew", pady=10, ipady=10)
        ctk.CTkLabel(b2, text="Générateurs d'Identités").pack(pady=5)
        
        btn_frame2 = ctk.CTkFrame(b2, fg_color="transparent")
        btn_frame2.pack(pady=5)
        ctk.CTkButton(btn_frame2, text="PSEUDO GAMING", fg_color=CTK_ACCENT, text_color="black", command=lambda: self.run_gen("pseudo")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame2, text="FAUSSE IDENTITÉ", fg_color=CTK_ACCENT, text_color="black", command=lambda: self.run_gen("ident")).pack(side="left", padx=5)
        
        self.gen_console = ctk.CTkTextbox(b2, height=100)
        self.gen_console.pack(fill="x", padx=20, pady=10)

    def run_gen(self, gtype):
        length = int(self.gen_len.get())
        if gtype == "mdp":
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            pw = "".join(secrets.choice(alphabet) for _ in range(length))
            self.gen_output.delete(0, 'end'); self.gen_output.insert(0, pw)
        elif gtype == "pin":
            pin = "".join(secrets.choice(string.digits) for _ in range(length))
            self.gen_output.delete(0, 'end'); self.gen_output.insert(0, pin)
        elif gtype == "pseudo":
            adj = ["Dark", "Silent", "Crimson", "Shadow", "Toxic", "Frozen", "Cyber", "Ghost", "Neon"]
            noun = ["Wolf", "Demon", "Tiger", "Phantom", "Raven", "Viper", "Hunter", "Ninja", "Reaper"]
            ps = f"{random.choice(adj)}{random.choice(noun)}{random.randint(0, 999)}"
            self.gen_console.delete("1.0", "end"); self.gen_console.insert("end", f"Pseudo généré : {ps}")
        elif gtype == "ident":
            f, l = random.choice(["Lucas", "Emma", "Hugo", "Léa"]), random.choice(["Martin", "Bernard", "Dubois", "Petit"])
            mail = f"{f.lower()}.{l.lower()}{random.randint(10,99)}@proton.me"
            tel = "06 " + " ".join(f"{random.randint(0, 99):02}" for _ in range(4))
            self.gen_console.delete("1.0", "end")
            self.gen_console.insert("end", f"Nom : {f} {l}\nEmail : {mail}\nTel : {tel}")

    # ================== BOÎTE MAIL JETABLE ==================
    def setup_mail(self):
        f = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Mail"] = f
        f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(f, text="> Boîte Mail Jetable (API Mail.tm)", font=ctk.CTkFont(size=28, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20))

        btn_f = ctk.CTkFrame(f, fg_color="transparent")
        btn_f.grid(row=1, column=0, pady=10)
        ctk.CTkButton(btn_f, text="GÉNÉRER ADRESSE", fg_color=CTK_ACCENT, text_color="black", command=self.run_temp_mail).pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="RECHARGER BOÎTE", border_color=CTK_ACCENT, border_width=1, fg_color="transparent", command=self.refresh_temp_mail).pack(side="left", padx=10)

        self.mail_address_lbl = ctk.CTkLabel(f, text="Aucune adresse active", font=ctk.CTkFont(size=20, weight="bold"), text_color=CTK_ACCENT)
        self.mail_address_lbl.grid(row=2, column=0, pady=10)

        self.mail_console = ctk.CTkTextbox(f, fg_color=CTK_PANEL, text_color="white")
        self.mail_console.grid(row=3, column=0, sticky="nsew", pady=10)
        f.grid_rowconfigure(3, weight=1)

    def run_temp_mail(self):
        self.mail_console.delete("1.0", "end")
        self.log("[*] Création du compte Mail.tm...", self.mail_console)
        threading.Thread(target=self._mail_gen_thread, daemon=True).start()

    def _mail_gen_thread(self):
        try:
            d_req = self.session.get("https://api.mail.tm/domains", timeout=5)
            if d_req.status_code == 200:
                domain = d_req.json()['hydra:member'][0]['domain']
                user = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
                pw = secrets.token_hex(8)
                email = f"{user}@{domain}"
                
                c_req = self.session.post("https://api.mail.tm/accounts", json={"address": email, "password": pw}, timeout=5)
                if c_req.status_code in [200, 201]:
                    t_req = self.session.post("https://api.mail.tm/token", json={"address": email, "password": pw}, timeout=5)
                    if t_req.status_code == 200:
                        self.temp_mail = email
                        self.mail_token = t_req.json().get('token')
                        self.after(0, lambda: self.mail_address_lbl.configure(text=self.temp_mail))
                        self.log(f"[+] Boîte prête ! Utilise {email}", self.mail_console)
                        return
            self.log("[-] Échec de la génération API.", self.mail_console)
        except Exception as e: self.log(f"[!] Erreur : {e}", self.mail_console)

    def refresh_temp_mail(self):
        if not self.temp_mail: return self.log("[!] Générez d'abord une adresse.", self.mail_console)
        threading.Thread(target=self._mail_refresh_thread, daemon=True).start()

    def _mail_refresh_thread(self):
        self.log("[*] Vérification de la boîte...", self.mail_console)
        try:
            r = self.session.get("https://api.mail.tm/messages", headers={"Authorization": f"Bearer {self.mail_token}"}, timeout=5)
            if r.status_code == 200:
                msgs = r.json().get('hydra:member', [])
                if not msgs: self.log("[-] Aucun nouveau message.", self.mail_console)
                else:
                    for m in msgs:
                        self.log(f"\n--- REÇU DE : {m['from']['address']} ---", self.mail_console)
                        self.log(f"Sujet : {m['subject']}", self.mail_console)
            else: self.log("[-] Erreur de rafraîchissement.", self.mail_console)
        except Exception as e: self.log(f"[!] Erreur : {e}", self.mail_console)

if __name__ == "__main__":
    app = EclipseNexus()
    app.mainloop()