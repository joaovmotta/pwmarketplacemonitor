import requests
from bs4 import BeautifulSoup
import threading
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://marketplace.theclassic.games/pw126"
BASE_DETAIL = "https://marketplace.theclassic.games/details/pw126/"

CLASSES = {
    "Todos": None,
    "Guerreiro": "Guerreiro",
    "Mago": "Mago",
    "Barbaro": "Barbaro",
    "Feiticeira": "Feiticeira",
    "Arqueiro": "Arqueiro",
    "Sacerdote": "Sacerdote"
}

CONFIG_FILE = "monitor_config.json"


class EmailConfig:
    def __init__(self):
        self.email_remetente = ""
        self.senha_app = ""
        self.email_destinatario = ""
        self.notificar_novos = False
        self.notificar_hercules = False
        self.notificar_classe = "Todos"
        self.preco_min = ""
        self.preco_max = ""
        self.carregar()

    def carregar(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                self.email_remetente = data.get("email_remetente", "")
                self.senha_app = data.get("senha_app", "")
                self.email_destinatario = data.get("email_destinatario", "")
                self.notificar_novos = data.get("notificar_novos", False)
                self.notificar_hercules = data.get("notificar_hercules", False)
                self.notificar_classe = data.get("notificar_classe", "Todos")
                self.preco_min = data.get("preco_min", "")
                self.preco_max = data.get("preco_max", "")
            except:
                pass

    def salvar(self):
        data = {
            "email_remetente": self.email_remetente,
            "senha_app": self.senha_app,
            "email_destinatario": self.email_destinatario,
            "notificar_novos": self.notificar_novos,
            "notificar_hercules": self.notificar_hercules,
            "notificar_classe": self.notificar_classe,
            "preco_min": self.preco_min,
            "preco_max": self.preco_max
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def enviar_email(self, assunto, corpo_html):
        if not self.email_remetente or not self.senha_app or not self.email_destinatario:
            print("Email nao configurado!")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = assunto
            msg["From"] = self.email_remetente
            msg["To"] = self.email_destinatario

            parte_html = MIMEText(corpo_html, "html")
            msg.attach(parte_html)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.email_remetente, self.senha_app)
                server.sendmail(self.email_remetente, self.email_destinatario, msg.as_string())

            print(f"Email enviado: {assunto}")
            return True
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
            return False


class JanelaConfigEmail(tk.Toplevel):
    def __init__(self, parent, email_config):
        super().__init__(parent)
        self.email_config = email_config
        self.title("Configurar Notificacoes por Email")
        self.geometry("500x480")
        self.configure(bg="#1a1a2e")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.criar_widgets()

    def criar_widgets(self):
        tk.Label(self, text="Configuracao de Email (Gmail)",
                 font=("Arial", 14, "bold"), fg="#e94560", bg="#1a1a2e").pack(pady=(15, 5))

        tk.Label(self, text="Use uma Senha de App do Google (nao a senha normal)",
                 font=("Arial", 9), fg="#888", bg="#1a1a2e").pack(pady=(0, 10))

        campos = tk.Frame(self, bg="#1a1a2e")
        campos.pack(fill="x", padx=30, pady=5)

        tk.Label(campos, text="Email Gmail (remetente):", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_remetente = tk.Entry(campos, width=35, font=("Arial", 10))
        self.entry_remetente.insert(0, self.email_config.email_remetente)
        self.entry_remetente.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(campos, text="Senha de App:", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_senha = tk.Entry(campos, width=35, font=("Arial", 10), show="*")
        self.entry_senha.insert(0, self.email_config.senha_app)
        self.entry_senha.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(campos, text="Email destinatario:", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_destinatario = tk.Entry(campos, width=35, font=("Arial", 10))
        self.entry_destinatario.insert(0, self.email_config.email_destinatario)
        self.entry_destinatario.grid(row=2, column=1, padx=10, pady=5)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=30, pady=15)

        tk.Label(self, text="Quando notificar?",
                 font=("Arial", 12, "bold"), fg="#ffcc00", bg="#1a1a2e").pack(pady=(0, 5))

        filtros = tk.Frame(self, bg="#1a1a2e")
        filtros.pack(fill="x", padx=30)

        self.var_novos = tk.BooleanVar(value=self.email_config.notificar_novos)
        tk.Checkbutton(filtros, text="Notificar qualquer personagem novo",
                       variable=self.var_novos, fg="white", bg="#1a1a2e",
                       selectcolor="#1a1a2e", activebackground="#1a1a2e",
                       font=("Arial", 10)).pack(anchor="w", pady=3)

        self.var_hercules = tk.BooleanVar(value=self.email_config.notificar_hercules)
        tk.Checkbutton(filtros, text="Notificar somente se tiver Hercules",
                       variable=self.var_hercules, fg="#00ff88", bg="#1a1a2e",
                       selectcolor="#1a1a2e", activebackground="#1a1a2e",
                       font=("Arial", 10, "bold")).pack(anchor="w", pady=3)

        classe_frame = tk.Frame(filtros, bg="#1a1a2e")
        classe_frame.pack(anchor="w", pady=5)

        tk.Label(classe_frame, text="Filtrar por classe:", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).pack(side="left")
        self.combo_classe = ttk.Combobox(classe_frame, values=list(CLASSES.keys()),
                                          state="readonly", width=12)
        self.combo_classe.set(self.email_config.notificar_classe)
        self.combo_classe.pack(side="left", padx=10)

        preco_frame = tk.Frame(filtros, bg="#1a1a2e")
        preco_frame.pack(anchor="w", pady=5)

        tk.Label(preco_frame, text="Preco min (TCC):", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).pack(side="left")
        self.entry_preco_min = tk.Entry(preco_frame, width=8, font=("Arial", 10))
        self.entry_preco_min.insert(0, self.email_config.preco_min)
        self.entry_preco_min.pack(side="left", padx=(5, 15))

        tk.Label(preco_frame, text="Preco max (TCC):", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).pack(side="left")
        self.entry_preco_max = tk.Entry(preco_frame, width=8, font=("Arial", 10))
        self.entry_preco_max.insert(0, self.email_config.preco_max)
        self.entry_preco_max.pack(side="left", padx=5)

        btn_frame = tk.Frame(self, bg="#1a1a2e")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Testar Email", command=self.testar_email,
                  bg="#0f3460", fg="white", font=("Arial", 10, "bold"),
                  padx=15, pady=5, cursor="hand2").pack(side="left", padx=10)

        tk.Button(btn_frame, text="Salvar", command=self.salvar,
                  bg="#1b998b", fg="white", font=("Arial", 10, "bold"),
                  padx=25, pady=5, cursor="hand2").pack(side="left", padx=10)

        tk.Button(btn_frame, text="Cancelar", command=self.destroy,
                  bg="#666", fg="white", font=("Arial", 10, "bold"),
                  padx=15, pady=5, cursor="hand2").pack(side="left", padx=10)

    def testar_email(self):
        self.email_config.email_remetente = self.entry_remetente.get().strip()
        self.email_config.senha_app = self.entry_senha.get().strip()
        self.email_config.email_destinatario = self.entry_destinatario.get().strip()

        if not self.email_config.email_remetente or not self.email_config.senha_app:
            messagebox.showwarning("Aviso", "Preencha email e senha de app!")
            return

        corpo = """
        <html>
        <body style="font-family: Arial; background: #1a1a2e; color: white; padding: 20px;">
            <h2 style="color: #e94560;">Teste de Notificacao</h2>
            <p>Se voce recebeu este email, as notificacoes estao funcionando!</p>
            <p style="color: #00ff88;">Marketplace Monitor - The Classic PW 1.2.6</p>
        </body>
        </html>
        """

        sucesso = self.email_config.enviar_email(
            "[PW Monitor] Teste de Notificacao", corpo
        )

        if sucesso:
            messagebox.showinfo("Sucesso", "Email de teste enviado com sucesso!")
        else:
            messagebox.showerror("Erro", "Falha ao enviar email.\nVerifique email e senha de app.")

    def salvar(self):
        self.email_config.email_remetente = self.entry_remetente.get().strip()
        self.email_config.senha_app = self.entry_senha.get().strip()
        self.email_config.email_destinatario = self.entry_destinatario.get().strip()
        self.email_config.notificar_novos = self.var_novos.get()
        self.email_config.notificar_hercules = self.var_hercules.get()
        self.email_config.notificar_classe = self.combo_classe.get()
        self.email_config.preco_min = self.entry_preco_min.get().strip()
        self.email_config.preco_max = self.entry_preco_max.get().strip()

        self.email_config.salvar()
        messagebox.showinfo("Salvo", "Configuracoes salvas com sucesso!")
        self.destroy()


class MarketplaceMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("The Classic PW 1.2.6 - Marketplace Monitor")
        self.root.geometry("1200x850")
        self.root.configure(bg="#1a1a2e")

        self.personagens = {}
        self.novos_monitor = {}
        self.monitorando = False
        self.verificando_hercules = False
        self.parar_hercules = False
        self.timer = None
        self.ordem_reversa = {}
        self.email_config = EmailConfig()

        self.criar_interface()

    def criar_interface(self):
        header = tk.Frame(self.root, bg="#16213e", pady=10)
        header.pack(fill="x")

        tk.Label(header, text="The Classic PW 1.2.6 - Marketplace Monitor",
                 font=("Arial", 16, "bold"), fg="#e94560", bg="#16213e").pack()

        filtros = tk.Frame(self.root, bg="#1a1a2e", pady=10)
        filtros.pack(fill="x", padx=15)

        tk.Label(filtros, text="Classe:", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).grid(row=0, column=0, padx=5)
        self.filtro_classe = ttk.Combobox(filtros, values=list(CLASSES.keys()),
                                          state="readonly", width=12)
        self.filtro_classe.set("Todos")
        self.filtro_classe.grid(row=0, column=1, padx=5)

        tk.Label(filtros, text="Level min:", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).grid(row=0, column=2, padx=5)
        self.filtro_level_min = tk.Entry(filtros, width=6)
        self.filtro_level_min.grid(row=0, column=3, padx=5)

        tk.Label(filtros, text="Level max:", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).grid(row=0, column=4, padx=5)
        self.filtro_level_max = tk.Entry(filtros, width=6)
        self.filtro_level_max.grid(row=0, column=5, padx=5)

        tk.Label(filtros, text="Preco min:", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).grid(row=0, column=6, padx=5)
        self.filtro_preco_min = tk.Entry(filtros, width=8)
        self.filtro_preco_min.grid(row=0, column=7, padx=5)

        tk.Label(filtros, text="Preco max:", fg="white", bg="#1a1a2e",
                 font=("Arial", 10)).grid(row=0, column=8, padx=5)
        self.filtro_preco_max = tk.Entry(filtros, width=8)
        self.filtro_preco_max.grid(row=0, column=9, padx=5)

        self.check_hercules = tk.BooleanVar()
        tk.Checkbutton(filtros, text="So com Hercules", variable=self.check_hercules,
                       fg="#e94560", bg="#1a1a2e", selectcolor="#1a1a2e",
                       activebackground="#1a1a2e", activeforeground="#e94560",
                       font=("Arial", 10, "bold")).grid(row=0, column=10, padx=10)

        botoes = tk.Frame(self.root, bg="#1a1a2e", pady=5)
        botoes.pack(fill="x", padx=15)

        self.btn_buscar = tk.Button(botoes, text="Buscar", command=self.iniciar_busca,
                                     bg="#0f3460", fg="white", font=("Arial", 10, "bold"),
                                     padx=15, pady=5, cursor="hand2")
        self.btn_buscar.pack(side="left", padx=5)

        self.btn_filtrar = tk.Button(botoes, text="Aplicar Filtros", command=self.aplicar_filtros,
                                      bg="#533483", fg="white", font=("Arial", 10, "bold"),
                                      padx=15, pady=5, cursor="hand2")
        self.btn_filtrar.pack(side="left", padx=5)

        self.btn_monitor = tk.Button(botoes, text="Iniciar Monitor (3min)",
                                      command=self.toggle_monitor,
                                      bg="#1b998b", fg="white", font=("Arial", 10, "bold"),
                                      padx=15, pady=5, cursor="hand2")
        self.btn_monitor.pack(side="left", padx=5)

        self.btn_hercules = tk.Button(botoes, text="Verificar Hercules/Pets",
                                       command=self.iniciar_verificacao_hercules,
                                       bg="#e94560", fg="white", font=("Arial", 10, "bold"),
                                       padx=15, pady=5, cursor="hand2")
        self.btn_hercules.pack(side="left", padx=5)

        self.btn_parar_hercules = tk.Button(botoes, text="Parar Verificacao",
                                             command=self.parar_verificacao_hercules,
                                             bg="#ff6600", fg="white", font=("Arial", 10, "bold"),
                                             padx=15, pady=5, cursor="hand2",
                                             state="disabled")
        self.btn_parar_hercules.pack(side="left", padx=5)

        self.btn_email = tk.Button(botoes, text="Config Email",
                                    command=self.abrir_config_email,
                                    bg="#ff9900", fg="white", font=("Arial", 10, "bold"),
                                    padx=15, pady=5, cursor="hand2")
        self.btn_email.pack(side="left", padx=5)

        self.label_notif = tk.Label(botoes, text="", fg="#00ff88",
                                     bg="#1a1a2e", font=("Arial", 9))
        self.label_notif.pack(side="left", padx=5)
        self.atualizar_label_notif()

        self.label_status = tk.Label(botoes, text="Aguardando...", fg="#aaa",
                                      bg="#1a1a2e", font=("Arial", 9))
        self.label_status.pack(side="right", padx=10)

        tk.Label(self.root, text="Todos os Personagens", fg="#aaa", bg="#1a1a2e",
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=15)

        tabela_frame = tk.Frame(self.root, bg="#1a1a2e")
        tabela_frame.pack(fill="both", expand=True, padx=15, pady=(0, 5))

        colunas = ("nome", "classe", "level", "preco", "cultivo", "fama", "hercules", "pets", "url")
        self.tree = ttk.Treeview(tabela_frame, columns=colunas, show="headings", height=12)

        self.tree.heading("nome", text="Nome")
        self.tree.heading("classe", text="Classe")
        self.tree.heading("level", text="Level")
        self.tree.heading("preco", text="Preco (TCC)")
        self.tree.heading("cultivo", text="Cultivo")
        self.tree.heading("fama", text="Fama")
        self.tree.heading("hercules", text="Hercules")
        self.tree.heading("pets", text="Pets/Montarias")
        self.tree.heading("url", text="Link")

        self.tree.column("nome", width=110)
        self.tree.column("classe", width=80)
        self.tree.column("level", width=50, anchor="center")
        self.tree.column("preco", width=80, anchor="center")
        self.tree.column("cultivo", width=100)
        self.tree.column("fama", width=60, anchor="center")
        self.tree.column("hercules", width=70, anchor="center")
        self.tree.column("pets", width=250)
        self.tree.column("url", width=300)

        scrollbar = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.copiar_link)

        novos_header = tk.Frame(self.root, bg="#1a1a2e")
        novos_header.pack(fill="x", padx=15, pady=(5, 0))

        tk.Label(novos_header, text="Novos (Monitor)", fg="#ffcc00", bg="#1a1a2e",
                 font=("Arial", 10, "bold")).pack(side="left")

        self.label_novos_count = tk.Label(novos_header, text="(0)", fg="#ffcc00",
                                           bg="#1a1a2e", font=("Arial", 10))
        self.label_novos_count.pack(side="left", padx=5)

        self.label_novos_status = tk.Label(novos_header, text="", fg="#888",
                                            bg="#1a1a2e", font=("Arial", 9))
        self.label_novos_status.pack(side="left", padx=15)

        self.btn_limpar_novos = tk.Button(novos_header, text="Limpar Novos",
                                           command=self.limpar_novos,
                                           bg="#444", fg="white", font=("Arial", 9),
                                           padx=10, pady=2, cursor="hand2")
        self.btn_limpar_novos.pack(side="right")

        novos_frame = tk.Frame(self.root, bg="#1a1a2e")
        novos_frame.pack(fill="both", expand=True, padx=15, pady=(0, 5))

        colunas_novos = ("hora", "nome", "classe", "level", "preco", "cultivo", "fama", "hercules", "pets", "url")
        self.tree_novos = ttk.Treeview(novos_frame, columns=colunas_novos, show="headings", height=6)

        self.tree_novos.heading("hora", text="Detectado")
        self.tree_novos.heading("nome", text="Nome")
        self.tree_novos.heading("classe", text="Classe")
        self.tree_novos.heading("level", text="Level")
        self.tree_novos.heading("preco", text="Preco (TCC)")
        self.tree_novos.heading("cultivo", text="Cultivo")
        self.tree_novos.heading("fama", text="Fama")
        self.tree_novos.heading("hercules", text="Hercules")
        self.tree_novos.heading("pets", text="Pets/Montarias")
        self.tree_novos.heading("url", text="Link")

        self.tree_novos.column("hora", width=65, anchor="center")
        self.tree_novos.column("nome", width=100)
        self.tree_novos.column("classe", width=75)
        self.tree_novos.column("level", width=45, anchor="center")
        self.tree_novos.column("preco", width=75, anchor="center")
        self.tree_novos.column("cultivo", width=95)
        self.tree_novos.column("fama", width=55, anchor="center")
        self.tree_novos.column("hercules", width=65, anchor="center")
        self.tree_novos.column("pets", width=230)
        self.tree_novos.column("url", width=280)

        scrollbar_novos = ttk.Scrollbar(novos_frame, orient="vertical", command=self.tree_novos.yview)
        self.tree_novos.configure(yscrollcommand=scrollbar_novos.set)

        self.tree_novos.pack(side="left", fill="both", expand=True)
        scrollbar_novos.pack(side="right", fill="y")

        self.tree_novos.tag_configure("hercules_novo", foreground="#00ff88")
        self.tree_novos.tag_configure("novo_normal", foreground="#ffcc00")

        self.tree_novos.bind("<Double-1>", self.copiar_link_novos)

        for col in colunas:
            self.tree.heading(col, text=self.tree.heading(col)["text"],
                              command=lambda c=col: self.ordenar_tabela(self.tree, c))
        for col in colunas_novos:
            self.tree_novos.heading(col, text=self.tree_novos.heading(col)["text"],
                                    command=lambda c=col: self.ordenar_tabela(self.tree_novos, c))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                         background="#16213e",
                         foreground="white",
                         fieldbackground="#16213e",
                         font=("Arial", 10),
                         rowheight=28)
        style.configure("Treeview.Heading",
                         background="#0f3460",
                         foreground="white",
                         font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#533483")])

        self.tree.tag_configure("hercules", foreground="#00ff88")

        rodape = tk.Frame(self.root, bg="#16213e", pady=5)
        rodape.pack(fill="x")

        self.label_total = tk.Label(rodape, text="Total: 0 personagens",
                                     fg="#aaa", bg="#16213e", font=("Arial", 9))
        self.label_total.pack(side="left", padx=15)

        tk.Label(rodape, text="Clique no cabecalho da coluna para ordenar | Duplo clique na linha para copiar o link",
                 fg="#666", bg="#16213e", font=("Arial", 9)).pack(side="right", padx=15)

    def set_status(self, texto):
        self.label_status.config(text=texto)
        self.root.update_idletasks()

    def atualizar_label_notif(self):
        cfg = self.email_config
        if cfg.notificar_novos or cfg.notificar_hercules:
            filtro = cfg.notificar_classe if cfg.notificar_classe != "Todos" else "todas classes"
            tipo = "Hercules" if cfg.notificar_hercules else "novos"
            self.label_notif.config(
                text=f"[Email ON: {tipo} - {filtro}]",
                fg="#00ff88"
            )
        else:
            self.label_notif.config(text="[Email OFF]", fg="#666")

    def abrir_config_email(self):
        JanelaConfigEmail(self.root, self.email_config)
        self.root.wait_window(self.root.winfo_children()[-1] if self.root.winfo_children() else None)
        self.atualizar_label_notif()

    def notificar_por_email(self, personagens_novos):
        cfg = self.email_config
        if not cfg.notificar_novos and not cfg.notificar_hercules:
            return

        para_notificar = []
        classe_filtro = CLASSES.get(cfg.notificar_classe)

        for cid, info in personagens_novos.items():
            if classe_filtro and info.get("classe") != classe_filtro:
                continue

            try:
                preco = int(info.get("preco", 0))
                if cfg.preco_min and preco < int(cfg.preco_min):
                    continue
                if cfg.preco_max and preco > int(cfg.preco_max):
                    continue
            except (ValueError, TypeError):
                pass

            if cfg.notificar_hercules and "SIM" not in info.get("hercules", ""):
                continue

            if not cfg.notificar_novos and not cfg.notificar_hercules:
                continue

            para_notificar.append(info)

        if not para_notificar:
            return

        tem_hercules = any("SIM" in p.get("hercules", "") for p in para_notificar)

        if tem_hercules:
            assunto = f"[PW Monitor] HERCULES ENCONTRADO! {len(para_notificar)} personagem(ns) novo(s)"
        else:
            assunto = f"[PW Monitor] {len(para_notificar)} personagem(ns) novo(s) encontrado(s)"

        linhas = ""
        for p in para_notificar:
            cor_herc = "#00ff88" if "SIM" in p.get("hercules", "") else "#ff4444"
            url_completa = f"https://marketplace.theclassic.games{p['url']}" if p['url'].startswith('/') else p['url']
            linhas += f"""
            <tr style="border-bottom: 1px solid #333;">
                <td style="padding: 8px; color: white;">{p['nome']}</td>
                <td style="padding: 8px; color: white;">{p['classe']}</td>
                <td style="padding: 8px; color: white; text-align: center;">{p['level']}</td>
                <td style="padding: 8px; color: white; text-align: center;">{p['preco']}</td>
                <td style="padding: 8px; color: white;">{p['cultivo']}</td>
                <td style="padding: 8px; color: white; text-align: center;">{p['fama']}</td>
                <td style="padding: 8px; color: {cor_herc}; font-weight: bold; text-align: center;">{p.get('hercules', '---')}</td>
                <td style="padding: 8px; color: #aaa;">{p.get('pets', '---')}</td>
                <td style="padding: 8px;"><a href="{url_completa}" style="color: #4da6ff;">Ver conta</a></td>
            </tr>
            """

        corpo = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #1a1a2e; color: white; padding: 20px;">
            <h2 style="color: #e94560;">Marketplace Monitor - The Classic PW 1.2.6</h2>
            <p style="color: #aaa;">Detectado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>

            {"<h3 style='color: #00ff88;'>HERCULES ENCONTRADO!</h3>" if tem_hercules else ""}

            <p>{len(para_notificar)} personagem(ns) novo(s) encontrado(s):</p>

            <table style="border-collapse: collapse; width: 100%; background: #16213e; border-radius: 8px;">
                <tr style="background: #0f3460;">
                    <th style="padding: 10px; color: white; text-align: left;">Nome</th>
                    <th style="padding: 10px; color: white; text-align: left;">Classe</th>
                    <th style="padding: 10px; color: white; text-align: center;">Level</th>
                    <th style="padding: 10px; color: white; text-align: center;">Preco</th>
                    <th style="padding: 10px; color: white; text-align: left;">Cultivo</th>
                    <th style="padding: 10px; color: white; text-align: center;">Fama</th>
                    <th style="padding: 10px; color: white; text-align: center;">Hercules</th>
                    <th style="padding: 10px; color: white; text-align: left;">Pets</th>
                    <th style="padding: 10px; color: white; text-align: left;">Link</th>
                </tr>
                {linhas}
            </table>

            <p style="color: #666; margin-top: 20px; font-size: 12px;">
                Enviado automaticamente pelo Marketplace Monitor
            </p>
        </body>
        </html>
        """

        threading.Thread(target=cfg.enviar_email, args=(assunto, corpo), daemon=True).start()

    def ordenar_tabela(self, tree, coluna):
        dados = [(tree.set(item, coluna), item) for item in tree.get_children("")]

        chave = (id(tree), coluna)
        reverso = self.ordem_reversa.get(chave, False)

        try:
            dados.sort(key=lambda x: int(x[0].replace(".", "").replace(",", "")),
                       reverse=reverso)
        except (ValueError, AttributeError):
            dados.sort(key=lambda x: x[0].lower(), reverse=reverso)

        for i, (val, item) in enumerate(dados):
            tree.move(item, "", i)

        self.ordem_reversa[chave] = not reverso

    def buscar_personagens(self):
        response = requests.get(URL)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.find_all("li", class_="character-card")
        resultado = {}

        for card in cards:
            link = card.find("a", class_="link")
            if not link:
                continue

            href = link.get("href", "")
            char_id = href.split("/")[-1]

            nome_tag = card.find("dd", class_="item-name")
            nome = nome_tag.text.strip() if nome_tag else "?"

            classe_tag = card.find("dd", class_="item-type")
            classe = classe_tag.text.strip() if classe_tag else "?"

            level_tag = card.find("dl", class_="level")
            if level_tag:
                dd = level_tag.find("dd")
                level = dd.text.strip() if dd else "?"
            else:
                level = card.get("data-level", "?")

            preco = card.get("data-price", "?")

            cultivo = "?"
            fama = "?"
            scores = card.find_all("div", class_="display-score")
            for score in scores:
                dt = score.find("dt")
                dd = score.find("dd")
                if dt and dd:
                    if "Cultivo" in dt.text:
                        cultivo = dd.text.strip()
                    elif "Fama" in dt.text:
                        fama = dd.text.strip()

            resultado[char_id] = {
                "nome": nome,
                "classe": classe,
                "level": level,
                "preco": preco,
                "cultivo": cultivo,
                "fama": fama,
                "hercules": "---",
                "pets": "---",
                "url": href
            }

        return resultado

    def verificar_detalhes_char(self, char_id):
        driver = None
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--log-level=3")

            import sys
            chromedriver_local = None
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
                possivel = os.path.join(base_path, "chromedriver.exe")
                if os.path.exists(possivel):
                    chromedriver_local = possivel
                    print(f"ChromeDriver encontrado em: {chromedriver_local}")

            try:
                if chromedriver_local:
                    driver = webdriver.Chrome(service=Service(chromedriver_local), options=options)
                else:
                    driver = webdriver.Chrome(options=options)
            except:
                try:
                    driver = webdriver.Chrome(
                        service=Service(ChromeDriverManager().install()),
                        options=options
                    )
                except Exception as e:
                    print(f"Todas tentativas falharam: {e}")
                    return "ERRO", f"ERRO: {str(e)[:80]}"

            driver.get(BASE_DETAIL + char_id)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-pet-name], .badge, .mount-list, .character-skill"))
                )
            except:
                pass

            time.sleep(2)

            pets = driver.find_elements(By.CSS_SELECTOR, "[data-pet-name]")
            nomes_pets = []
            tem_hercules = False

            for pet in pets:
                nome_pet = pet.get_attribute("data-pet-name")
                if nome_pet:
                    nomes_pets.append(nome_pet)
                    if "hercules" in nome_pet.lower() or "hércules" in nome_pet.lower():
                        tem_hercules = True

            driver.quit()

            pets_str = ", ".join(nomes_pets) if nomes_pets else "Nenhum"
            hercules_str = "SIM" if tem_hercules else "NAO"

            return hercules_str, pets_str
        except Exception as e:
            print(f"ERRO Selenium [{char_id}]: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return "ERRO", f"ERRO: {str(e)[:80]}"

    def atualizar_tabela(self, dados=None):
        self.tree.delete(*self.tree.get_children())

        if dados is None:
            dados = self.personagens

        filtrados = self.filtrar_dados(dados)

        for char_id, info in filtrados.items():
            tag = "hercules" if "SIM" in info.get("hercules", "") else ""
            self.tree.insert("", "end", iid=char_id, values=(
                info["nome"], info["classe"], info["level"],
                info["preco"], info["cultivo"], info["fama"],
                info["hercules"], info.get("pets", "---"), info["url"]
            ), tags=(tag,))

        self.label_total.config(text=f"Total: {len(filtrados)} personagens (de {len(self.personagens)})")

    def atualizar_tabela_novos(self):
        self.tree_novos.delete(*self.tree_novos.get_children())

        for char_id, info in self.novos_monitor.items():
            tag = "hercules_novo" if "SIM" in info.get("hercules", "") else "novo_normal"
            self.tree_novos.insert("", 0, values=(
                info.get("hora_detectado", "?"),
                info["nome"], info["classe"], info["level"],
                info["preco"], info["cultivo"], info["fama"],
                info["hercules"], info.get("pets", "---"), info["url"]
            ), tags=(tag,))

        self.label_novos_count.config(text=f"({len(self.novos_monitor)})")

    def limpar_novos(self):
        self.novos_monitor = {}
        self.atualizar_tabela_novos()
        self.label_novos_status.config(text="")
        self.set_status("Lista de novos limpa")

    def filtrar_dados(self, dados):
        filtrados = {}

        classe_sel = CLASSES.get(self.filtro_classe.get())
        level_min = self.filtro_level_min.get()
        level_max = self.filtro_level_max.get()
        preco_min = self.filtro_preco_min.get()
        preco_max = self.filtro_preco_max.get()
        so_hercules = self.check_hercules.get()

        for cid, info in dados.items():
            if classe_sel and info.get("classe") != classe_sel:
                continue

            try:
                lv = int(info["level"])
                if level_min and lv < int(level_min):
                    continue
                if level_max and lv > int(level_max):
                    continue
            except ValueError:
                pass

            try:
                pr = int(info["preco"])
                if preco_min and pr < int(preco_min):
                    continue
                if preco_max and pr > int(preco_max):
                    continue
            except ValueError:
                pass

            if so_hercules and "SIM" not in info.get("hercules", ""):
                continue

            filtrados[cid] = info

        return filtrados

    def iniciar_busca(self):
        self.btn_buscar.config(state="disabled")
        self.set_status("Buscando personagens...")
        threading.Thread(target=self._buscar_thread, daemon=True).start()

    def _buscar_thread(self):
        try:
            self.personagens = self.buscar_personagens()
            agora = datetime.now().strftime("%H:%M:%S")
            self.root.after(0, lambda: self.atualizar_tabela())
            self.root.after(0, lambda: self.set_status(
                f"{len(self.personagens)} personagens encontrados as {agora}"))
        except Exception as e:
            self.root.after(0, lambda: self.set_status(f"Erro: {e}"))
        finally:
            self.root.after(0, lambda: self.btn_buscar.config(state="normal"))

    def iniciar_verificacao_hercules(self):
        filtrados = self.filtrar_dados(self.personagens)
        if not filtrados:
            self.set_status("Nenhum personagem para verificar. Busque primeiro!")
            return

        self.parar_hercules = False
        self.verificando_hercules = True
        self.btn_hercules.config(state="disabled")
        self.btn_parar_hercules.config(state="normal")
        self.set_status(f"Verificando Hercules/Pets em {len(filtrados)} personagens...")
        threading.Thread(target=self._hercules_thread,
                         args=(filtrados,), daemon=True).start()

    def parar_verificacao_hercules(self):
        self.parar_hercules = True
        self.set_status("Parando verificacao...")

    def _hercules_thread(self, filtrados):
        total = len(filtrados)
        verificados = 0

        for i, (char_id, info) in enumerate(filtrados.items(), 1):
            if self.parar_hercules:
                self.root.after(0, lambda v=verificados: self.set_status(
                    f"Verificacao parada! {v}/{total} verificados"))
                break

            self.root.after(0, lambda i=i: self.set_status(
                f"Verificando Hercules/Pets {i}/{total}..."))

            hercules, pets = self.verificar_detalhes_char(char_id)
            self.personagens[char_id]["hercules"] = hercules
            self.personagens[char_id]["pets"] = pets
            verificados = i

            self.root.after(0, lambda: self.atualizar_tabela())

            time.sleep(1)
        else:
            com_herc = sum(1 for v in self.personagens.values() if "SIM" in v.get("hercules", ""))
            self.root.after(0, lambda: self.set_status(
                f"Verificacao completa! {com_herc} com Hercules"))

        self.verificando_hercules = False
        self.parar_hercules = False
        self.root.after(0, lambda: self.btn_hercules.config(state="normal"))
        self.root.after(0, lambda: self.btn_parar_hercules.config(state="disabled"))

    def aplicar_filtros(self):
        self.atualizar_tabela()

    def toggle_monitor(self):
        if self.monitorando:
            self.monitorando = False
            if self.timer:
                self.root.after_cancel(self.timer)
            self.btn_monitor.config(text="Iniciar Monitor (3min)", bg="#1b998b")
            self.set_status("Monitor parado")
        else:
            self.monitorando = True
            self.btn_monitor.config(text="Parar Monitor", bg="#e94560")
            self.set_status("Monitor ativo - verificando a cada 3 min")
            self.agendar_monitor()

    def agendar_monitor(self):
        if self.monitorando:
            self.timer = self.root.after(180000, self.executar_monitor)

    def executar_monitor(self):
        if not self.monitorando:
            return
        threading.Thread(target=self._monitor_thread, daemon=True).start()

    def _monitor_thread(self):
        try:
            novos_dados = self.buscar_personagens()
            novas = {cid: info for cid, info in novos_dados.items()
                     if cid not in self.personagens}

            agora = datetime.now().strftime("%H:%M:%S")

            if novas:
                for char_id, info in novas.items():
                    hercules, pets = self.verificar_detalhes_char(char_id)
                    info["hercules"] = hercules
                    info["pets"] = pets
                    info["hora_detectado"] = agora

                    self.novos_monitor[char_id] = info.copy()

                    time.sleep(1)

                self.notificar_por_email(novas)

                for cid in novos_dados:
                    if cid not in novas and cid in self.personagens:
                        novos_dados[cid]["hercules"] = self.personagens[cid].get("hercules", "---")
                        novos_dados[cid]["pets"] = self.personagens[cid].get("pets", "---")

                self.personagens = novos_dados

                com_herc = [i for i in novas.values() if "SIM" in i.get("hercules", "")]

                self.root.after(0, lambda: self.atualizar_tabela())
                self.root.after(0, lambda: self.atualizar_tabela_novos())
                self.root.after(0, lambda: self.label_novos_status.config(
                    text=f"Ultima verificacao: {agora} - {len(novas)} novo(s) encontrado(s)!",
                    fg="#00ff88"))
                self.root.after(0, lambda: self.set_status(
                    f"NOVO! {len(novas)} nova(s) as {agora}! "
                    f"{str(len(com_herc)) + ' com Hercules!' if com_herc else ''}"))
            else:
                for cid in novos_dados:
                    if cid in self.personagens:
                        novos_dados[cid]["hercules"] = self.personagens[cid].get("hercules", "---")
                        novos_dados[cid]["pets"] = self.personagens[cid].get("pets", "---")

                self.personagens = novos_dados
                self.root.after(0, lambda: self.atualizar_tabela())
                self.root.after(0, lambda: self.label_novos_status.config(
                    text=f"Nenhum novo personagem encontrado as {agora}",
                    fg="#888"))
                self.root.after(0, lambda: self.set_status(
                    f"Sem novos as {agora}. Total: {len(novos_dados)}"))
        except Exception as e:
            self.root.after(0, lambda: self.set_status(f"Erro monitor: {e}"))

        self.root.after(0, self.agendar_monitor)

    def copiar_link(self, event):
        item = self.tree.selection()
        if item:
            valores = self.tree.item(item[0], "values")
            url = valores[-1]
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.set_status(f"Link copiado: {url}")

    def copiar_link_novos(self, event):
        item = self.tree_novos.selection()
        if item:
            valores = self.tree_novos.item(item[0], "values")
            url = valores[-1]
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.set_status(f"Link copiado: {url}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MarketplaceMonitor(root)
    root.mainloop()