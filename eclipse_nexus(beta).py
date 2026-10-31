import os, sys, json, socket, threading, time, string, secrets
import requests
import customtkinter as ctk
from datetime import datetime, timezone
from urllib.parse import quote

# Configuration des couleurs de l'interface (Inspiration Cyberpunk / Cyan)
CTK_BG = "#0B131C"        # Fond principal (très sombre)
CTK_PANEL = "#111C26"     # Fond des panneaux/cartes
CTK_ACCENT = "#00D2FF"    # Cyan néon
CTK_HOVER = "#0099CC"     # Cyan foncé pour les boutons
CTK_TEXT = "#E0E0E0"      # Texte clair

# Initialisation de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class EclipseNexus(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ECLIPSE NEXUS // CYBER SUITE")
        self.geometry("1100x700")
        self.configure(fg_color=CTK_BG)
        self.session = requests.Session()
        self.local_ip = self.get_local_ip()
        self.public_ip = "Recherche..."
        self.start_time = time.time()

        # --- LAYOUT PRINCIPAL ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. MENU LATÉRAL (Gauche)
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=CTK_PANEL, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="ECLIPSE\nNEXUS", font=ctk.CTkFont(size=24, weight="bold"), text_color=CTK_ACCENT)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.subtitle = ctk.CTkLabel(self.sidebar, text="VERSION GUI // 1.0", font=ctk.CTkFont(size=10), text_color="grey")
        self.subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Boutons du menu
        self.btn_dash = self.create_nav_button("Dashboard", 2, self.show_dashboard)
        self.btn_osint = self.create_nav_button("OSINT & Réseau", 3, self.show_osint)
        self.btn_crypto = self.create_nav_button("Générateurs", 4, self.show_generators)
        self.btn_mail = self.create_nav_button("Boîte Mail Jetable", 5, self.show_mail)

        # 2. ZONE PRINCIPALE (Droite)
        self.main_container = ctk.CTkFrame(self, fg_color=CTK_BG, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Création des différentes vues (Frames)
        self.frames = {}
        
        # --- VUE DASHBOARD ---
        self.frames["Dashboard"] = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.setup_dashboard()

        # --- VUE OSINT ---
        self.frames["OSINT"] = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.setup_osint()

        # --- VUE GÉNÉRATEURS ---
        self.frames["Generators"] = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.setup_generators()

        # --- VUE MAIL ---
        self.frames["Mail"] = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.setup_mail()

        # 3. BARRE DE STATUT (En bas)
        self.statusbar = ctk.CTkFrame(self, height=30, fg_color=CTK_PANEL, corner_radius=0)
        self.statusbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_label = ctk.CTkLabel(self.statusbar, text="PANEL ACTIF  |  MOTEUR : RED DEAD MONEY  |  SESSION : 00:00:00", font=ctk.CTkFont(size=11), text_color=CTK_ACCENT)
        self.status_label.pack(pady=5)

        # Lancement
        self.show_dashboard()
        threading.Thread(target=self.fetch_public_ip, daemon=True).start()
        self.update_clock()

    # ================== UTILITAIRES GUI ==================
    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=CTK_TEXT, 
                            hover_color=CTK_PANEL, border_width=1, border_color=CTK_PANEL,
                            anchor="w", command=command)
        btn.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        return btn

    def show_frame(self, frame_name):
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[frame_name].grid(row=0, column=0, sticky="nsew")

    def show_dashboard(self): self.show_frame("Dashboard")
    def show_osint(self): self.show_frame("OSINT")
    def show_generators(self): self.show_frame("Generators")
    def show_mail(self): self.show_frame("Mail")

    # ================== CONSTRUCTION DES VUES ==================

    def setup_dashboard(self):
        frame = self.frames["Dashboard"]
        frame.grid_columnconfigure((0,1,2,3), weight=1)

        # En-tête
        header = ctk.CTkLabel(frame, text="> Dashboard_", font=ctk.CTkFont(size=28, weight="bold"))
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 20))
        
        self.clock_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=14), text_color=CTK_ACCENT)
        self.clock_label.grid(row=0, column=2, columnspan=2, sticky="e", pady=(10, 20))

        # Les 4 panneaux d'information
        self.ip_panel = self.create_info_panel(frame, "MON IPv4", "Chargement...", 1, 0)
        self.create_info_panel(frame, "IP LOCALE", self.local_ip, 1, 1)
        self.create_info_panel(frame, "PROXY / VPN", "Désactivé", 1, 2)
        self.create_info_panel(frame, "MODULES ACTIFS", "4 Prêts", 1, 3)

        # Centre visuel (Animation / Radar)
        radar_frame = ctk.CTkFrame(frame, fg_color=CTK_PANEL, border_color=CTK_ACCENT, border_width=1)
        radar_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=20, ipady=100)
        
        radar_lbl = ctk.CTkLabel(radar_frame, text="CYBER DEFENSE // MONITORING RÉSEAU", text_color=CTK_ACCENT)
        radar_lbl.pack(pady=10)
        
        # Un canevas pour dessiner un truc cyberpunk
        self.canvas = ctk.CTkCanvas(radar_frame, width=200, height=200, bg=CTK_PANEL, highlightthickness=0)
        self.canvas.pack(expand=True)
        self.draw_radar()

        # Boutons d'action rapide en bas
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=4, pady=10)
        ctk.CTkButton(btn_frame, text="SCAN RÉSEAU", fg_color=CTK_ACCENT, text_color="black", hover_color=CTK_HOVER, command=self.show_osint).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="CYBER LAB", fg_color=CTK_ACCENT, text_color="black", hover_color=CTK_HOVER, command=self.show_generators).pack(side="left", padx=10)

    def create_info_panel(self, parent, title, value, row, col):
        p = ctk.CTkFrame(parent, fg_color=CTK_PANEL, border_width=1, border_color="#2A3B4C")
        p.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(p, text=title, font=ctk.CTkFont(size=11), text_color="grey").pack(pady=(10, 0))
        val_lbl = ctk.CTkLabel(p, text=value, font=ctk.CTkFont(size=16, weight="bold"))
        val_lbl.pack(pady=(5, 10))
        return val_lbl

    def setup_osint(self):
        frame = self.frames["OSINT"]
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(frame, text="> Console OSINT & Réseau", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", pady=(10, 20))

        # Barre de recherche
        search_frame = ctk.CTkFrame(frame, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", pady=10)
        
        self.osint_type = ctk.CTkOptionMenu(search_frame, values=["IP Intelligence", "Port Scanner", "Username Tracker", "Roblox Tracker"], fg_color=CTK_PANEL, button_color=CTK_ACCENT)
        self.osint_type.pack(side="left", padx=(0, 10))

        self.osint_entry = ctk.CTkEntry(search_frame, placeholder_text="Entrez l'IP, le pseudo ou le domaine...", width=400)
        self.osint_entry.pack(side="left", padx=10)

        ctk.CTkButton(search_frame, text="LANCER L'ANALYSE", fg_color=CTK_ACCENT, text_color="black", command=self.run_osint).pack(side="left", padx=10)

        # Console de sortie
        self.osint_console = ctk.CTkTextbox(frame, fg_color=CTK_PANEL, text_color=CTK_ACCENT, font=ctk.CTkFont(family="Courier", size=13))
        self.osint_console.grid(row=2, column=0, sticky="nsew", pady=10)
        self.osint_console.insert("end", "[*] Moteur Eclipse OSINT prêt. En attente d'une cible...\n")

    def setup_generators(self):
        frame = self.frames["Generators"]
        ctk.CTkLabel(frame, text="> Cyber Lab & Générateurs", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(10, 20))

        # Mot de passe
        p_frame = ctk.CTkFrame(frame, fg_color=CTK_PANEL)
        p_frame.pack(fill="x", pady=10, ipady=10)
        ctk.CTkLabel(p_frame, text="Générateur de Mots de Passe Ultra-Sécurisés").pack()
        self.pw_len = ctk.CTkSlider(p_frame, from_=8, to=64, number_of_steps=56)
        self.pw_len.set(16)
        self.pw_len.pack(pady=10)
        ctk.CTkButton(p_frame, text="GÉNÉRER", fg_color=CTK_ACCENT, text_color="black", command=self.run_pw_gen).pack()
        self.pw_output = ctk.CTkEntry(p_frame, width=300, justify="center")
        self.pw_output.pack(pady=10)

    def setup_mail(self):
        frame = self.frames["Mail"]
        ctk.CTkLabel(frame, text="> Boîte Mail Jetable (Mail.tm)", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(10, 20))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="GÉNÉRER ADRESSE", fg_color=CTK_ACCENT, text_color="black", command=self.run_temp_mail).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="RECHARGER BOÎTE", border_color=CTK_ACCENT, border_width=1, fg_color="transparent", command=self.refresh_temp_mail).pack(side="left", padx=10)

        self.mail_address_lbl = ctk.CTkLabel(frame, text="Aucune adresse active", font=ctk.CTkFont(size=18, weight="bold"), text_color=CTK_ACCENT)
        self.mail_address_lbl.pack(pady=10)

        self.mail_console = ctk.CTkTextbox(frame, fg_color=CTK_PANEL, text_color="white", width=800, height=400)
        self.mail_console.pack(pady=10)

    # ================== LOGIQUE DES MODULES ==================

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
            self.ip_panel.configure(text=self.public_ip)
        except: self.ip_panel.configure(text="Erreur réseau")

    def update_clock(self):
        now = datetime.now(timezone.utc).strftime("%d %b %Y  •  %H:%M:%S UTC")
        self.clock_label.configure(text=now)
        
        # Calcul du temps de session
        elapsed = int(time.time() - self.start_time)
        hrs, rem = divmod(elapsed, 3600)
        mins, secs = divmod(rem, 60)
        self.status_label.configure(text=f"PANEL ACTIF  |  IP : {self.local_ip}  |  SESSION : {hrs:02}:{mins:02}:{secs:02}")
        
        self.after(1000, self.update_clock)

    def draw_radar(self):
        # Un simple cercle radar décoratif dessiné sur le Canvas Tkinter
        self.canvas.delete("all")
        w, h = 200, 200
        self.canvas.create_oval(10, 10, w-10, h-10, outline=CTK_ACCENT, width=1)
        self.canvas.create_oval(40, 40, w-40, h-40, outline=CTK_ACCENT, width=1, dash=(2, 4))
        self.canvas.create_oval(70, 70, w-70, h-70, outline=CTK_ACCENT, width=1)
        self.canvas.create_line(w/2, 10, w/2, h-10, fill=CTK_ACCENT, dash=(2,2))
        self.canvas.create_line(10, h/2, w-10, h/2, fill=CTK_ACCENT, dash=(2,2))
        # Dans un vrai projet, on ferait tourner une ligne ici avec un `self.after`

    def print_osint(self, text):
        self.osint_console.insert("end", text + "\n")
        self.osint_console.see("end")

    def run_osint(self):
        target = self.osint_entry.get().strip()
        tool = self.osint_type.get()
        if not target:
            self.print_osint("[!] Erreur : Veuillez entrer une cible valide.")
            return

        self.print_osint(f"\n[{datetime.now().strftime('%H:%M:%S')}] Lancement de {tool} sur : {target}")
        self.print_osint("-" * 60)
        
        # Lancement dans un thread pour ne pas geler l'interface graphique
        threading.Thread(target=self._osint_thread, args=(tool, target), daemon=True).start()

    def _osint_thread(self, tool, target):
        if tool == "IP Intelligence":
            try:
                r = self.session.get(f"https://ipwho.is/{target}", timeout=5).json()
                if not r.get("success"): self.print_osint("[-] Cible invalide ou introuvable.")
                else:
                    self.print_osint(f"IP       : {r.get('ip')} ({r.get('type')})")
                    self.print_osint(f"Pays     : {r.get('country')} ({r.get('country_code')})")
                    self.print_osint(f"Ville    : {r.get('city')}, {r.get('region')}")
                    self.print_osint(f"FAI/Org  : {r.get('connection', {}).get('isp')}")
            except Exception as e: self.print_osint(f"[!] Erreur API : {e}")
            
        elif tool == "Port Scanner":
            ports = [21, 22, 80, 443, 3306, 25565]
            self.print_osint("Scan des ports fréquents en cours...")
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                if sock.connect_ex((target, port)) == 0:
                    self.print_osint(f"[+] Port {port} : OUVERT")
                sock.close()
            self.print_osint("Scan terminé.")
            
        elif tool == "Roblox Tracker":
            try:
                r = self.session.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [target], "excludeBannedUsers": False}).json()
                if not r.get("data"): self.print_osint("[-] Joueur introuvable.")
                else:
                    pid = r["data"][0]["id"]
                    infos = self.session.get(f"https://users.roblox.com/v1/users/{pid}").json()
                    self.print_osint(f"ID Joueur   : {pid}")
                    self.print_osint(f"Pseudo      : {infos.get('displayName')}")
                    self.print_osint(f"Date Créa   : {infos.get('created', '').split('T')[0]}")
                    self.print_osint(f"Banni       : {'Oui' if infos.get('isBanned') else 'Non'}")
            except: self.print_osint("[!] Erreur de recherche Roblox.")
            
        else:
            self.print_osint("[!] Module en cours d'intégration dans la version GUI.")

    def run_pw_gen(self):
        length = int(self.pw_len.get())
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        self.pw_output.delete(0, 'end')
        self.pw_output.insert(0, pw)

    def run_temp_mail(self):
        self.mail_console.delete("1.0", "end")
        self.mail_console.insert("end", "[*] Connexion à l'API Mail.tm...\n")
        threading.Thread(target=self._mail_gen_thread, daemon=True).start()

    def _mail_gen_thread(self):
        try:
            dom_req = self.session.get("https://api.mail.tm/domains", timeout=5)
            if dom_req.status_code == 200:
                domain = dom_req.json()['hydra:member'][0]['domain']
                username = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
                password = secrets.token_hex(8)
                email = f"{username}@{domain}"
                
                create_req = self.session.post("https://api.mail.tm/accounts", json={"address": email, "password": password}, timeout=5)
                if create_req.status_code in [200, 201]:
                    token_req = self.session.post("https://api.mail.tm/token", json={"address": email, "password": password}, timeout=5)
                    if token_req.status_code == 200:
                        self.temp_mail = email
                        self.mail_token = token_req.json().get('token')
                        self.mail_address_lbl.configure(text=self.temp_mail)
                        self.mail_console.insert("end", f"[+] Adresse générée avec succès : {self.temp_mail}\n")
                        return
            self.mail_console.insert("end", "[!] Erreur lors de la génération.\n")
        except Exception as e:
            self.mail_console.insert("end", f"[!] Erreur réseau : {e}\n")

    def refresh_temp_mail(self):
        if not self.temp_mail or not hasattr(self, 'mail_token'):
            self.mail_console.insert("end", "[!] Générez d'abord une adresse.\n")
            return
        threading.Thread(target=self._mail_refresh_thread, daemon=True).start()

    def _mail_refresh_thread(self):
        self.mail_console.insert("end", "[*] Vérification de la boîte de réception...\n")
        try:
            headers = {"Authorization": f"Bearer {self.mail_token}"}
            msgs_req = self.session.get("https://api.mail.tm/messages", headers=headers, timeout=5)
            if msgs_req.status_code == 200:
                messages = msgs_req.json().get('hydra:member', [])
                if not messages:
                    self.mail_console.insert("end", "[-] Aucun nouveau message.\n")
                else:
                    for msg in messages:
                        self.mail_console.insert("end", f"\n--- MESSAGE REÇU ---\n")
                        self.mail_console.insert("end", f"De    : {msg['from']['address']}\n")
                        self.mail_console.insert("end", f"Sujet : {msg['subject']}\n")
                        # Récupérer le contenu du message nécessiterait une autre requête sur /messages/id
            else:
                self.mail_console.insert("end", "[!] Erreur API lors du rafraîchissement.\n")
        except Exception as e:
            self.mail_console.insert("end", f"[!] Erreur de connexion : {e}\n")

if __name__ == "__main__":
    app = EclipseNexus()
    app.mainloop()