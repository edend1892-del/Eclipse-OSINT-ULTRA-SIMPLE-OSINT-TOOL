#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSE OSINT - Powered by Red Dead Money Core
"""

import os, sys, json, time, socket, base64, hashlib, secrets, string, random, re, subprocess
from datetime import datetime, timezone
import hmac
from urllib.parse import quote, urlparse
from concurrent.futures import ThreadPoolExecutor

# --- SYSTÈME D'AUTO-INSTALLATION ---
try:
    import requests
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone as ph_tz
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress
    from rich.prompt import Prompt, IntPrompt
    from rich.text import Text
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("[!] Dépendances manquantes détectées.")
    print("[*] Installation automatique en cours, patiente quelques secondes…")
    import os, sys
    os.system(f"{sys.executable} -m pip install requests rich phonenumbers pillow")
    print("[+] Installation terminée avec succès ! Relance le script.")
    sys.exit(0)
# -----------------------------------

USERS_FILE = os.path.join(os.path.expanduser("~"), ".eclipse_users.json")
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".eclipse_config.json")
TIMEOUT = 5
EMAIL_PROVIDERS = ["gmail.com", "outlook.com", "yahoo.fr", "proton.me", "icloud.com", "hotmail.com", "live.fr"]

# --- DICTIONNAIRE DE TRADUCTION ---
TRANSLATIONS = {
    "fr": {
        "active_agent": "Agent actif",
        "restricted_access": "Accès restreint",
        "login": "Se connecter",
        "register": "Créer un compte",
        "quit": "Quitter",
        "choice": "Choix",
        "username": "Identifiant",
        "password": "Mot de passe",
        "new_username": "Nouvel Identifiant",
        "new_password": "Nouveau Mot de passe",
        "access_denied": "Accès refusé.",
        "account_created": "Compte agent créé !",
        "error_account": "Erreur (déjà pris ou mdp trop court).",
        "save_error": "Erreur de sauvegarde.",
        "connected": "Connexion établie, {} !",
        "settings": "Paramètres (Thème & Langue)",
        "settings_title": "Paramètres de l'Interface",
        "theme_updated": "Thème mis à jour !",
        "lang_updated": "Langue mise à jour avec succès !",
        "back": "Retour",
        "press_enter": "Appuie sur Entrée pour continuer...",
        "menu_osint": "🌐 OSINT & Réseau",
        "menu_social": "👾 Social, Gaming & Fuites",
        "menu_web": "🛠 Web & Forensics",
        "menu_crypto": "🎲 Générateurs & Crypto"
    },
    "en": {
        "active_agent": "Active Agent",
        "restricted_access": "Restricted Access",
        "login": "Login",
        "register": "Create Account",
        "quit": "Exit",
        "choice": "Choice",
        "username": "Username",
        "password": "Password",
        "new_username": "New Username",
        "new_password": "New Password",
        "access_denied": "Access denied.",
        "account_created": "Agent account created!",
        "error_account": "Error (already taken or password too short).",
        "save_error": "Saving error.",
        "connected": "Connection established, {}!",
        "settings": "Settings (Theme & Language)",
        "settings_title": "Interface Settings",
        "theme_updated": "Theme updated!",
        "lang_updated": "Language successfully updated!",
        "back": "Back",
        "press_enter": "Press Enter to continue...",
        "menu_osint": "🌐 OSINT & Network",
        "menu_social": "👾 Social, Gaming & Leaks",
        "menu_web": "🛠 Web & Forensics",
        "menu_crypto": "🎲 Generators & Crypto"
    }
}

class EclipseOSINT:
    def __init__(self):
        self.console = Console()
        self.load_config()
        self.text_theme = "bold white"
        self.dim_theme = "bold grey50"
        self.current_user = None
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Eclipse/RDM-Core"})

    def tr(self, key):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["fr"]).get(key, key)

    def load_config(self):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
                self.theme = data.get("theme", "bold cyan")
                self.lang = data.get("lang", "fr")
        except:
            self.theme = "bold cyan"
            self.lang = "fr"

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"theme": self.theme, "lang": self.lang}, f)
        except: pass

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def banner(self):
        self.clear()
        b = f"""
