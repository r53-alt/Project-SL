import minecraft_launcher_lib
import subprocess
import os
import sys
import json
import threading
import shutil
import time
import random
import string
import requests
import base64
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk, ImageDraw

class ModernDarkLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Project SL Launcher")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.root.configure(bg='#0a0a0f')

        # Улучшенная цветовая схема - темная и приятная
        self.colors = {
            'bg': '#0c0c14',
            'bg_secondary': '#111118',
            'bg_tertiary': '#1a1a24',
            'bg_card': '#15151e',
            'accent': '#8b5cf6',
            'accent2': '#a78bfa',
            'accent3': '#7c3aed',
            'success': '#10b981',
            'error': '#f43f5e',
            'warning': '#f59e0b',
            'info': '#3b82f6',
            'text': '#f8fafc',
            'text_secondary': '#a1a1aa',
            'text_muted': '#71717a',
            'border': '#272735',
            'border_hover': '#3f3f55',
            'gradient_start': '#8b5cf6',
            'gradient_end': '#6366f1',
        }

        # Фиксированное имя папки
        self.game_folder_name = "2b30qkcx"

        # Папка лаунчера
        self.launcher_dir = Path(__file__).parent.absolute()

        # Папка с игрой (фиксированное имя)
        self.minecraft_dir = self.launcher_dir / self.game_folder_name
        self.minecraft_dir.mkdir(exist_ok=True)

        # Создаем подпапки
        self.versions_dir = self.minecraft_dir / "versions"
        self.assets_dir = self.minecraft_dir / "assets"
        self.libraries_dir = self.minecraft_dir / "libraries"
        self.skins_dir = self.launcher_dir / "skins"
        self.skins_dir.mkdir(exist_ok=True)

        for d in [self.versions_dir, self.assets_dir, self.libraries_dir]:
            d.mkdir(exist_ok=True)

        # Конфиг
        self.config_file = self.launcher_dir / "system.cfg"
        self.load_config()

        # Переменные
        self.selected_version = tk.StringVar()
        self.username = tk.StringVar(value=self.config.get("username", "Player"))
        self.ram = tk.StringVar(value=str(self.config.get("ram", "4096")))
        self.java_path = tk.StringVar(value=self.config.get("java_path", "java"))
        self.game_width = tk.StringVar(value=str(self.config.get("width", "1280")))
        self.game_height = tk.StringVar(value=str(self.config.get("height", "720")))
        self.fullscreen = tk.BooleanVar(value=self.config.get("fullscreen", False))
        self.show_fps = tk.BooleanVar(value=self.config.get("show_fps", False))
        self.install_status = tk.StringVar(value="Ready")
        self.download_progress = tk.DoubleVar(value=0)
        self.current_skin = tk.StringVar(value=self.config.get("skin", ""))
        self.skin_preview = None
        self.skin_image = None
        self.avatar_image = None

        # Данные
        self.available_versions = []
        self.installed_versions = []
        self.profiles = {}
        self.is_installing = False
        self.current_page = "home"

        # Создаем интерфейс
        self.setup_styles()
        self.setup_ui()

        # Загружаем данные
        self.load_profiles()
        self.refresh_installed_versions()
        self.load_versions_background()
        self.load_skin_preview()
        self.load_skin_avatar()

        self.update_console("=== PROJECT SL LAUNCHER v2.0 ===\n")
        self.update_console("Welcome!\n")
        self.update_console(f"Game folder: {self.game_folder_name}\n")
        self.update_console("Ready!\n\n")

    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('default')

        style.configure("Modern.Horizontal.TProgressbar",
                        troughcolor=self.colors['bg_tertiary'],
                        background=self.colors['accent'],
                        bordercolor=self.colors['bg_tertiary'],
                        lightcolor=self.colors['accent2'],
                        darkcolor=self.colors['accent3'],
                        thickness=8)

        style.configure("Modern.TCombobox",
                        fieldbackground=self.colors['bg_tertiary'],
                        background=self.colors['bg_tertiary'],
                        foreground=self.colors['text'],
                        arrowcolor=self.colors['accent'])

    def setup_ui(self):
        """Create UI"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar (navigation)
        self.sidebar = tk.Frame(self.main_frame, bg=self.colors['bg_secondary'], width=260)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Logo in sidebar
        logo_container = tk.Frame(self.sidebar, bg=self.colors['bg_secondary'], height=120)
        logo_container.pack(fill=tk.X, pady=(25, 15))
        logo_container.pack_propagate(False)

        # Градиентный круг для иконки
        logo_circle = tk.Canvas(logo_container, width=50, height=50, 
                               bg=self.colors['bg_secondary'], highlightthickness=0)
        logo_circle.pack(pady=(10, 5))
        logo_circle.create_oval(2, 2, 48, 48, fill=self.colors['accent'], outline="")
        logo_circle.create_text(25, 25, text="SL", font=('Segoe UI', 18, 'bold'), 
                               fill='white')

        logo_text = tk.Label(logo_container, text="PROJECT SL", font=('Segoe UI', 15, 'bold'),
                           bg=self.colors['bg_secondary'], fg=self.colors['text'])
        logo_text.pack()

        logo_sub = tk.Label(logo_container, text="MINECRAFT LAUNCHER", font=('Segoe UI', 8, 'bold'),
                          bg=self.colors['bg_secondary'], fg=self.colors['text_muted'])
        logo_sub.pack()

        # Divider
        tk.Frame(self.sidebar, bg=self.colors['border'], height=1).pack(fill=tk.X, padx=20, pady=10)

        # Navigation buttons
        nav_buttons = [
            ("  Home", self.show_home, "home"),
            ("  Launch", self.show_launch, "launch"),
            ("  Install", self.show_install, "install"),
            ("  Skins", self.show_skins, "skins"),
            ("  Profiles", self.show_profiles, "profiles"),
            ("  Settings", self.show_settings, "settings")
        ]

        self.nav_buttons = {}
        self.nav_indicators = {}
        for text, command, page in nav_buttons:
            btn_frame = tk.Frame(self.sidebar, bg=self.colors['bg_secondary'])
            btn_frame.pack(fill=tk.X, padx=15, pady=2)

            # Индикатор активной страницы
            indicator = tk.Frame(btn_frame, bg=self.colors['bg_secondary'], width=4)
            indicator.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
            self.nav_indicators[page] = indicator

            btn = tk.Button(btn_frame, text=text, command=lambda c=command, p=page: self.navigate(c, p),
                          bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                          font=('Segoe UI', 11), bd=0, cursor='hand2', anchor=tk.W,
                          padx=5, pady=12, activebackground=self.colors['bg_secondary'],
                          activeforeground=self.colors['accent2'])
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.nav_buttons[page] = btn

            btn.bind("<Enter>", lambda e, b=btn, ind=indicator: (
                b.config(bg=self.colors['bg_tertiary'], fg=self.colors['text']),
                ind.config(bg=self.colors['accent']) if self.current_page != page.split()[0] else None
            ))
            btn.bind("<Leave>", lambda e, b=btn, p=page, ind=indicator: b.config(
                bg=self.colors['bg_secondary'], 
                fg=self.colors['accent'] if self.current_page == p else self.colors['text_secondary']
            ) or ind.config(bg=self.colors['accent'] if self.current_page == p else self.colors['bg_secondary']))

        # Info at bottom of sidebar
        tk.Frame(self.sidebar, bg=self.colors['border'], height=1).pack(fill=tk.X, padx=20, pady=10)

        info_frame = tk.Frame(self.sidebar, bg=self.colors['bg_secondary'])
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(info_frame, text=f"Folder: {self.game_folder_name}", 
                font=('Segoe UI', 8), bg=self.colors['bg_secondary'], 
                fg=self.colors['text_muted']).pack(anchor=tk.W)

        self.version_count_label = tk.Label(info_frame, text="Versions: 0", 
                                           font=('Segoe UI', 8), bg=self.colors['bg_secondary'],
                                           fg=self.colors['text_muted'])
        self.version_count_label.pack(anchor=tk.W)

        # Main content area
        self.content_area = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Header
        self.header = tk.Frame(self.content_area, bg=self.colors['bg'], height=70)
        self.header.pack(fill=tk.X, padx=35, pady=(25, 0))
        self.header.pack_propagate(False)

        self.page_title = tk.Label(self.header, text="Home", font=('Segoe UI', 26, 'bold'),
                                  bg=self.colors['bg'], fg=self.colors['text'])
        self.page_title.pack(side=tk.LEFT)

        # Decorative accent line under title
        self.title_accent = tk.Frame(self.header, bg=self.colors['accent'], height=3, width=40)
        self.title_accent.place(x=35, y=55)

        # User area
        user_frame = tk.Frame(self.header, bg=self.colors['bg'])
        user_frame.pack(side=tk.RIGHT)

        # Skin avatar
        self.avatar_label = tk.Label(user_frame, bg=self.colors['bg_tertiary'], width=40, height=40)
        self.avatar_label.pack(side=tk.RIGHT)

        self.username_label = tk.Label(user_frame, textvariable=self.username,
                                      font=('Segoe UI', 12, 'bold'), bg=self.colors['bg'],
                                      fg=self.colors['text'])
        self.username_label.pack(side=tk.RIGHT, padx=10)

        # Divider
        tk.Frame(self.content_area, bg=self.colors['border'], height=1).pack(fill=tk.X, padx=30, pady=15)

        # Page container
        self.page_container = tk.Frame(self.content_area, bg=self.colors['bg'])
        self.page_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))

        # Status bar
        self.status_bar = tk.Frame(self.content_area, bg=self.colors['bg_secondary'], height=50)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)

        # Top border
        tk.Frame(self.status_bar, bg=self.colors['border'], height=1).pack(fill=tk.X)

        self.status_icon = tk.Label(self.status_bar, text="●", font=('Segoe UI', 10),
                                   bg=self.colors['bg_secondary'], fg=self.colors['success'])
        self.status_icon.pack(side=tk.LEFT, padx=(25, 10), pady=(2, 0))

        self.status_label = tk.Label(self.status_bar, textvariable=self.install_status,
                                    bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                                    font=('Segoe UI', 10))
        self.status_label.pack(side=tk.LEFT, pady=(2, 0))

        self.progress_bar = ttk.Progressbar(self.status_bar, variable=self.download_progress,
                                           mode='determinate', style="Modern.Horizontal.TProgressbar",
                                           length=350)
        self.progress_bar.pack(side=tk.RIGHT, padx=25, pady=(2, 0))

        # Show home page
        self.show_home()
        self.update_nav_highlight()

    def navigate(self, command, page):
        """Navigate between pages"""
        self.current_page = page
        self.update_nav_highlight()
        command()
        # Update title accent
        if hasattr(self, 'title_accent'):
            self.title_accent.config(bg=self.colors['accent'])

    def update_nav_highlight(self):
        """Update navigation highlight"""
        for page, btn in self.nav_buttons.items():
            indicator = self.nav_indicators.get(page)
            if page == self.current_page:
                btn.config(fg=self.colors['accent'], bg=self.colors['bg_tertiary'])
                if indicator:
                    indicator.config(bg=self.colors['accent'])
            else:
                btn.config(fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'])
                if indicator:
                    indicator.config(bg=self.colors['bg_secondary'])

    def clear_container(self):
        """Clear container"""
        for widget in self.page_container.winfo_children():
            widget.destroy()

    def create_card(self, parent, title=None, padding=20):
        """Create card with modern styling"""
        card = tk.Frame(parent, bg=self.colors['bg_card'], bd=0, highlightbackground=self.colors['border'],
                       highlightthickness=1)
        if title:
            header = tk.Frame(card, bg=self.colors['bg_card'])
            header.pack(fill=tk.X, padx=padding, pady=(padding, 0))
            tk.Label(header, text=title, font=('Segoe UI', 14, 'bold'),
                    bg=self.colors['bg_card'], fg=self.colors['text']).pack(anchor=tk.W)
            tk.Frame(card, bg=self.colors['border'], height=1).pack(fill=tk.X, padx=padding, pady=(10, 10))
        return card

    def create_button(self, parent, text, command, bg=None, fg='#ffffff', 
                     font=('Segoe UI', 11, 'bold'), padx=20, pady=10, 
                     hover_bg=None, width=None, borderless=False):
        """Create styled button with modern effects"""
        bg = bg or self.colors['accent']
        hover_bg = hover_bg or self.colors['accent2']

        btn = tk.Button(parent, text=text, command=command,
                       bg=bg, fg=fg, font=font, bd=0, cursor='hand2',
                       padx=padx, pady=pady, activebackground=hover_bg,
                       activeforeground=fg, width=width,
                       relief=tk.FLAT)

        # Hover glow effect
        def on_enter(e, b=btn, h=hover_bg, original_bg=bg):
            b.config(bg=h)
            if not borderless and bg == self.colors['accent']:
                b.config(highlightbackground=self.colors['accent2'], highlightthickness=1)

        def on_leave(e, b=btn, c=bg):
            b.config(bg=c, highlightthickness=0)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def create_entry(self, parent, textvariable, label=None, width=None, show=None):
        """Create entry field with focus effects"""
        if label:
            tk.Label(parent, text=label, font=('Segoe UI', 10),
                    bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack(anchor=tk.W, pady=(10, 5))

        entry_frame = tk.Frame(parent, bg=self.colors['border'], padx=1, pady=1)
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        entry = tk.Entry(entry_frame, textvariable=textvariable, bg=self.colors['bg_tertiary'],
                        fg=self.colors['text'], bd=0, font=('Segoe UI', 11),
                        insertbackground=self.colors['accent'], width=width, show=show,
                        relief=tk.FLAT, highlightthickness=0)
        entry.pack(fill=tk.X, padx=8, pady=6)

        # Focus effects
        def on_focus_in(e, ef=entry_frame):
            ef.config(bg=self.colors['accent'])
        def on_focus_out(e, ef=entry_frame):
            ef.config(bg=self.colors['border'])

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

        return entry

    def show_home(self):
        """Home screen with modern design"""
        self.clear_container()
        self.page_title.config(text="Home")
        if hasattr(self, 'title_accent'):
            self.title_accent.config(bg=self.colors['accent'])

        content = tk.Frame(self.page_container, bg=self.colors['bg'])
        content.pack(fill=tk.BOTH, expand=True)

        # Welcome section with gradient feel
        welcome_frame = tk.Frame(content, bg=self.colors['bg_card'], padx=45, pady=35)
        welcome_frame.pack(fill=tk.X, pady=(0, 25))

        # Accent bar at top
        tk.Frame(welcome_frame, bg=self.colors['accent'], height=3).pack(fill=tk.X, pady=(0, 15))

        greeting = self.get_greeting()
        tk.Label(welcome_frame, text=f"{greeting}, {self.username.get()}!", 
                font=('Segoe UI', 24, 'bold'), bg=self.colors['bg_card'], 
                fg=self.colors['text']).pack(anchor=tk.W)

        tk.Label(welcome_frame, text="Welcome to Project SL Launcher — Your Minecraft experience", 
                font=('Segoe UI', 12), bg=self.colors['bg_card'], 
                fg=self.colors['text_secondary']).pack(anchor=tk.W, pady=(8, 0))

        # Stats row
        stats_frame = tk.Frame(content, bg=self.colors['bg'])
        stats_frame.pack(fill=tk.X, pady=(0, 25))

        stats = [
            ("📦", str(len(self.installed_versions)), "Installed", self.colors['accent']),
            ("⚡", self.ram.get() + " MB", "RAM", self.colors['success']),
            ("👤", self.username.get(), "Player", self.colors['warning']),
            ("🎨", "Yes" if self.current_skin.get() else "No", "Skin", self.colors['info'])
        ]

        for icon, value, label, color in stats:
            card = self.create_card(stats_frame)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

            # Top colored bar
            tk.Frame(card, bg=color, height=4).pack(fill=tk.X)

            inner = tk.Frame(card, bg=self.colors['bg_card'])
            inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

            tk.Label(inner, text=icon, font=('Segoe UI', 26), bg=self.colors['bg_card'], 
                    fg=color).pack(pady=(5, 5))
            tk.Label(inner, text=value, font=('Segoe UI', 20, 'bold'), bg=self.colors['bg_card'],
                    fg=self.colors['text']).pack()
            tk.Label(inner, text=label, font=('Segoe UI', 10), bg=self.colors['bg_card'],
                    fg=self.colors['text_secondary']).pack(pady=(5, 5))

        # Quick actions
        actions_frame = tk.Frame(content, bg=self.colors['bg'])
        actions_frame.pack(fill=tk.X, pady=(0, 20))

        # Quick launch
        quick_card = self.create_card(actions_frame, "Quick Launch")
        quick_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        quick_content = tk.Frame(quick_card, bg=self.colors['bg_card'])
        quick_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        if self.installed_versions:
            tk.Label(quick_content, text=f"Latest installed version:",
                    font=('Segoe UI', 11), bg=self.colors['bg_card'], 
                    fg=self.colors['text_secondary']).pack(anchor=tk.W)
            tk.Label(quick_content, text=self.installed_versions[-1],
                    font=('Segoe UI', 16, 'bold'), bg=self.colors['bg_card'], 
                    fg=self.colors['accent']).pack(anchor=tk.W, pady=(2, 0))

            play_btn = self.create_button(quick_content, "▶  PLAY NOW", self.quick_play,
                                         bg=self.colors['success'], hover_bg='#059669',
                                         font=('Segoe UI', 14, 'bold'), padx=35, pady=14)
            play_btn.pack(anchor=tk.W, pady=(20, 0))
        else:
            tk.Label(quick_content, text="No versions installed",
                    font=('Segoe UI', 12), bg=self.colors['bg_card'],
                    fg=self.colors['text_secondary']).pack(anchor=tk.W)

            install_btn = self.create_button(quick_content, "+ Install Version", 
                                            lambda: self.navigate(self.show_install, "install"),
                                            font=('Segoe UI', 12, 'bold'), padx=25, pady=12)
            install_btn.pack(anchor=tk.W, pady=(15, 0))

        # Info
        info_card = self.create_card(actions_frame, "System Info")
        info_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        info_content = tk.Frame(info_card, bg=self.colors['bg_card'])
        info_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        info_items = [
            ("Launcher", "v2.0.0"),
            ("Game folder", self.game_folder_name),
            ("Mode", "Offline"),
            ("Java", self.java_path.get() or "System default"),
        ]

        for label, value in info_items:
            row = tk.Frame(info_content, bg=self.colors['bg_card'])
            row.pack(fill=tk.X, pady=6)
            tk.Label(row, text=f"{label}:", font=('Segoe UI', 10),
                    bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack(side=tk.LEFT)
            tk.Label(row, text=value, font=('Segoe UI', 10, 'bold'),
                    bg=self.colors['bg_card'], fg=self.colors['text']).pack(side=tk.RIGHT)

    def get_greeting(self):
        """Get greeting based on time"""
        hour = time.localtime().tm_hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 22:
            return "Good evening"
        else:
            return "Good night"

    def show_launch(self):
        """Launch screen"""
        self.clear_container()
        self.page_title.config(text="Launch Game")
        if hasattr(self, 'title_accent'):
            self.title_accent.config(bg=self.colors['accent'])

        left = tk.Frame(self.page_container, bg=self.colors['bg'])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right = tk.Frame(self.page_container, bg=self.colors['bg'])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Left panel - launch settings
        settings_card = self.create_card(left, "Launch Settings")
        settings_card.pack(fill=tk.BOTH, expand=True)

        settings_content = tk.Frame(settings_card, bg=self.colors['bg_card'])
        settings_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Version
        tk.Label(settings_content, text="Version", font=('Segoe UI', 11, 'bold'),
                bg=self.colors['bg_card'], fg=self.colors['text']).pack(anchor=tk.W, pady=(10, 5))

        self.version_combo = ttk.Combobox(settings_content, textvariable=self.selected_version,
                                         state="readonly", font=('Segoe UI', 11),
                                         style="Modern.TCombobox")
        self.version_combo.pack(fill=tk.X, pady=(0, 15))

        # Username
        self.create_entry(settings_content, self.username, "Username")

        # RAM
        ram_frame = tk.Frame(settings_content, bg=self.colors['bg_card'])
        ram_frame.pack(fill=tk.X, pady=(5, 15))

        tk.Label(ram_frame, text="RAM (MB)", font=('Segoe UI', 10),
                bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack(anchor=tk.W)

        ram_scale = tk.Scale(ram_frame, from_=1024, to=16384, resolution=256,
                            orient=tk.HORIZONTAL, variable=self.ram,
                            bg=self.colors['bg_card'], fg=self.colors['text'],
                            highlightthickness=0, troughcolor=self.colors['bg_tertiary'],
                            activebackground=self.colors['accent'], sliderrelief=tk.FLAT,
                            font=('Segoe UI', 9))
        ram_scale.pack(fill=tk.X)

        # Resolution
        res_frame = tk.Frame(settings_content, bg=self.colors['bg_card'])
        res_frame.pack(fill=tk.X, pady=5)

        tk.Label(res_frame, text="Resolution", font=('Segoe UI', 10),
                bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack(anchor=tk.W)

        res_inputs = tk.Frame(res_frame, bg=self.colors['bg_card'])
        res_inputs.pack(fill=tk.X, pady=5)

        tk.Entry(res_inputs, textvariable=self.game_width, bg=self.colors['bg_tertiary'],
                fg=self.colors['text'], bd=0, font=('Segoe UI', 11), width=8).pack(side=tk.LEFT)
        tk.Label(res_inputs, text=" x ", bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack(side=tk.LEFT)
        tk.Entry(res_inputs, textvariable=self.game_height, bg=self.colors['bg_tertiary'],
                fg=self.colors['text'], bd=0, font=('Segoe UI', 11), width=8).pack(side=tk.LEFT)

        # Checkboxes
        checks_frame = tk.Frame(settings_content, bg=self.colors['bg_card'])
        checks_frame.pack(fill=tk.X, pady=10)

        tk.Checkbutton(checks_frame, text="Fullscreen", variable=self.fullscreen,
                      bg=self.colors['bg_card'], fg=self.colors['text'], selectcolor=self.colors['bg_tertiary'],
                      activebackground=self.colors['bg_card'], font=('Segoe UI', 10)).pack(anchor=tk.W)

        tk.Checkbutton(checks_frame, text="Show FPS", variable=self.show_fps,
                      bg=self.colors['bg_card'], fg=self.colors['text'], selectcolor=self.colors['bg_tertiary'],
                      activebackground=self.colors['bg_card'], font=('Segoe UI', 10)).pack(anchor=tk.W)

        # Launch button
        launch_btn = self.create_button(settings_content, "LAUNCH GAME", self.launch_game,
                                       bg=self.colors['success'], hover_bg='#16a34a',
                                       font=('Segoe UI', 14, 'bold'), padx=30, pady=15)
        launch_btn.pack(fill=tk.X, pady=(20, 10))

        # Right panel - console and skin
        # Skin preview
        skin_card = self.create_card(right, "Skin Preview")
        skin_card.pack(fill=tk.X, pady=(0, 10))

        skin_preview_frame = tk.Frame(skin_card, bg=self.colors['bg_card'], height=200)
        skin_preview_frame.pack(fill=tk.X, padx=20, pady=10)
        skin_preview_frame.pack_propagate(False)

        if self.skin_image:
            preview_label = tk.Label(skin_preview_frame, image=self.skin_image, bg=self.colors['bg_card'])
            preview_label.pack()
        else:
            tk.Label(skin_preview_frame, text="No skin loaded", font=('Segoe UI', 12),
                    bg=self.colors['bg_card'], fg=self.colors['text_secondary']).place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Console
        console_card = self.create_card(right, "Console")
        console_card.pack(fill=tk.BOTH, expand=True)

        console_frame = tk.Frame(console_card, bg=self.colors['bg_tertiary'])
        console_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.console = tk.Text(console_frame, bg='#0d1117', fg='#a5b4fc',
                              font=('JetBrains Mono', 10), bd=0, wrap=tk.WORD,
                              insertbackground=self.colors['accent'], padx=12, pady=12,
                              selectbackground=self.colors['accent3'], selectforeground='white')
        self.console.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.console, bg=self.colors['bg_tertiary'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.console.yview)

        self.refresh_installed_versions()

    def show_install(self):
        """Install screen"""
        self.clear_container()
        self.page_title.config(text="Install Versions")
        if hasattr(self, 'title_accent'):
            self.title_accent.config(bg=self.colors['accent'])

        # Search
        search_card = self.create_card(self.page_container, "Search Versions")
        search_card.pack(fill=tk.X, pady=(0, 15))

        search_frame = tk.Frame(search_card, bg=self.colors['bg_card'])
        search_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(search_frame, text="🔍", font=('Segoe UI', 14), bg=self.colors['bg_card'],
                fg=self.colors['text_secondary']).pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, bg=self.colors['bg_tertiary'],
                               fg=self.colors['text'], bd=0, font=('Segoe UI', 12), insertbackground=self.colors['accent'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Filters
        filter_frame = tk.Frame(search_card, bg=self.colors['bg_card'])
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        self.version_filter = tk.StringVar(value="all")
        filters = [("All", "all"), ("Releases", "release"), ("Snapshots", "snapshot"), ("Old", "old")]

        for text, value in filters:
            tk.Radiobutton(filter_frame, text=text, variable=self.version_filter, value=value,
                          bg=self.colors['bg_card'], fg=self.colors['text'], selectcolor=self.colors['bg_tertiary'],
                          activebackground=self.colors['bg_card'], font=('Segoe UI', 10),
                          command=self.apply_filter).pack(side=tk.LEFT, padx=5)

        # Version list
        list_frame = tk.Frame(self.page_container, bg=self.colors['bg'])
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Left - list
        versions_card = self.create_card(list_frame, "Available Versions")
        versions_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        list_container = tk.Frame(versions_card, bg=self.colors['bg_card'])
        list_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(list_container, bg=self.colors['bg_tertiary'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.versions_listbox = tk.Listbox(list_container, bg=self.colors['bg_tertiary'],
                                           fg=self.colors['text'], selectbackground=self.colors['accent3'],
                                           selectforeground=self.colors['text'],
                                           bd=0, font=('Segoe UI', 11), yscrollcommand=scrollbar.set,
                                           selectmode=tk.SINGLE, highlightthickness=0,
                                           activestyle='none')
        self.versions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.versions_listbox.yview)

        # Right - details and buttons
        details_card = self.create_card(list_frame, "Actions")
        details_card.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        details_content = tk.Frame(details_card, bg=self.colors['bg_card'])
        details_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.version_info_label = tk.Label(details_content, text="Select a version",
                                          font=('Segoe UI', 12), bg=self.colors['bg_card'],
                                          fg=self.colors['text_secondary'], wraplength=250)
        self.version_info_label.pack(pady=20)

        install_btn = self.create_button(details_content, "INSTALL", self.install_version,
                                        font=('Segoe UI', 12, 'bold'), padx=20, pady=12)
        install_btn.pack(fill=tk.X, pady=(0, 10))

        refresh_btn = self.create_button(details_content, "REFRESH LIST", self.load_versions,
                                        bg=self.colors['bg_tertiary'], fg=self.colors['text'],
                                        hover_bg=self.colors['border'], font=('Segoe UI', 11), padx=15, pady=10)
        refresh_btn.pack(fill=tk.X, pady=(0, 10))

        self.update_versions_list()

    def show_skins(self):
        """Skins screen with enhanced preview"""
        self.clear_container()
        self.page_title.config(text="Skin Manager")
        if hasattr(self, 'title_accent'):
            self.title_accent.config(bg=self.colors['accent'])

        left = tk.Frame(self.page_container, bg=self.colors['bg'])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right = tk.Frame(self.page_container, bg=self.colors['bg'])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Left panel - upload
        upload_card = self.create_card(left, "Upload Skin")
        upload_card.pack(fill=tk.BOTH, expand=True)

        upload_content = tk.Frame(upload_card, bg=self.colors['bg_card'])
        upload_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(upload_content, text="Upload a skin for your character", 
                font=('Segoe UI', 12), bg=self.colors['bg_card'], 
                fg=self.colors['text_secondary']).pack(anchor=tk.W, pady=(0, 15))

        tk.Label(upload_content, text="Supported: PNG, 64x64 or 64x32", 
                font=('Segoe UI', 10), bg=self.colors['bg_card'], 
                fg=self.colors['text_muted']).pack(anchor=tk.W, pady=(0, 20))

        upload_btn = self.create_button(upload_content, "SELECT FILE", self.upload_skin,
                                       font=('Segoe UI', 12, 'bold'), padx=25, pady=12)
        upload_btn.pack(anchor=tk.W, pady=(0, 15))

        # URL upload
        tk.Label(upload_content, text="Or enter skin URL:", 
                font=('Segoe UI', 10), bg=self.colors['bg_card'], 
                fg=self.colors['text_secondary']).pack(anchor=tk.W, pady=(10, 5))

        url_frame = tk.Frame(upload_content, bg=self.colors['bg_card'])
        url_frame.pack(fill=tk.X, pady=(0, 15))

        self.skin_url_var = tk.StringVar()
        url_entry = tk.Entry(url_frame, textvariable=self.skin_url_var, bg=self.colors['bg_tertiary'],
                            fg=self.colors['text'], bd=0, font=('Segoe UI', 11), insertbackground=self.colors['accent'])
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        url_btn = self.create_button(url_frame, "Download", self.download_skin_from_url,
                                    font=('Segoe UI', 10, 'bold'), padx=15, pady=5)
        url_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Skin history
        skin_files = list(self.skins_dir.glob("*.png"))
        if skin_files and len(skin_files) > 1:
            tk.Label(upload_content, text="Skin history:", 
                    font=('Segoe UI', 11, 'bold'), bg=self.colors['bg_card'], 
                    fg=self.colors['text']).pack(anchor=tk.W, pady=(20, 10))

            skins_frame = tk.Frame(upload_content, bg=self.colors['bg_card'])
            skins_frame.pack(fill=tk.X)

            for skin_file in sorted(skin_files)[:5]:
                if skin_file.name == "current_skin.png":
                    continue
                skin_row = tk.Frame(skins_frame, bg=self.colors['bg_tertiary'], padx=10, pady=5)
                skin_row.pack(fill=tk.X, pady=2)
                skin_row.bind("<Button-1>", lambda e, f=skin_file: self.load_skin_file(f))

                tk.Label(skin_row, text=skin_file.name, font=('Segoe UI', 10),
                        bg=self.colors['bg_tertiary'], fg=self.colors['text']).pack(side=tk.LEFT)

                tk.Label(skin_row, text="Click to apply", font=('Segoe UI', 8),
                        bg=self.colors['bg_tertiary'], fg=self.colors['text_muted']).pack(side=tk.RIGHT)

        # Right panel - preview
        preview_card = self.create_card(right, "Skin Preview")
        preview_card.pack(fill=tk.BOTH, expand=True)

        preview_content = tk.Frame(preview_card, bg=self.colors['bg_card'])
        preview_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Canvas for skin preview with frame
        canvas_frame = tk.Frame(preview_content, bg=self.colors['border'], padx=2, pady=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.skin_canvas = tk.Canvas(canvas_frame, bg=self.colors['bg_tertiary'], 
                                    highlightthickness=0, height=300)
        self.skin_canvas.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.draw_skin_preview()

        # Skin info
        self.skin_info_label = tk.Label(preview_content, text="No skin loaded",
                                       font=('Segoe UI', 11), bg=self.colors['bg_card'],
                                       fg=self.colors['text_secondary'])
        self.skin_info_label.pack(pady=10)

        # Buttons
        btn_frame = tk.Frame(preview_content, bg=self.colors['bg_card'])
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        if self.current_skin.get():
            remove_btn = self.create_button(btn_frame, "REMOVE SKIN", self.remove_skin,
                                           bg=self.colors['error'], hover_bg='#dc2626',
                                           font=('Segoe UI', 10, 'bold'), padx=15, pady=8)
            remove_btn.pack(side=tk.LEFT, padx=(0, 10))

    def upload_skin(self):
        """Upload skin from file"""
        file_path = filedialog.askopenfilename(
            title="Select skin",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            self.process_skin_file(Path(file_path))

    def download_skin_from_url(self):
        """Download skin from URL"""
        url = self.skin_url_var.get().strip()
        if not url:
            messagebox.showwarning("Error", "Enter URL")
            return

        try:
            self.update_status("Downloading skin...", "◐")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            skin_name = f"skin_{int(time.time())}.png"
            skin_path = self.skins_dir / skin_name

            with open(skin_path, 'wb') as f:
                f.write(response.content)

            self.process_skin_file(skin_path)
            self.skin_url_var.set("")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to download skin: {e}")
            self.update_status("Skin download error", "●")

    def process_skin_file(self, file_path):
        """Process skin file"""
        try:
            img = Image.open(file_path)

            # Check dimensions
            if img.size not in [(64, 32), (64, 64)]:
                messagebox.showwarning("Warning", 
                    f"Unusual skin size: {img.size}. Recommended: 64x64 or 64x32.")

            # Save as current skin
            current_skin_path = self.skins_dir / "current_skin.png"
            shutil.copy(file_path, current_skin_path)

            self.current_skin.set(str(current_skin_path))
            self.config["skin"] = str(current_skin_path)
            self.save_config()

            self.load_skin_preview()
            self.load_skin_avatar()

            # Refresh skin page if open
            if self.current_page == "skins":
                self.show_skins()
            else:
                self.draw_skin_preview()

            self.update_status("Skin loaded!", "●")
            messagebox.showinfo("Success", "Skin loaded successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process skin: {e}")

    def load_skin_file(self, file_path):
        """Load skin from history"""
        self.process_skin_file(file_path)

    def remove_skin(self):
        """Remove skin"""
        if messagebox.askyesno("Confirm", "Remove current skin?"):
            current_skin_path = self.skins_dir / "current_skin.png"
            if current_skin_path.exists():
                current_skin_path.unlink()
            self.current_skin.set("")
            self.config["skin"] = ""
            self.save_config()
            self.skin_image = None

            if self.current_page == "skins":
                self.show_skins()
            else:
                self.draw_skin_preview()

            # Clear avatar
            self.avatar_label.config(image="")
            self.avatar_image = None
            messagebox.showinfo("Success", "Skin removed")

    def load_skin_preview(self):
        """Load skin preview"""
        skin_path = self.current_skin.get()
        if skin_path and Path(skin_path).exists():
            try:
                img = Image.open(skin_path)
                img = img.resize((128, 128), Image.Resampling.LANCZOS)
                self.skin_image = ImageTk.PhotoImage(img)
            except:
                self.skin_image = None
        else:
            self.skin_image = None

    def load_skin_avatar(self):
        """Load skin avatar for header"""
        skin_path = self.current_skin.get()
        if skin_path and Path(skin_path).exists():
            try:
                img = Image.open(skin_path)
                # Crop head area
                head = img.crop((8, 8, 16, 16))
                head = head.resize((40, 40), Image.Resampling.NEAREST)

                # Create circular mask
                mask = Image.new('L', (40, 40), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 40, 40), fill=255)

                output = Image.new('RGBA', (40, 40), (0, 0, 0, 0))
                output.paste(head, (0, 0))
                output.putalpha(mask)

                self.avatar_image = ImageTk.PhotoImage(output)
                self.avatar_label.config(image=self.avatar_image)
            except:
                pass
        else:
            # Clear avatar if no skin
            self.avatar_label.config(image="")
            self.avatar_image = None

    def draw_skin_preview(self):
        """Draw skin preview on canvas with modern styling"""
        if hasattr(self, 'skin_canvas') and self.skin_canvas.winfo_exists():
            self.skin_canvas.delete("all")

            w = self.skin_canvas.winfo_width() or 400
            h = self.skin_canvas.winfo_height() or 300

            # Background with subtle pattern
            self.skin_canvas.create_rectangle(0, 0, w, h, fill=self.colors['bg_tertiary'], outline="")

            # Grid pattern
            for i in range(0, w, 20):
                self.skin_canvas.create_line(i, 0, i, h, fill='#1e1e2e', width=1)
            for i in range(0, h, 20):
                self.skin_canvas.create_line(0, i, w, i, fill='#1e1e2e', width=1)

            if self.skin_image:
                x = w // 2 - 64
                y = h // 2 - 64

                # Shadow effect
                self.skin_canvas.create_rectangle(x+4, y+4, x+132, y+132, 
                                                  fill='#000000', stipple='gray50', outline="")
                self.skin_canvas.create_image(x, y, image=self.skin_image, anchor=tk.NW)

                if hasattr(self, 'skin_info_label') and self.skin_info_label.winfo_exists():
                    self.skin_info_label.config(text=f"✓ Skin active  •  {self.skin_image.width()}x{self.skin_image.height()}",
                                               fg=self.colors['success'])
            else:
                # Placeholder with icon
                self.skin_canvas.create_text(w//2, h//2 - 15, text="🎨", 
                                            fill=self.colors['text_muted'], font=('Segoe UI', 32))
                self.skin_canvas.create_text(w//2, h//2 + 25, text="No skin selected", 
                                            fill=self.colors['text_muted'], font=('Segoe UI', 12))

    def show_profiles(self):
        """Profiles screen"""
        self.clear_container()
        self.page_title.config(text="Profiles")
        if hasattr(self, 'title_accent'):
            self.title_accent.config(bg=self.colors['accent'])

        left = tk.Frame(self.page_container, bg=self.colors['bg'])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right = tk.Frame(self.page_container, bg=self.colors['bg'])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Profile list
        list_card = self.create_card(left, "Saved Profiles")
        list_card.pack(fill=tk.BOTH, expand=True)

        list_content = tk.Frame(list_card, bg=self.colors['bg_card'])
        list_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(list_content, bg=self.colors['bg_tertiary'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.profiles_listbox = tk.Listbox(list_content, bg=self.colors['bg_tertiary'],
                                           fg=self.colors['text'], selectbackground=self.colors['accent'],
                                           bd=0, font=('Segoe UI', 11), yscrollcommand=scrollbar.set,
                                           highlightthickness=0)
        self.profiles_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.profiles_listbox.yview)

        # Buttons
        btn_frame = tk.Frame(list_content, bg=self.colors['bg_card'])
        btn_frame.pack(fill=tk.X, pady=10)

        self.create_button(btn_frame, "SAVE", self.save_profile,
                          font=('Segoe UI', 10, 'bold'), padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        self.create_button(btn_frame, "LOAD", self.load_profile,
                          bg=self.colors['bg_tertiary'], fg=self.colors['text'],
                          hover_bg=self.colors['border'], font=('Segoe UI', 10), padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        self.create_button(btn_frame, "DELETE", self.delete_profile,
                          bg=self.colors['error'], hover_bg='#dc2626',
                          font=('Segoe UI', 10, 'bold'), padx=15, pady=8).pack(side=tk.LEFT, padx=5)

        # Profile details
        details_card = self.create_card(right, "Profile Details")
        details_card.pack(fill=tk.BOTH, expand=True)

        self.profile_details = tk.Label(details_card, text="Select a profile",
                                       font=('Segoe UI', 12), bg=self.colors['bg_card'],
                                       fg=self.colors['text_secondary'], justify=tk.LEFT)
        self.profile_details.pack(padx=20, pady=20)

        self.profiles_listbox.bind('<<ListboxSelect>>', self.on_profile_select)

        self.update_profiles_list()

    def on_profile_select(self, event):
        """Profile selection"""
        sel = self.profiles_listbox.curselection()
        if sel:
            name = self.profiles_listbox.get(sel[0])
            p = self.profiles.get(name, {})
            details = f"""Name: {name}
