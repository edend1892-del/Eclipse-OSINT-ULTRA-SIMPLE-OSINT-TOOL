#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSE OSINT - Powered by Red Dead Money Core
"""

import os, sys, json, time, socket, base64, hashlib, secrets, string, random, re
from datetime import datetime, timezone
import hmac
from urllib.parse import quote, urlparse
from concurrent.futures import ThreadPoolExecutor

# --- SYSTÈME D'AUTO-INSTALLATION (Utile uniquement pour la version .py) ---
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
except ImportError:
    print("[!] Dépendances manquantes détectées.")
    print("[*] Installation automatique en cours, patiente quelques secondes...")
    os.system(f"{sys.executable} -m pip install requests rich phonenumbers pillow")
    print("[+] Installation terminée avec succès ! Relance le script.")
    sys.exit(0)
# -------------------------------------------------------------------------

USERS_FILE = os.path.join(os.path.expanduser("~"), ".eclipse_users.json")
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".eclipse_config.json")
TIMEOUT = 5
EMAIL_PROVIDERS = ["gmail.com", "outlook.com", "yahoo.fr", "proton.me", "icloud.com"]

class EclipseOSINT:
    def __init__(self):
        self.console = Console()
        self.load_config()
        self.text_theme = "bold white"
        self.dim_theme = "bold grey50"
        self.current_user = None
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Eclipse/RDM-Core"})

    def load_config(self):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                self.theme = json.load(f).get("theme", "bold cyan")
        except:
            self.theme = "bold cyan"

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"theme": self.theme}, f)
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
        status = f"Agent actif: {self.current_user}" if self.current_user else "Accès restreint"
        self.console.print(Panel(f"[{self.text_theme}]v2.5[/] | [{self.theme}]Moteur: Red Dead Money[/] | [{self.dim_theme}]{status}[/]", style=self.theme, expand=False), justify="center")
        print("\n")

    def error(self, msg): self.console.print(f"[{self.theme}][!][/] {msg}")
    def success(self, msg): self.console.print(f"[bold green][+][/] {msg}")

    # ================= SYSTÈME DE COMPTES =================
    def hash_pw(self, password, salt=None):
        salt = salt or secrets.token_bytes(16)
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
        return salt.hex(), h.hex()

    def auth_screen(self):
        while not self.current_user:
            self.banner()
            t = Table(show_header=False, box=None)
            t.add_row(f"[{self.theme}][1][/]", "Se connecter")
            t.add_row(f"[{self.theme}][2][/]", "Créer un compte")
            t.add_row(f"[{self.theme}][0][/]", "Quitter")
            self.console.print(t)
            
            c = Prompt.ask(f"\n[{self.theme}]Choix[/]")
            if c == "0": sys.exit(0)
            
            try:
                with open(USERS_FILE, encoding="utf-8") as f: users = json.load(f)
            except: users = {}

            if c == "1":
                name = Prompt.ask("Identifiant")
                pw = Prompt.ask("Mot de passe")
                u = users.get(name)
                if u:
                    _, h = self.hash_pw(pw, bytes.fromhex(u["salt"]))
                    if hmac.compare_digest(h, u["hash"]):
                        self.current_user = name
                        self.success(f"Connexion établie, {name} !"); time.sleep(1)
                        return
                self.error("Accès refusé."); time.sleep(1.5)
            elif c == "2":
                name = Prompt.ask("Nouvel Identifiant")
                pw = Prompt.ask("Nouveau Mot de passe")
                if len(pw) < 6 or name in users:
                    self.error("Erreur (déjà pris ou mdp trop court)."); time.sleep(1.5); continue
                salt, h = self.hash_pw(pw)
                users[name] = {"salt": salt, "hash": h, "created": datetime.now().strftime("%d/%m/%Y")}
                try:
                    with open(USERS_FILE, "w", encoding="utf-8") as f: json.dump(users, f)
                    self.success("Compte agent créé !"); time.sleep(1.5)
                except: self.error("Erreur de sauvegarde."); time.sleep(1.5)

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

    # ================= 4. GÉNÉRATEURS & CRYPTO =================
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

    # ================= PARAMÈTRES & MENUS =================
    def settings_menu(self):
        colors = ["bold red", "bold green", "bold blue", "bold cyan", "bold magenta", "bold yellow"]
        while True:
            self.banner()
            t = Table(title="Paramètres de l'Interface", show_header=True, header_style=self.theme)
            t.add_column("N°"); t.add_column("Couleur")
            for i, c in enumerate(colors, 1): t.add_row(str(i), f"[{c}]■ {c.replace('bold ', '').capitalize()}[/]")
            t.add_row("0", "Retour")
            self.console.print(t)
            
            choix = Prompt.ask(f"\n[{self.theme}]Choix[/]")
            if choix == "0": break
            if choix.isdigit() and 1 <= int(choix) <= len(colors):
                self.theme = colors[int(choix)-1]
                self.save_config(); self.success("Thème mis à jour !")

    def execute_menu(self, title, options):
        while True:
            self.banner()
            t = Table(title=title, show_header=True, header_style=self.theme, border_style=self.dim_theme)
            t.add_column("N°", justify="center"); t.add_column("Outil")
            for i, (name, _) in enumerate(options, 1): t.add_row(str(i), name)
            t.add_row("0", "Retour")
            self.console.print(t)
            
            c = Prompt.ask(f"\n[{self.theme}]Choix[/]")
            if c == "0": break
            if c.isdigit() and 1 <= int(c) <= len(options):
                print("\n"); options[int(c)-1][1]()
                Prompt.ask(f"\n[{self.dim_theme}]Appuie sur Entrée pour continuer...[/]")

    def run(self):
        self.auth_screen()
        while True:
            self.banner()
            menus = [
                ("1", "🌐 OSINT & Réseau", [
                    ("IP Intelligence", self.module_ip_info),
                    ("Scanner de Ports", self.module_port_scanner),
                    ("Recherche de Sous-domaines", self.module_subdomains),
                    ("Phone OSINT", self.module_phone_osint)
                ]),
                ("2", "👾 Social, Gaming & Fuites", [
                    ("Username Tracker Asynchrone", self.module_username_tracker),
                    ("Discord Snowflake", self.module_discord_snowflake),
                    ("Roblox Player Tracker", self.module_roblox_tracker),
                    ("Email Breach Checker (Dark Web)", self.module_breach_checker)
                ]),
                ("3", "🛠️ Web & Forensics", [
                    ("Détection de Technologies", self.module_tech_detect),
                    ("Unshortener (Analyse de Redirections)", self.module_unshorten),
                    ("Wayback Machine", self.module_wayback)
                ]),
                ("4", "🎲 Générateurs & Crypto", [
                    ("Identité Fictive (Red Dead Money)", self.module_fake_identity),
                    ("Hash & Base64 Tools", self.module_crypto_tools),
                    ("Décodeur JWT", self.module_jwt_decode)
                ])
            ]
            
            t = Table(show_header=True, header_style=self.theme, border_style=self.dim_theme)
            t.add_column("N°", justify="center"); t.add_column("Catégorie")
            for num, name, _ in menus: t.add_row(num, name)
            t.add_row("S", "Paramètres (Couleurs)")
            t.add_row("0", "Quitter")
            self.console.print(t)
            
            c = Prompt.ask(f"\n[{self.theme}]Choix[/]").upper()
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