███████╗ ██████╗██╗     ██╗██████╗ ███████╗███████╗
██╔════╝██╔════╝██║     ██║██╔══██╗██╔════╝██╔════╝
█████╗  ██║     ██║     ██║██████╔╝███████╗█████╗  
██╔══╝  ██║     ██║     ██║██╔═══╝ ╚════██║██╔══╝  
███████╗╚██████╗███████╗██║██║     ███████║███████╗
╚══════╝ ╚═════╝╚══════╝╚═╝╚═╝     ╚══════╝╚══════╝
        """
        self.console.print(Text(b, style=self.theme, justify="center"))
        status = f"{self.tr('active_agent')}: {self.current_user}" if self.current_user else self.tr("restricted_access")
        self.console.print(Panel(f"[{self.text_theme}]Eclipse OSINT - Ultra Simple Tool v4.7[/] | [{self.theme}]Moteur: Red Dead Money[/] | [{self.dim_theme}]{status}[/]", style=self.theme, expand=False), justify="center")
        print("\n")

    def error(self, msg): self.console.print(f"[{self.theme}][!][/] {msg}")
    def success(self, msg): self.console.print(f"[bold green][+][/] {msg}")

    # ================= SYSTÈmes DE COMPTES =================
    def hash_pw(self, password, salt=None):
        salt = salt or secrets.token_bytes(16)
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
        return salt.hex(), h.hex()

    def auth_screen(self):
        while not self.current_user:
            self.banner()
            t = Table(show_header=False, box=None)
            t.add_row(f"[{self.theme}][1][/]", self.tr("login"))
            t.add_row(f"[{self.theme}][2][/]", self.tr("register"))
            t.add_row(f"[{self.theme}][0][/]", self.tr("quit"))
            self.console.print(t)
            
            c = Prompt.ask(f"\n[{self.theme}]{self.tr('choice')}[/]")
            if c == "0": sys.exit(0)
            
            try:
                with open(USERS_FILE, encoding="utf-8") as f: users = json.load(f)
            except: users = {}

            if c == "1":
                name = Prompt.ask(self.tr("username"))
                pw = Prompt.ask(self.tr("password"))
                u = users.get(name)
                if u:
                    _, h = self.hash_pw(pw, bytes.fromhex(u["salt"]))
                    if hmac.compare_digest(h, u["hash"]):
                        self.current_user = name
                        self.success(self.tr("connected").format(name)); time.sleep(1)
                        return
                self.error(self.tr("access_denied")); time.sleep(1.5)
            elif c == "2":
                name = Prompt.ask(self.tr("new_username"))
                pw = Prompt.ask(self.tr("new_password"))
                if len(pw) < 6 or name in users:
                    self.error(self.tr("error_account")); time.sleep(1.5); continue
                salt, h = self.hash_pw(pw)
                users[name] = {"salt": salt, "hash": h, "created": datetime.now().strftime("%d/%m/%Y")}
                try:
                    with open(USERS_FILE, "w", encoding="utf-8") as f: json.dump(users, f)
                    self.success(self.tr("account_created")); time.sleep(1.5)
                except: self.error(self.tr("save_error")); time.sleep(1.5)

    # ================= 1. OSINT & RÉSEAU =================
    def module_ip_info(self):
        ip = Prompt.ask(f"[{self.theme}]IP ou Domaine[/]")
        try:
            r = self.session.get(f"https://ipwho.is/{ip}", timeout=TIMEOUT).json()
            if not r.get("success"): return self.error("Invalide.")
            t = Table(title="IP Intelligence", style=self.theme)
            t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
            t.add_row("IP / Type", f"{r.get('ip')} ({r.get('type')})")
            t.add_row("Localisation", f"{r.get('city')}, {r.get('region')}, {r.get('country')}")
            t.add_row("ISP / Org", f"{r.get('connection', {}).get('isp')} / {r.get('connection', {}).get('org')}")
            self.console.print(t)
        except Exception as e: self.error(str(e))

    def module_minecraft_osint(self):
        ip = Prompt.ask(f"[{self.theme}]IP du serveur Minecraft[/]")
        try:
            r = self.session.get(f"https://api.mcsrvstat.us/2/{ip}", timeout=TIMEOUT).json()
            if not r.get("online"): return self.error("Serveur hors ligne ou introuvable.")
            t = Table(title=f"Minecraft OSINT : {ip}", style=self.theme)
            t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
            t.add_row("Version", r.get("version", "Inconnue"))
            t.add_row("Joueurs", f"{r.get('players', {}).get('online', 0)} / {r.get('players', {}).get('max', 0)}")
            motd = r.get("motd", {}).get("clean", [""])
            t.add_row("MOTD", "\n".join(motd)[:100])
            t.add_row("Logiciel/Modpack", r.get("software", "Vanilla/Inconnu"))
            self.console.print(t)
        except Exception as e: self.error(str(e))

    def module_port_scanner(self):
        ip = Prompt.ask(f"[{self.theme}]IP à scanner[/]")
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389, 8080, 25565]
        t = Table(title=f"Port Scanner (Red Dead Money) : {ip}", style=self.theme)
        t.add_column("Port", justify="center", style=self.theme); t.add_column("État", justify="center")
        self.console.print(f"[{self.dim_theme}]Scan en cours des ports critiques...[/]")
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, port))
            if result == 0:
                t.add_row(str(port), "[bold green]OUVERT[/]")
            sock.close()
        self.console.print(t)

    def module_subdomains(self):
        d = Prompt.ask(f"[{self.theme}]Domaine cible[/]")
        try:
            self.console.print(f"[{self.dim_theme}]Recherche via crt.sh (peut prendre du temps)...[/]")
            r = self.session.get(f"https://crt.sh/?q=%25.{d}&output=json", timeout=20).json()
            subs = sorted({n.strip().lstrip("*.") for e in r for n in e["name_value"].split("\n")})
            t = Table(title=f"Sous-domaines : {d}", style=self.theme)
            t.add_column("Sous-domaine", style=self.text_theme)
            for s in subs[:50]: t.add_row(s)
            self.console.print(t)
            if len(subs) > 50: self.console.print(f"[{self.theme}]+ {len(subs)-50} autres (limité à 50)[/]")
        except Exception as e: self.error(str(e))

    def module_phone_osint(self):
        num = Prompt.ask(f"[{self.theme}]Numéro (ex: +33612345678)[/]")
        try:
            p = phonenumbers.parse(num)
            if not phonenumbers.is_valid_number(p): return self.error("Numéro invalide.")
            t = Table(title="Phone Intelligence", style=self.theme)
            t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
            t.add_row("Format International", phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
            t.add_row("Pays", geocoder.description_for_number(p, "fr"))
            t.add_row("Opérateur", carrier.name_for_number(p, "fr") or "Inconnu/Fixe")
            self.console.print(t)
        except Exception as e: self.error(str(e))

    def module_mac_lookup(self):
        mac = Prompt.ask(f"[{self.theme}]Adresse MAC ou Préfixe (ex: 00:1A:2B)[/]")
        try:
            r = self.session.get(f"https://api.macvendors.com/{quote(mac)}", timeout=TIMEOUT)
            t = Table(title=f"MAC Vendor Lookup : {mac}", style=self.theme)
            t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
            if r.status_code == 200:
                t.add_row("Constructeur / Marque", f"[bold green]{r.text}[/]")
            else:
                t.add_row("Résultat", "[bold red]Constructeur inconnu ou format invalide[/]")
            self.console.print(t)
        except Exception as e: self.error(str(e))

    # ================= 2. SOCIAL, GAMING & FUITES =================
    def module_username_tracker(self):
        u = Prompt.ask(f"[{self.theme}]Pseudo cible[/]")
        sites = {
            "GitHub": f"https://github.com/{u}", "TikTok": f"https://www.tiktok.com/@{u}",
            "Reddit": f"https://www.reddit.com/user/{u}", "Twitch": f"https://www.twitch.tv/{u}",
            "SoundCloud": f"https://soundcloud.com/{u}", "Steam": f"https://steamcommunity.com/id/{u}",
            "Spotify": f"https://open.spotify.com/user/{u}", "Pinterest": f"https://www.pinterest.com/{u}/"
        }
        found = []
        def check(name, url):
            try:
                if self.session.get(url, timeout=TIMEOUT).status_code == 200: return name, url
            except: pass
            return None

        with Progress() as prog:
            task = prog.add_task(f"[{self.theme}]Recherche Asynchrone...", total=len(sites))
            with ThreadPoolExecutor(max_workers=10) as ex:
                for f in [ex.submit(check, n, url) for n, url in sites.items()]:
                    res = f.result()
                    if res: found.append(res)
                    prog.advance(task)
        
        t = Table(title=f"Profils trouvés : {u}", style=self.theme)
        t.add_column("Site", style=self.text_theme); t.add_column("Lien", style="cyan")
        for n, l in found: t.add_row(n, l)
        self.console.print(t) if found else self.error("Aucun profil trouvé.")

    def module_discord_snowflake(self):
        s = Prompt.ask(f"[{self.theme}]ID Discord[/]")
        if not s.isdigit(): return self.error("ID invalide.")
        ts = ((int(s) >> 22) + 1420070400000) / 1000
        t = Table(title="Discord Snowflake", style=self.theme)
        t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
        t.add_row("Date de création", datetime.fromtimestamp(ts, timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC"))
        t.add_row("Worker / Process", f"{(int(s) >> 17) & 31} / {(int(s) >> 12) & 31}")
        self.console.print(t)

    def module_discord_invite(self):
        code = Prompt.ask(f"[{self.theme}]Code ou Lien d'invitation Discord[/]")
        code = code.split("/")[-1].strip()
        try:
            r = self.session.get(f"https://discord.com/api/v9/invites/{code}?with_counts=true", timeout=TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                guild = data.get("guild", {})
                t = Table(title=f"Discord Invite Recon : {code}", style=self.theme)
                t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
                t.add_row("Nom du Serveur", guild.get("name", "N/A"))
                t.add_row("ID du Serveur", guild.get("id", "N/A"))
                t.add_row("Membres Totaux", str(data.get("approximate_member_count", "N/A")))
                t.add_row("Membres en Ligne", str(data.get("approximate_presence_count", "N/A")))
                t.add_row("Description", guild.get("description", "Aucune"))
                self.console.print(t)
            else:
                self.error("Invitation invalide, expirée ou introuvable.")
        except Exception as e: self.error(str(e))

    def module_roblox_tracker(self):
        u = Prompt.ask(f"[{self.theme}]Pseudo Roblox[/]")
        try:
            r = self.session.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [u], "excludeBannedUsers": False}).json()
            if not r.get("data"): return self.error("Joueur introuvable.")
            pid = r["data"][0]["id"]
            infos = self.session.get(f"https://users.roblox.com/v1/users/{pid}").json()
            t = Table(title=f"Roblox Player: {u}", style=self.theme)
            t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
            t.add_row("ID Joueur", str(pid))
            t.add_row("Nom d'affichage", infos.get("displayName", "N/A"))
            date_create = infos.get("created", "N/A").split("T")[0]
            t.add_row("Créé le", date_create)
            t.add_row("Banni", "Oui" if infos.get("isBanned") else "Non")
            self.console.print(t)
        except Exception as e: self.error(str(e))

    def module_minecraft_names(self):
        u = Prompt.ask(f"[{self.theme}]Pseudo Minecraft (actuel ou ancien)[/]")
        try:
            r = self.session.get(f"https://api.mojang.com/users/profiles/minecraft/{u}", timeout=TIMEOUT)
            if r.status_code != 200: return self.error("Joueur introuvable.")
            data = r.json()
            uuid = data.get("id")
            current_name = data.get("name")
            
            r2 = self.session.get(f"https://api.mojang.com/user/profiles/{uuid}/names", timeout=TIMEOUT)
            names = r2.json() if r2.status_code == 200 else [{"name": current_name}]
            
            t = Table(title=f"Historique Pseudos Minecraft : {current_name}", style=self.theme)
            t.add_column("Pseudo", style=self.theme); t.add_column("Date de changement", style=self.text_theme)
            for entry in names:
                changed_at = "Pseudo d'origine"
                if "changedToAt" in entry:
                    ts = entry["changedToAt"] / 1000
                    changed_at = datetime.fromtimestamp(ts, timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
                t.add_row(entry.get("name"), changed_at)
            self.console.print(t)
        except Exception as e: self.error(str(e))

    def module_steam_checker(self):
        u = Prompt.ask(f"[{self.theme}]SteamID64 ou Custom ID (ex: gaben)[/]")
        url = f"https://steamcommunity.com/id/{u}/?xml=1" if not u.isdigit() else f"https://steamcommunity.com/profiles/{u}/?xml=1"
        try:
            r = self.session.get(url, timeout=TIMEOUT)
            if r.status_code == 200 and "<profile>" in r.text:
                t = Table(title=f"Steam OSINT & VAC Checker : {u}", style=self.theme)
                t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
                
                s_name = re.search(r'<steamID><!\[CDATA\[(.*?)\]\]></steamID>', r.text)
                if s_name: t.add_row("Nom du Profil", s_name.group(1))
                
                s_id64 = re.search(r'<steamID64>(.*?)</steamID64>', r.text)
                if s_id64: t.add_row("SteamID64", s_id64.group(1))
                
                state = re.search(r'<onlineState><!\[CDATA\[(.*?)\]\]></onlineState>', r.text)
                if state: t.add_row("État en ligne", state.group(1))
                
                privacy = re.search(r'<privacyState><!\[CDATA\[(.*?)\]\]></privacyState>', r.text)
                if privacy: t.add_row("Visibilité", privacy.group(1))
                
                vac = re.search(r'<vacBanned>(.*?)</vacBanned>', r.text)
                if vac:
                    banned = vac.group(1) == "1"
                    t.add_row("VAC Banned", "[bold red]OUI (Banni pour triche)[/]" if banned else "[bold green]NON (Propre)[/]")
                
                self.console.print(t)
            else:
                self.error("Profil Steam introuvable ou privé.")
        except Exception as e: self.error(str(e))

    def module_gta_tracker(self):
        u = Prompt.ask(f"[{self.theme}]Pseudo Rockstar / FiveM[/]")
        self.console.print(f"[{self.dim_theme}]Interrogation des bases de données Rockstar...[/]")
        url = f"https://socialclub.rockstargames.com/member/{quote(u)}"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(url, headers=headers, timeout=TIMEOUT)
            if r.status_code == 200 and "Page Not Found" not in r.text:
                t = Table(title=f"GTA Online & RP Tracker (Deep Scan) : {u}", style=self.theme)
                t.add_column("Donnée extraite", style=self.theme); t.add_column("Valeur", style=self.text_theme)
                t.add_row("Statut du Compte", "[bold green]Existant & Actif[/]")
                t.add_row("URL Rockstar", url)
                avatar = re.search(r'<meta property="og:image" content="(.*?)"', r.text)
                if avatar and "rockstargames.com" in avatar.group(1):
                    t.add_row("Avatar (Photo URL)", avatar.group(1))
                t.add_row("Niveau (GTA Online)", "[bold yellow]Verrouillé par l'API Rockstar (Nécessite Auth Token)[/]")
                t.add_row("Info GTA RP (FiveM)", "Les niveaux RP sont hébergés sur les bases MySQL privées des serveurs.")
                self.console.print(t)
            else:
                self.error("Cible introuvable ou profil totalement supprimé.")
        except Exception as e:
            self.error(f"Erreur de connexion : {str(e)}")

    def module_webhook_analyzer(self):
        url = Prompt.ask(f"[{self.theme}]URL du Webhook Discord[/]")
        try:
            r = self.session.get(url, timeout=TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                t = Table(title="Analyse de Webhook Discord", style=self.theme)
                t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
                t.add_row("Nom du Webhook", data.get("name", "N/A"))
                t.add_row("ID du Serveur (Guild)", data.get("guild_id", "N/A"))
                t.add_row("ID du Salon (Channel)", data.get("channel_id", "N/A"))
                user = data.get("user", {})
                if user:
                    t.add_row("Créé par", f"{user.get('username')}#{user.get('discriminator')} (ID: {user.get('id')})")
                self.console.print(t)
            else:
                self.error("Webhook invalide ou supprimé.")
        except Exception as e: self.error(str(e))

    def module_breach_checker(self):
        email = Prompt.ask(f"[{self.theme}]Email à vérifier[/]")
        try:
            r = self.session.get(f"https://api.xposedornot.com/v1/check-email/{email}", timeout=TIMEOUT)
            if r.status_code == 404:
                self.success("Aucune fuite de données trouvée pour cet email !")
            elif r.status_code == 200:
                data = r.json()
                breaches = data.get("breaches", [[]])[0]
                self.error(f"FUITE DÉTECTÉE ! L'email est présent dans {len(breaches)} base(s) de données.")
                for b in breaches[:10]: self.console.print(f"[{self.theme}]-[/] {b}")
            else: self.error(f"Erreur API ({r.status_code})")
        except Exception as e: self.error(str(e))

    # ================= 3. WEB & FORENSICS =================
    def module_tech_detect(self):
        u = Prompt.ask(f"[{self.theme}]URL[/]")
        if not u.startswith("http"): u = "https://" + u
        sigs = {"WordPress": "wp-content", "Shopify": "cdn.shopify.com", "React": "data-reactroot", "Cloudflare": "cloudflare"}
        try:
            r = self.session.get(u, timeout=TIMEOUT)
            blob = (r.text + str(r.headers)).lower()
            found = [n for n, s in sigs.items() if s.lower() in blob]
            for h in ("Server", "X-Powered-By"):
                if h in r.headers: found.append(f"{h}: {r.headers[h]}")
            t = Table(title="Technologies Détectées", style=self.theme)
            t.add_column("Technologie", style=self.text_theme)
            for f in found: t.add_row(f)
            self.console.print(t) if found else self.error("Rien de spécifique détecté.")
        except Exception as e: self.error(str(e))

    def module_unshorten(self):
        u = Prompt.ask(f"[{self.theme}]Lien Raccourci / Suspect[/]")
        if not u.startswith("http"): u = "https://" + u
        try:
            r = self.session.head(u, allow_redirects=True, timeout=TIMEOUT)
            t = Table(title="Analyse de Redirection", style=self.theme)
            t.add_column("Étape", style=self.theme); t.add_column("URL", style=self.text_theme)
            for i, hist in enumerate(r.history):
                t.add_row(f"Redirection {i+1}", hist.url)
            t.add_row("Destination Finale", r.url)
            self.console.print(t)
        except Exception as e: self.error(str(e))

    def module_wayback(self):
        u = Prompt.ask(f"[{self.theme}]URL[/]")
        try:
            r = self.session.get(f"https://archive.org/wayback/available?url={quote(u)}").json()
            s = r.get("archived_snapshots", {}).get("closest")
            if s:
                t = Table(title="Wayback Machine", style=self.theme)
                t.add_column("Date", style=self.theme); t.add_column("Lien Archive", style=self.text_theme)
                t.add_row(s["timestamp"], s["url"])
                self.console.print(t)
            else: self.error("Aucune archive trouvée.")
        except Exception as e: self.error(str(e))

    def module_google_dorks(self):
        cible = Prompt.ask(f"[{self.theme}]Nom de domaine ou Cible (ex: tesla.com)[/]")
        t = Table(title=f"Générateur Google Dorks : {cible}", style=self.theme)
        t.add_column("Type de Fichiers ciblé", style=self.theme); t.add_column("Requête Google (à copier)", style="cyan")
        t.add_row("Fichiers PDF / Docs", f"site:{cible} ext:pdf OR ext:doc OR ext:txt")
        t.add_row("Bases de données SQL", f"site:{cible} intext:\"sql dump\" OR ext:sql")
        t.add_row("Mots de passe exposés", f"site:{cible} intext:\"password\" OR intext:\"mot de passe\"")
        t.add_row("Dossiers ouverts / Index", f"site:{cible} intitle:\"index of\"")
        self.console.print(t)

    def module_github_radar(self):
        u = Prompt.ask(f"[{self.theme}]Pseudo GitHub du développeur[/]")
        try:
            r = self.session.get(f"https://api.github.com/users/{u}", timeout=TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                t = Table(title=f"GitHub Developer Radar : {u}", style=self.theme)
                t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
                t.add_row("Nom complet", data.get("name", "N/A"))
                t.add_row("Bio", data.get("bio", "N/A"))
                t.add_row("Entreprise", data.get("company", "N/A"))
                t.add_row("Localisation", data.get("location", "N/A"))
                t.add_row("Dépôts publics", str(data.get("public_repos", 0)))
                t.add_row("Abonnés", str(data.get("followers", 0)))
                t.add_row("Email public", data.get("email", "Non renseigné"))
                t.add_row("Profil URL", data.get("html_url", ""))
                self.console.print(t)
            else:
                self.error("Développeur GitHub introuvable.")
        except Exception as e: self.error(str(e))

    def module_exif_extractor(self):
        path = Prompt.ask(f"[{self.theme}]Chemin de l'image (ex: C:/dossier/photo.jpg)[/]")
        path = path.strip('"\'')
        if not os.path.exists(path): return self.error("Fichier introuvable.")
        try:
            img = Image.open(path)
            exif_data = img._getexif()
            if not exif_data: return self.error("Aucune métadonnée EXIF trouvée.")
            t = Table(title=f"Forensics d'Image (EXIF) : {os.path.basename(path)}", style=self.theme)
            t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag in ["Make", "Model", "DateTimeOriginal", "Software", "GPSInfo"]:
                    if tag == "GPSInfo": t.add_row("Localisation GPS", "[bold green]Coordonnées détectées ![/]")
                    else: t.add_row(str(tag), str(value)[:50])
            self.console.print(t)
        except Exception as e: self.error(str(e))

    def module_wifi_forensics(self):
        if os.name != "nt": return self.error("Module exclusif aux systèmes Windows.")
        self.console.print(f"[{self.dim_theme}]Scan des réseaux Wi-Fi à portée et profils enregistrés...[/]")
        try:
            networks_raw = subprocess.check_output('netsh wlan show networks mode=bssid', shell=True).decode('utf-8', errors="backslashreplace")
            profiles_data = subprocess.check_output('netsh wlan show profiles', shell=True).decode('utf-8', errors="backslashreplace")
            profiles = [i.split(":")[1][1:-1] for i in profiles_data.split('\n') if "Profil Tous les utilisateurs" in i or "All User Profile" in i]
            
            saved_passes = {}
            for p in profiles:
                try:
                    res = subprocess.check_output(f'netsh wlan show profile name="{p}" key=clear', shell=True).decode('utf-8', errors="backslashreplace")
                    pw = [b.split(":")[1][1:-1] for b in res.split('\n') if "Contenu de la cl" in b or "Key Content" in b]
                    saved_passes[p] = pw[0] if pw else "[Ouvert / Sans MDP]"
                except:
                    saved_passes[p] = "[Erreur lecture]"

            ssids_in_range = []
            for line in networks_raw.split('\n'):
                if "SSID" in line and ":" in line and "BSSID" not in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        s_name = parts[1].strip()
                        if s_name and s_name not in ssids_in_range:
                            ssids_in_range.append(s_name)

            t = Table(title="Wi-Fi Recon & Local Forensics (In-Range + Saved Passwords)", style=self.theme)
            t.add_column("Réseau (SSID)", style=self.theme)
            t.add_column("Statut à portée", justify="center")
            t.add_column("Mot de Passe (Clair si enregistré)", style="bold red")

            all_ssids = sorted(list(set(list(saved_passes.keys()) + ssids_in_range)))
            for ssid in all_ssids:
                in_range = "[bold green]À portée (En ligne)[/]" if ssid in ssids_in_range else "[dim]Hors de portée[/]"
                password = saved_passes.get(ssid, "[Jamais connecté sur ce PC]")
                t.add_row(ssid, in_range, password)

            self.console.print(t)
        except Exception as e:
            self.error(f"Erreur système Wi-Fi : {str(e)}")

    # ================= 4. GÉNÉRATEURS & CRYPTO =================
    def module_password_gen(self):
        length = IntPrompt.ask(f"[{self.theme}]Longueur du mot de passe (défaut 16)[/]", default=16)
        length = max(4, min(length, 128))
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+?"
        while True:
            p = "".join(secrets.choice(alphabet) for _ in range(length))
            if (any(c.islower() for c in p) and any(c.isupper() for c in p) and any(c.isdigit() for c in p)): break
        self.success(f"Mot de passe généré : [bold white]{p}[/]")

    def module_email_gen(self):
        size = random.randint(8, 12)
        letters, string_pool = string.ascii_lowercase, string.ascii_lowercase + string.digits
        local = secrets.choice(letters) + "".join(secrets.choice(string_pool) for _ in range(size - 1))
        domain = random.choice(EMAIL_PROVIDERS)
        self.success(f"Email fictif : [bold white]{local}@{domain}[/]")

    def module_pseudo_gen(self):
        adj = ["Dark", "Silent", "Crimson", "Shadow", "Toxic", "Frozen", "Cyber", "Ghost", "Neon"]
        noun = ["Wolf", "Demon", "Tiger", "Phantom", "Raven", "Viper", "Hunter", "Ninja", "Reaper"]
        a, b, num = random.choice(adj), random.choice(noun), random.randint(0, 999)
        self.success(f"Pseudo généré : [bold white]{a}{b}{num}[/]")

    def module_pin_gen(self):
        length = IntPrompt.ask(f"[{self.theme}]Nombre de chiffres (défaut 4)[/]", default=4)
        pin = "".join(secrets.choice(string.digits) for _ in range(length))
        self.success(f"Code PIN généré : [bold white]{pin}[/]")

    def module_fake_identity(self):
        fn = ["Lucas", "Emma", "Hugo", "Léa", "Noah", "Chloé"]
        ln = ["Martin", "Bernard", "Dubois", "Petit", "Durand"]
        t = Table(title="Identité Fictive (Red Dead Money)", style=self.theme)
        t.add_column("Champ", style=self.theme); t.add_column("Donnée", style=self.text_theme)
        f, l = random.choice(fn), random.choice(ln)
        t.add_row("Nom", f"{f} {l}")
        t.add_row("Email", f"{f.lower()}.{l.lower()}{random.randint(10,99)}@{random.choice(EMAIL_PROVIDERS)}")
        t.add_row("Téléphone", "06 " + " ".join(f"{random.randint(0, 99):02}" for _ in range(4)))
        self.console.print(t)

    def module_crypto_tools(self):
        txt = Prompt.ask(f"[{self.theme}]Texte cible[/]")
        t = Table(title="Cryptographie & Encodage", style=self.theme)
        t.add_column("Algorithme", style=self.theme); t.add_column("Résultat", style=self.text_theme)
        t.add_row("MD5", hashlib.md5(txt.encode()).hexdigest())
        t.add_row("SHA-256", hashlib.sha256(txt.encode()).hexdigest())
        t.add_row("Base64 (Enc)", base64.b64encode(txt.encode()).decode())
        try: t.add_row("Base64 (Dec)", base64.b64decode(txt).decode())
        except: pass
        self.console.print(t)

    def module_jwt_decode(self):
        jwt = Prompt.ask(f"[{self.theme}]Token JWT[/]")
        try:
            t = Table(title="Décodeur JWT", style=self.theme)
            t.add_column("Partie", style=self.theme); t.add_column("Données JSON", style=self.text_theme)
            for name, part in zip(("Header", "Payload"), jwt.split(".")[:2]):
                data = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
                t.add_row(name, json.dumps(data, indent=2))
            self.console.print(t)
        except: self.error("Token JWT invalide.")

    def module_crypto_wallet(self):
        wallet = Prompt.ask(f"[{self.theme}]Adresse portefeuille Bitcoin (BTC)[/]")
        self.console.print(f"[{self.dim_theme}]Interrogation de la blockchain...[/]")
        try:
            r = self.session.get(f"https://blockchain.info/rawaddr/{wallet}", timeout=TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                t = Table(title=f"Crypto Wallet Tracker : {wallet[:8]}...", style=self.theme)
                t.add_column("Propriété", style=self.theme); t.add_column("Valeur", style=self.text_theme)
                t.add_row("Nombre de Transactions", str(data.get("n_tx", 0)))
                t.add_row("Total Reçu (BTC)", str(data.get("total_received", 0) / 100000000))
                t.add_row("Solde Actuel (BTC)", f"[bold green]{data.get('final_balance', 0) / 100000000}[/]")
                self.console.print(t)
            else: self.error("Adresse invalide ou introuvable.")
        except Exception as e: self.error(str(e))

    # ================= PARAMÈTRES & MENUS =================
    def settings_menu(self):
        colors = ["bold red", "bold green", "bold blue", "bold cyan", "bold magenta", "bold yellow"]
        while True:
            self.banner()
            t = Table(title=self.tr("settings_title"), show_header=True, header_style=self.theme)
            t.add_column("N°"); t.add_column("Option")
            t.add_row("1", "Changer le Thème (Couleurs)")
            t.add_row("2", f"Changer la Langue (Actuelle : {self.lang.upper()})")
            t.add_row("0", self.tr("back"))
            self.console.print(t)
            
            choix = Prompt.ask(f"\n[{self.theme}]{self.tr('choice')}[/]")
            if choix == "0": break
            elif choix == "1":
                while True:
                    self.banner()
                    tc = Table(title="Choix du Thème", show_header=True, header_style=self.theme)
                    tc.add_column("N°"); tc.add_column("Couleur")
                    for i, c in enumerate(colors, 1): tc.add_row(str(i), f"[{c}]■ {c.replace('bold ', '').capitalize()}[/]")
                    tc.add_row("0", self.tr("back"))
                    self.console.print(tc)
                    c_choix = Prompt.ask(f"\n[{self.theme}]{self.tr('choice')}[/]")
                    if c_choix == "0": break
                    if c_choix.isdigit() and 1 <= int(c_choix) <= len(colors):
                        self.theme = colors[int(c_choix)-1]
                        self.save_config(); self.success(self.tr("theme_updated")); time.sleep(1)
                        break
            elif choix == "2":
                self.lang = "en" if self.lang == "fr" else "fr"
                self.save_config()
                self.success(self.tr("lang_updated"))
                time.sleep(1)

    def execute_menu(self, title, options):
        while True:
            self.banner()
            t = Table(title=title, show_header=True, header_style=self.theme, border_style=self.dim_theme)
            t.add_column("N°", justify="center"); t.add_column("Outil")
            for i, (name, _) in enumerate(options, 1): t.add_row(str(i), name)
            t.add_row("0", self.tr("back"))
            self.console.print(t)
            
            c = Prompt.ask(f"\n[{self.theme}]{self.tr('choice')}[/]")
            if c == "0": break
            if c.isdigit() and 1 <= int(c) <= len(options):
                print("\n"); options[int(c)-1][1]()
                Prompt.ask(f"\n[{self.dim_theme}]{self.tr('press_enter')}[/]")

    def run(self):
        self.auth_screen()
        while True:
            self.banner()
            menus = [
                ("1", self.tr("menu_osint"), [
                    ("IP Intelligence", self.module_ip_info),
                    ("Minecraft Server OSINT", self.module_minecraft_osint),
                    ("Scanner de Ports", self.module_port_scanner),
                    ("Recherche de Sous-domaines", self.module_subdomains),
                    ("Phone OSINT", self.module_phone_osint),
                    ("MAC Address / Vendor Lookup", self.module_mac_lookup)
                ]),
                ("2", self.tr("menu_social"), [
                    ("Username Tracker Asynchrone", self.module_username_tracker),
                    ("Discord Snowflake", self.module_discord_snowflake),
                    ("Discord Invite Recon", self.module_discord_invite),
                    ("Roblox Player Tracker", self.module_roblox_tracker),
                    ("Minecraft Name History", self.module_minecraft_names),
                    ("Steam OSINT & VAC Checker", self.module_steam_checker),
                    ("GTA Online & RP Tracker", self.module_gta_tracker),
                    ("Analyseur de Webhook Discord", self.module_webhook_analyzer),
                    ("Email Breach Checker (Dark Web)", self.module_breach_checker)
                ]),
                ("3", self.tr("menu_web"), [
                    ("Détection de Technologies", self.module_tech_detect),
                    ("Unshortener (Analyse de Redirections)", self.module_unshorten),
                    ("Wayback Machine", self.module_wayback),
                    ("Générateur de Google Dorks", self.module_google_dorks),
                    ("GitHub Developer Radar", self.module_github_radar),
                    ("Extracteur EXIF (Photo Forensics)", self.module_exif_extractor),
                    ("Wi-Fi Recon & Passwords", self.module_wifi_forensics)
                ]),
                ("4", self.tr("menu_crypto"), [
                    ("Générateur de Mot de Passe", self.module_password_gen),
                    ("Générateur d'Email Fictif", self.module_email_gen),
                    ("Générateur de Pseudo", self.module_pseudo_gen),
                    ("Générateur de Code PIN", self.module_pin_gen),
                    ("Identité Fictive (Red Dead Money)", self.module_fake_identity),
                    ("Hash & Base64 Tools", self.module_crypto_tools),
                    ("Décodeur JWT", self.module_jwt_decode),
                    ("Tracker de Portefeuille Bitcoin", self.module_crypto_wallet)
                ])
            ]
            
            t = Table(show_header=True, header_style=self.theme, border_style=self.dim_theme)
            t.add_column("N°", justify="center"); t.add_column("Catégorie")
            for num, name, _ in menus: t.add_row(num, name)
            t.add_row("S", self.tr("settings"))
            t.add_row("0", self.tr("quit"))
            self.console.print(t)
            
            c = Prompt.ask(f"\n[{self.theme}]{self.tr('choice')}[/]").upper()
            if c == "0": break
            elif c == "S": self.settings_menu()
            else:
                for num, name, options in menus:
                    if c == num: self.execute_menu(name, options)

if __name__ == "__main__":
    try:
        app = EclipseOSINT()
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)