Version: {p.get('version', 'Not set')}
Username: {p.get('username', 'Not set')}
RAM: {p.get('ram', '4096')} MB
Resolution: {p.get('width', '1280')}x{p.get('height', '720')}
Fullscreen: {'Yes' if p.get('fullscreen', False) else 'No'}
Skin: {'Yes' if p.get('skin', '') else 'No'}"""
            self.profile_details.config(text=details)

    def show_settings(self):
        """Settings screen"""
        self.clear_container()
        self.page_title.config(text="Settings")
        if hasattr(self, 'title_accent'):
            self.title_accent.config(bg=self.colors['accent'])

        left = tk.Frame(self.page_container, bg=self.colors['bg'])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right = tk.Frame(self.page_container, bg=self.colors['bg'])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # General settings
        general_card = self.create_card(left, "General Settings")
        general_card.pack(fill=tk.X, pady=(0, 15))

        general_content = tk.Frame(general_card, bg=self.colors['bg_card'])
        general_content.pack(fill=tk.X, padx=20, pady=10)

        self.create_entry(general_content, self.java_path, "Java Path")

        # Info
        info_card = self.create_card(left, "Launcher Info")
        info_card.pack(fill=tk.BOTH, expand=True)

        info_content = tk.Frame(info_card, bg=self.colors['bg_card'])
        info_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        info_items = [
            ("Launcher version", "2.0.0"),
            ("Game folder", self.game_folder_name),
            ("Game path", str(self.minecraft_dir)),
            ("Skins path", str(self.skins_dir)),
            ("Versions installed", str(len(self.installed_versions))),
            ("Profiles saved", str(len(self.profiles))),
        ]

        for label, value in info_items:
            row = tk.Frame(info_content, bg=self.colors['bg_card'])
            row.pack(fill=tk.X, pady=5)
            tk.Label(row, text=label + ":", font=('Segoe UI', 10),
                    bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack(side=tk.LEFT)
            tk.Label(row, text=value, font=('Segoe UI', 10, 'bold'),
                    bg=self.colors['bg_card'], fg=self.colors['text']).pack(side=tk.RIGHT)

        # Actions
        actions_card = self.create_card(right, "Actions")
        actions_card.pack(fill=tk.X, pady=(0, 15))

        actions_content = tk.Frame(actions_card, bg=self.colors['bg_card'])
        actions_content.pack(fill=tk.X, padx=20, pady=15)

        actions = [
            ("OPEN GAME FOLDER", self.open_folder),
            ("CLEAR CACHE", self.clear_cache),
            ("RESET SETTINGS", self.reset_settings),
            ("SAVE SETTINGS", self.save_all_settings)
        ]

        for text, cmd in actions:
            btn = self.create_button(actions_content, text, cmd,
                                    bg=self.colors['bg_tertiary'], fg=self.colors['text'],
                                    hover_bg=self.colors['border'], font=('Segoe UI', 11), 
                                    padx=15, pady=10)
            btn.pack(fill=tk.X, pady=3)

        # About
        about_card = self.create_card(right, "About")
        about_card.pack(fill=tk.BOTH, expand=True)

        about_content = tk.Frame(about_card, bg=self.colors['bg_card'])
        about_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        about_text = """Project SL Launcher v2.0

Enhanced Minecraft launcher with:
- Dark modern design
- Skin management
- Player profiles
- Enhanced console
- Animations and effects

Designed for comfortable gaming."""

        tk.Label(about_content, text=about_text, font=('Segoe UI', 11),
                bg=self.colors['bg_card'], fg=self.colors['text_secondary'],
                justify=tk.LEFT).pack(anchor=tk.W)

    def apply_filter(self):
        """Apply version filter"""
        self.update_versions_list()

    def quick_play(self):
        """Quick launch"""
        if not self.installed_versions:
            messagebox.showwarning("Error", "Install a Minecraft version first!")
            self.navigate(self.show_install, "install")
            return
        self.selected_version.set(self.installed_versions[-1])
        self.launch_game()

    def launch_game(self):
        """Launch game with enhanced parameters"""
        version = self.selected_version.get()
        username = self.username.get().strip() or "Player"
        ram_mb = int(self.ram.get()) if self.ram.get().isdigit() else 4096
        width = int(self.game_width.get()) if self.game_width.get().isdigit() else 1280
        height = int(self.game_height.get()) if self.game_height.get().isdigit() else 720

        if not version:
            messagebox.showwarning("Error", "Select a version")
            return

        def launch():
            try:
                self.update_status(f"Launching {version}...", "◐")
                self.update_console(f"\n[LAUNCH] Minecraft {version}\n")
                self.update_console(f"[INFO] Player: {username}\n")
                self.update_console(f"[INFO] RAM: {ram_mb} MB\n")
                self.update_console(f"[INFO] Resolution: {width}x{height}\n")

                # Генерируем offline UUID для скина
                player_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, username))

                options = {
                    "username": username,
                    "uuid": player_uuid,
                    "token": player_uuid,
                    "jvmArguments": [
                        f"-Xmx{ram_mb}M",
                        f"-Xms{ram_mb//2}M",
                    ],
                    "gameDirectory": str(self.minecraft_dir),
                    "resolution": {
                        "width": width,
                        "height": height
                    }
                }

                # Добавляем скин если есть
                skin_path = self.current_skin.get()
                if skin_path and Path(skin_path).exists():
                    try:
                        with open(skin_path, 'rb') as sf:
                            skin_data = base64.b64encode(sf.read()).decode('utf-8')
                        options["skin"] = skin_data
                        self.update_console(f"[INFO] Skin loaded: {Path(skin_path).name}\n")
                    except Exception as e:
                        self.update_console(f"[WARN] Failed to load skin: {e}\n")

                if self.fullscreen.get():
                    options["jvmArguments"].append("-Dfml.earlyprogresswindow=false")

                command = minecraft_launcher_lib.command.get_minecraft_command(
                    version, str(self.minecraft_dir), options
                )

                # Add window parameters
                if self.fullscreen.get():
                    command.append("--fullscreen")
                else:
                    command.extend(["--width", str(width), "--height", str(height)])

                self.update_console("[LAUNCH] Starting process...\n")
                process = subprocess.Popen(command, stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE, text=True, 
                                          cwd=str(self.minecraft_dir))

                def read_output(pipe, prefix):
                    for line in iter(pipe.readline, ''):
                        self.update_console(f"{prefix} {line}")
                    pipe.close()

                threading.Thread(target=read_output, args=(process.stdout, "[OUT]"), daemon=True).start()
                threading.Thread(target=read_output, args=(process.stderr, "[ERR]"), daemon=True).start()

                self.update_status("Game running!", "●")
                process.wait()
                self.update_console(f"\n[INFO] Game finished\n")
                self.update_status("Ready", "●")

            except Exception as e:
                self.update_status("Launch error", "●")
                self.update_console(f"[ERROR] {e}\n")
                messagebox.showerror("Error", f"Failed to launch: {e}")

        threading.Thread(target=launch, daemon=True).start()

    def install_version(self):
        """Install version"""
        if not hasattr(self, 'versions_listbox'):
            return

        selection = self.versions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Error", "Select a version")
            return

        # Extract version from formatted text
        version_text = self.versions_listbox.get(selection[0])
        version = version_text.split(" ", 1)[1] if " " in version_text else version_text

        if self.is_installing:
            messagebox.showwarning("Error", "Installation in progress")
            return

        def install():
            self.is_installing = True
            try:
                self.update_status(f"Installing {version}...", "◐")
                self.download_progress.set(0)

                max_progress = [1]

                def set_max(value):
                    max_progress[0] = max(value, 1)

                def set_progress(value):
                    try:
                        pct = (value / max_progress[0]) * 100
                        self.root.after(0, lambda p=pct: self.download_progress.set(p))
                    except Exception:
                        pass

                def set_status(text):
                    try:
                        self.root.after(0, lambda t=text: self.update_console(f"[INSTALL] {t}\n"))
                    except Exception:
                        pass

                callback = {
                    "setStatus": set_status,
                    "setProgress": set_progress,
                    "setMax": set_max,
                }

                minecraft_launcher_lib.install.install_minecraft_version(
                    version, str(self.minecraft_dir), callback=callback
                )

                self.download_progress.set(100)
                self.refresh_installed_versions()
                self.update_status(f"Installed!", "●")
                self.update_console(f"[SUCCESS] Version {version} installed!\n")
                messagebox.showinfo("Success", f"Version {version} installed!")

                time.sleep(1)
                self.download_progress.set(0)

            except Exception as e:
                self.update_status("Installation error", "●")
                self.update_console(f"[ERROR] {e}\n")
                messagebox.showerror("Error", f"Failed to install:\n{str(e)}")
            finally:
                self.is_installing = False

        threading.Thread(target=install, daemon=True).start()

    def load_versions(self):
        """Load version list"""
        def load():
            try:
                self.update_status("Loading list...", "◐")
                versions = minecraft_launcher_lib.utils.get_version_list()
                self.available_versions = versions
                self.root.after(0, self.update_versions_list)
                self.update_status(f"Loaded {len(versions)} versions", "●")
            except Exception as e:
                self.update_status("Error", "●")
                messagebox.showerror("Error", f"Failed to load versions: {e}")

        threading.Thread(target=load, daemon=True).start()

    def load_versions_background(self):
        """Background version loading"""
        def load():
            try:
                versions = minecraft_launcher_lib.utils.get_version_list()
                self.available_versions = versions
                self.root.after(0, self.update_versions_list)
            except:
                pass
        threading.Thread(target=load, daemon=True).start()

    def update_versions_list(self):
        """Update version list with filter"""
        if hasattr(self, 'versions_listbox'):
            try:
                if self.versions_listbox.winfo_exists():
                    self.versions_listbox.delete(0, tk.END)

                    filter_type = getattr(self, 'version_filter', tk.StringVar(value="all")).get()
                    search = getattr(self, 'search_var', tk.StringVar()).get().lower()

                    filtered = []
                    for v in self.available_versions:
                        if filter_type == "all" or v['type'] == filter_type or (filter_type == "old" and v['type'] in ['old_alpha', 'old_beta']):
                            if not search or search in v['id'].lower():
                                filtered.append(v)

                    for v in filtered[:100]:
                        type_icon = {"release": "●", "snapshot": "◐", "old_alpha": "◑", "old_beta": "◑"}.get(v['type'], "○")
                        self.versions_listbox.insert(tk.END, f"{type_icon} {v['id']}")
            except tk.TclError:
                pass

    def on_search(self, *args):
        """Search versions"""
        self.update_versions_list()

    def refresh_installed_versions(self):
        """Refresh installed versions list"""
        self.installed_versions = []
        real_versions_dir = self.minecraft_dir / "versions"
        if real_versions_dir.exists():
            for vd in real_versions_dir.iterdir():
                if vd.is_dir() and (vd / f"{vd.name}.jar").exists():
                    self.installed_versions.append(vd.name)

        self.installed_versions.sort()

        # Update sidebar label
        if hasattr(self, 'version_count_label'):
            self.version_count_label.config(text=f"Versions: {len(self.installed_versions)}")

        def _update_combo():
            if hasattr(self, 'version_combo'):
                try:
                    if self.version_combo.winfo_exists():
                        self.version_combo['values'] = self.installed_versions
                        if self.installed_versions and not self.selected_version.get():
                            self.selected_version.set(self.installed_versions[-1])
                except tk.TclError:
                    pass

        self.root.after(0, _update_combo)

    def save_profile(self):
        """Save profile"""
        name = simpledialog.askstring("Save", "Profile name:")
        if name:
            self.profiles[name] = {
                "version": self.selected_version.get(),
                "username": self.username.get(),
                "ram": self.ram.get(),
                "width": self.game_width.get(),
                "height": self.game_height.get(),
                "fullscreen": self.fullscreen.get(),
                "show_fps": self.show_fps.get(),
                "skin": self.current_skin.get()
            }
            with open(self.launcher_dir / "profiles.dat", 'w') as f:
                json.dump(self.profiles, f, indent=4)
            self.update_profiles_list()
            messagebox.showinfo("Success", f"Profile '{name}' saved")

    def load_profile(self):
        """Load profile"""
        sel = self.profiles_listbox.curselection()
        if sel:
            name = self.profiles_listbox.get(sel[0])
            p = self.profiles[name]
            self.selected_version.set(p.get("version", ""))
            self.username.set(p.get("username", "Player"))
            self.ram.set(p.get("ram", "4096"))
            self.game_width.set(p.get("width", "1280"))
            self.game_height.set(p.get("height", "720"))
            self.fullscreen.set(p.get("fullscreen", False))
            self.show_fps.set(p.get("show_fps", False))

            skin = p.get("skin", "")
            if skin and Path(skin).exists():
                self.current_skin.set(skin)
                self.load_skin_preview()
                self.load_skin_avatar()

            messagebox.showinfo("Success", f"Profile '{name}' loaded")

    def delete_profile(self):
        """Delete profile"""
        sel = self.profiles_listbox.curselection()
        if sel:
            name = self.profiles_listbox.get(sel[0])
            if messagebox.askyesno("Confirm", f"Delete '{name}'?"):
                del self.profiles[name]
                with open(self.launcher_dir / "profiles.dat", 'w') as f:
                    json.dump(self.profiles, f, indent=4)
                self.update_profiles_list()

    def update_profiles_list(self):
        """Update profiles list"""
        if hasattr(self, 'profiles_listbox'):
            try:
                if self.profiles_listbox.winfo_exists():
                    self.profiles_listbox.delete(0, tk.END)
                    for name in self.profiles:
                        self.profiles_listbox.insert(tk.END, name)
            except tk.TclError:
                pass

    def load_profiles(self):
        """Load profiles"""
        pf = self.launcher_dir / "profiles.dat"
        if pf.exists():
            try:
                with open(pf, 'r') as f:
                    self.profiles = json.load(f)
            except:
                self.profiles = {}

    def load_config(self):
        """Load config"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        """Save config"""
        self.config["username"] = self.username.get()
        self.config["ram"] = int(self.ram.get()) if self.ram.get().isdigit() else 4096
        self.config["java_path"] = self.java_path.get()
        self.config["width"] = int(self.game_width.get()) if self.game_width.get().isdigit() else 1280
        self.config["height"] = int(self.game_height.get()) if self.game_height.get().isdigit() else 720
        self.config["fullscreen"] = self.fullscreen.get()
        self.config["show_fps"] = self.show_fps.get()
        self.config["skin"] = self.current_skin.get()
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def save_all_settings(self):
        """Save all settings"""
        self.save_config()
        messagebox.showinfo("Success", "Settings saved")

    def open_folder(self):
        """Open game folder"""
        if sys.platform == 'win32':
            os.startfile(self.minecraft_dir)
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(self.minecraft_dir)])
        else:
            subprocess.run(['xdg-open', str(self.minecraft_dir)])

    def clear_cache(self):
        """Clear cache"""
        if messagebox.askyesno("Confirm", "Clear cache?"):
            try:
                cache_dirs = [
                    self.minecraft_dir / "assets" / "objects",
                    self.minecraft_dir / "assets" / "indexes",
                ]
                cleared = 0
                for d in cache_dirs:
                    if d.exists():
                        for item in d.iterdir():
                            if item.is_file():
                                item.unlink()
                                cleared += 1
                            elif item.is_dir():
                                shutil.rmtree(item)
                                cleared += 1
                self.update_console(f"[INFO] Cleared {cleared} items\n")
                messagebox.showinfo("Success", f"Cache cleared ({cleared} items)")
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")

    def reset_settings(self):
        """Reset settings"""
        if messagebox.askyesno("Confirm", "Reset settings?"):
            self.username.set("Player")
            self.ram.set("4096")
            self.java_path.set("java")
            self.game_width.set("1280")
            self.game_height.set("720")
            self.fullscreen.set(False)
            self.show_fps.set(False)
            self.save_config()
            messagebox.showinfo("Success", "Settings reset")

    def update_console(self, text):
        """Update console"""
        def update():
            if hasattr(self, 'console') and self.console.winfo_exists():
                try:
                    self.console.insert(tk.END, text)
                    self.console.see(tk.END)
                except:
                    pass
        self.root.after(0, update)

    def update_status(self, text, icon="●"):
        """Update status with color coding"""
        def update():
            try:
                color_map = {
                    "●": self.colors['success'],
                    "●": self.colors['success'],
                    "◐": self.colors['warning'],
                    "●": self.colors['error'],
                }
                self.status_icon.config(text=icon if icon in color_map else "●",
                                       fg=color_map.get(icon, self.colors['success']))
                self.install_status.set(text)
            except:
                pass
        self.root.after(0, update)

def main():
    root = tk.Tk()
    app = ModernDarkLauncher(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.save_config(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    try:
        import minecraft_launcher_lib
        print("OK: minecraft-launcher-lib found")
    except ImportError:
        print("ERROR: pip install minecraft-launcher-lib")
        sys.exit(1)

    try:
        from PIL import Image, ImageTk, ImageDraw
        print("OK: Pillow found")
    except ImportError:
        print("ERROR: pip install Pillow")
        sys.exit(1)

    try:
        import requests
        print("OK: requests found")
    except ImportError:
        print("ERROR: pip install requests")
        sys.exit(1)

    main()
