import os
import sys
import json
import time
import threading
import requests
import webbrowser
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import filedialog

# --- TEMA VE RENK AYARLARI ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

KOLETH_PURPLE = "#8b5cf6"
KOLETH_PURPLE_HOVER = "#7c3aed"
BG_MATTE_BLACK = "#0a0a0a"
FG_DARK_GRAY = "#171717"
FG_LIGHT_GRAY = "#262626"
TEXT_WHITE = "#ffffff"
TEXT_MUTED = "#a3a3a3"
SUCCESS_GREEN = "#10b981"
ERROR_RED = "#ef4444"

def get_profiles_path():
    """
    Profillerin kaydedileceği yolu belirler.
    Eğer uygulama .exe olarak çalışıyorsa (PyInstaller), verileri kullanıcının AppData klasörüne kaydeder.
    Böylece .exe güncellense bile profiller silinmez ve yazma izni sorunu yaşanmaz.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller ile derlenmişse
        app_data_dir = os.path.join(os.environ.get('APPDATA', ''), 'KolethHookMaster')
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)
        return os.path.join(app_data_dir, 'profiles.json')
    else:
        # Normal Python scripti olarak çalışıyorsa
        return "profiles.json"

PROFILES_FILE = get_profiles_path()

class KolethWebhookMaster(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Koleth Hook Master")
        self.geometry("1050x800")
        self.minsize(900, 700) # Minimum boyutu belirliyoruz ki arayüz bozulmasın
        self.configure(fg_color=BG_MATTE_BLACK)
        self.resizable(True, True) # Artık büyütülebilir!

        self.file_path = None
        self.profiles = self.load_profiles()
        self.ensure_default_profile()

        self.create_widgets()

    def ensure_default_profile(self):
        if "Koleth Support" not in self.profiles:
            self.profiles["Koleth Support"] = {
                "webhook_url": "",
                "msg_content": "",
                "mentions": False,
                "author_name": "Koleth Ecosystem",
                "author_icon": "",
                "title": "🚀 Koleth Ecosystem Support",
                "description": "Koleth Hook Master'ı kullandığınız için teşekkürler!\n\n🌐 Web Sitemiz: https://koleth.net.tr\n💻 Teknoloji Blogumuz: https://rodyat.tech\n\nDaha fazla araç ve destek için bizi takip edin!",
                "color": "#8b5cf6",
                "image": "",
                "thumbnail": "",
                "footer_text": "Developing for the future.",
                "footer_icon": ""
            }
            self.save_profiles_to_file()

    def open_github(self):
        webbrowser.open("https://github.com/Koleth")

    def create_widgets(self):
        # --- ÜST BAR (Header) ---
        self.header_frame = ctk.CTkFrame(self, fg_color=FG_DARK_GRAY, corner_radius=0, height=60)
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        self.title_label = ctk.CTkLabel(self.header_frame, text="KOLETH HOOK MASTER", font=("Poppins", 20, "bold"), text_color=KOLETH_PURPLE)
        self.title_label.pack(side="left", padx=20, pady=15)

        self.github_btn = ctk.CTkButton(self.header_frame, text="Get More Tools 🚀", font=("Poppins", 12, "bold"), fg_color=FG_LIGHT_GRAY, hover_color=KOLETH_PURPLE, text_color=TEXT_WHITE, width=120, height=30, corner_radius=15, command=self.open_github)
        self.github_btn.pack(side="right", padx=20, pady=15)

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=25, pady=20)

        # --- 1. WEBHOOK URL GİRİŞİ ---
        self.url_frame = ctk.CTkFrame(self.main_frame, fg_color=FG_DARK_GRAY, corner_radius=15)
        self.url_frame.pack(fill="x", pady=(0, 20))

        self.url_label = ctk.CTkLabel(self.url_frame, text="Webhook URL", font=("Poppins", 14, "bold"), text_color=TEXT_MUTED)
        self.url_label.pack(side="left", padx=20, pady=15)

        self.webhook_url = ctk.CTkEntry(self.url_frame, placeholder_text="https://discord.com/api/webhooks/...", font=("Consolas", 13), width=600, height=40, border_width=2, border_color=FG_LIGHT_GRAY, fg_color=BG_MATTE_BLACK)
        self.webhook_url.pack(side="left", padx=(0, 20), pady=15, fill="x", expand=True)

        # --- ORTA KISIM ---
        self.middle_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.middle_frame.pack(fill="both", expand=True, pady=(0, 20))

        # --- SOL: EMBED EDİTÖRÜ (Scrollable) ---
        self.embed_scroll = ctk.CTkScrollableFrame(self.middle_frame, fg_color=FG_DARK_GRAY, corner_radius=15)
        self.embed_scroll.pack(side="left", fill="both", expand=True, padx=(0, 15))

        def create_section(parent, title):
            frame = ctk.CTkFrame(parent, fg_color=FG_LIGHT_GRAY, corner_radius=10)
            frame.pack(fill="x", padx=15, pady=(15, 0))
            ctk.CTkLabel(frame, text=title, font=("Poppins", 14, "bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=15, pady=(10, 5))
            return frame

        entry_kwargs = {"height": 35, "border_width": 1, "border_color": FG_DARK_GRAY, "fg_color": BG_MATTE_BLACK, "font": ("Poppins", 12)}

        # 1. Mesaj & Etiketler
        sec_msg = create_section(self.embed_scroll, "💬 Normal Mesaj & Etiketler")
        self.msg_content = ctk.CTkTextbox(sec_msg, height=60, border_width=1, border_color=FG_DARK_GRAY, fg_color=BG_MATTE_BLACK, font=("Poppins", 12))
        self.msg_content.pack(fill="x", padx=15, pady=(0, 10))
        self.msg_content.insert("1.0", "Normal mesaj içeriği (İsteğe bağlı)...")
        
        self.mention_switch = ctk.CTkSwitch(sec_msg, text="@everyone ve @here Etiketlerine İzin Ver", font=("Poppins", 12), progress_color=KOLETH_PURPLE)
        self.mention_switch.pack(anchor="w", padx=15, pady=(0, 15))

        # 2. Yazar (Author)
        sec_author = create_section(self.embed_scroll, "👤 Yazar (Author)")
        self.embed_author_name = ctk.CTkEntry(sec_author, placeholder_text="Yazar Adı", **entry_kwargs)
        self.embed_author_name.pack(fill="x", padx=15, pady=(0, 10))
        self.embed_author_icon = ctk.CTkEntry(sec_author, placeholder_text="Yazar İkon URL", **entry_kwargs)
        self.embed_author_icon.pack(fill="x", padx=15, pady=(0, 15))

        # 3. Ana Embed
        sec_main = create_section(self.embed_scroll, "📝 Ana Embed")
        self.embed_title = ctk.CTkEntry(sec_main, placeholder_text="Başlık (Title)", **entry_kwargs)
        self.embed_title.pack(fill="x", padx=15, pady=(0, 10))
        self.embed_desc = ctk.CTkTextbox(sec_main, height=100, border_width=1, border_color=FG_DARK_GRAY, fg_color=BG_MATTE_BLACK, font=("Poppins", 12))
        self.embed_desc.pack(fill="x", padx=15, pady=(0, 10))
        self.embed_desc.insert("1.0", "Açıklama (Description)...")
        self.embed_color = ctk.CTkEntry(sec_main, placeholder_text="Renk Hex (Örn: #8b5cf6)", **entry_kwargs)
        self.embed_color.pack(fill="x", padx=15, pady=(0, 15))

        # 4. Görseller
        sec_img = create_section(self.embed_scroll, "🖼️ Görseller")
        self.embed_image = ctk.CTkEntry(sec_img, placeholder_text="Büyük Resim URL (Image)", **entry_kwargs)
        self.embed_image.pack(fill="x", padx=15, pady=(0, 10))
        self.embed_thumb = ctk.CTkEntry(sec_img, placeholder_text="Küçük Resim URL (Thumbnail)", **entry_kwargs)
        self.embed_thumb.pack(fill="x", padx=15, pady=(0, 15))

        # 5. Altbilgi (Footer)
        sec_footer = create_section(self.embed_scroll, "📌 Altbilgi (Footer)")
        self.embed_footer_text = ctk.CTkEntry(sec_footer, placeholder_text="Altbilgi Metni", **entry_kwargs)
        self.embed_footer_text.pack(fill="x", padx=15, pady=(0, 10))
        self.embed_footer_icon = ctk.CTkEntry(sec_footer, placeholder_text="Altbilgi İkon URL", **entry_kwargs)
        self.embed_footer_icon.pack(fill="x", padx=15, pady=(0, 15))

        # 6. Dosya Eki
        sec_file = create_section(self.embed_scroll, "📎 Dosya Eki")
        file_btn_frame = ctk.CTkFrame(sec_file, fg_color="transparent")
        file_btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.file_btn = ctk.CTkButton(file_btn_frame, text="Dosya Seç", font=("Poppins", 12, "bold"), width=100, fg_color=FG_DARK_GRAY, hover_color=KOLETH_PURPLE, command=self.select_file)
        self.file_btn.pack(side="left")
        self.file_clear_btn = ctk.CTkButton(file_btn_frame, text="X", font=("Poppins", 12, "bold"), width=30, fg_color="#dc2626", hover_color="#b91c1c", command=self.clear_file)
        self.file_clear_btn.pack(side="left", padx=(5, 0))
        self.file_label = ctk.CTkLabel(file_btn_frame, text="Dosya seçilmedi", font=("Poppins", 12), text_color=TEXT_MUTED)
        self.file_label.pack(side="left", padx=(10, 0))

        # 7. Zamanlama (Scheduling)
        sec_schedule = create_section(self.embed_scroll, "⏰ Zamanlayıcı")
        self.schedule_switch = ctk.CTkSwitch(sec_schedule, text="İleri Bir Saatte Gönder", font=("Poppins", 12), progress_color=KOLETH_PURPLE, command=self.toggle_schedule)
        self.schedule_switch.pack(anchor="w", padx=15, pady=(0, 10))
        
        self.schedule_container = ctk.CTkFrame(sec_schedule, fg_color="transparent", height=0)
        self.schedule_container.pack(fill="x", padx=15)
        self.schedule_container.pack_propagate(False)
        
        self.schedule_time = ctk.CTkEntry(self.schedule_container, placeholder_text="Saat (Örn: 14:30)", **entry_kwargs)
        self.schedule_time.pack(fill="x", pady=(0, 15))

        # Boşluk bırakmak için
        ctk.CTkFrame(self.embed_scroll, fg_color="transparent", height=15).pack()

        # --- SAĞ: HIZLI PROFİLLER ---
        self.profile_frame = ctk.CTkFrame(self.middle_frame, fg_color=FG_DARK_GRAY, corner_radius=15, width=280)
        self.profile_frame.pack(side="right", fill="y")
        self.profile_frame.pack_propagate(False)

        self.profile_header = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        self.profile_header.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(self.profile_header, text="Hızlı Profiller", font=("Poppins", 16, "bold"), text_color=TEXT_WHITE).pack(side="left")

        self.profile_name_entry = ctk.CTkEntry(self.profile_frame, placeholder_text="Yeni Profil Adı", **entry_kwargs)
        self.profile_name_entry.pack(pady=(0, 10), padx=20, fill="x")

        self.save_btn = ctk.CTkButton(self.profile_frame, text="Kaydet", font=("Poppins", 13, "bold"), height=35, fg_color=KOLETH_PURPLE, hover_color=KOLETH_PURPLE_HOVER, command=self.save_profile)
        self.save_btn.pack(pady=(0, 20), padx=20, fill="x")

        ctk.CTkFrame(self.profile_frame, height=1, fg_color=FG_LIGHT_GRAY).pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(self.profile_frame, text="Kayıtlı Profiller", font=("Poppins", 12, "bold"), text_color=TEXT_MUTED).pack(pady=(0, 5), padx=20, anchor="w")

        self.profile_var = ctk.StringVar(value="Profil Seçin")
        self.profile_menu = ctk.CTkOptionMenu(self.profile_frame, variable=self.profile_var, values=["Profil Seçin"], height=35, fg_color=BG_MATTE_BLACK, button_color=FG_LIGHT_GRAY, button_hover_color=KOLETH_PURPLE, dropdown_fg_color=FG_DARK_GRAY, dropdown_hover_color=KOLETH_PURPLE, font=("Poppins", 12), dropdown_font=("Poppins", 12))
        self.profile_menu.pack(pady=(0, 10), padx=20, fill="x")
        self.update_profile_menu()

        self.btn_frame = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20)
        
        self.load_btn = ctk.CTkButton(self.btn_frame, text="Yükle", font=("Poppins", 12, "bold"), height=35, fg_color=FG_LIGHT_GRAY, hover_color="#2563eb", command=self.load_profile)
        self.load_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.delete_btn = ctk.CTkButton(self.btn_frame, text="Sil", font=("Poppins", 12, "bold"), height=35, fg_color=FG_LIGHT_GRAY, hover_color="#dc2626", command=self.delete_profile)
        self.delete_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # --- 4. MESAJ GÖNDER BUTONU ---
        self.send_btn = ctk.CTkButton(self.main_frame, text="GÖNDER", font=("Poppins", 22, "bold"), height=60, corner_radius=15, fg_color=KOLETH_PURPLE, hover_color=KOLETH_PURPLE_HOVER, command=self.send_webhook)
        self.send_btn.pack(fill="x", pady=(0, 20))

        # --- 5. LIVE LOG (Terminal Alanı) ---
        self.log_frame = ctk.CTkFrame(self.main_frame, fg_color=BG_MATTE_BLACK, corner_radius=10, border_width=1, border_color=FG_LIGHT_GRAY)
        self.log_frame.pack(fill="x")

        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent", height=30)
        log_header.pack(fill="x", padx=10, pady=(5, 0))
        ctk.CTkLabel(log_header, text="Terminal Log", font=("Consolas", 12, "bold"), text_color=TEXT_MUTED).pack(side="left")
        
        self.clear_log_btn = ctk.CTkButton(log_header, text="🧹 Temizle", font=("Poppins", 11, "bold"), width=70, height=24, fg_color=FG_LIGHT_GRAY, hover_color=KOLETH_PURPLE, command=self.clear_log)
        self.clear_log_btn.pack(side="right")

        self.log_box = ctk.CTkTextbox(self.log_frame, height=90, fg_color="transparent", text_color=TEXT_MUTED, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.log_box.configure(state="disabled")
        
        # --- 6. FOOTER ---
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.footer_frame.pack(fill="x", side="bottom", pady=(0, 5))
        
        self.footer_label = ctk.CTkLabel(self.footer_frame, text="Developing for the future. Check our projects: ", font=("Poppins", 11), text_color=TEXT_MUTED)
        self.footer_label.pack(side="left", padx=(25, 0))
        
        self.footer_link = ctk.CTkLabel(self.footer_frame, text="Koleth Web", font=("Poppins", 11, "bold", "underline"), text_color=KOLETH_PURPLE, cursor="hand2")
        self.footer_link.pack(side="left")
        self.footer_link.bind("<Button-1>", lambda e: webbrowser.open("https://koleth.net.tr"))

        # Başlangıç Logları
        self.log("🚀 Powered by Koleth Ecosystem (rodyat.tech | koleth.net.tr)", color=KOLETH_PURPLE)
        self.log("Koleth Hook Master başlatıldı. Sisteme hoş geldin! ⚡", color=SUCCESS_GREEN)

    # --- FONKSİYONLAR ---

    def toggle_schedule(self):
        if self.schedule_switch.get():
            self.animate_height(self.schedule_container, 0, 50, 5)
        else:
            self.animate_height(self.schedule_container, 50, 0, -5)

    def animate_height(self, widget, current, target, step):
        current += step
        if (step > 0 and current <= target) or (step < 0 and current >= target):
            widget.configure(height=current)
            if current != target:
                self.after(15, self.animate_height, widget, current, target, step)

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_path = path
            self.file_label.configure(text=os.path.basename(path), text_color=SUCCESS_GREEN)

    def clear_file(self):
        self.file_path = None
        self.file_label.configure(text="Dosya seçilmedi", text_color=TEXT_MUTED)

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.log("🚀 Powered by Koleth Ecosystem (rodyat.tech | koleth.net.tr)", color=KOLETH_PURPLE)
        self.log("Terminal temizlendi. 🧹", color=SUCCESS_GREEN)

    def log(self, message, color=TEXT_MUTED):
        self.log_box.configure(state="normal")
        time_str = datetime.now().strftime("%H:%M:%S")
        
        tag_name = f"color_{color.replace('#', '')}"
        self.log_box.tag_config(tag_name, foreground=color)
        
        log_text = f"[{time_str}] {message}\n"
        
        start_index = self.log_box.index("end-1c")
        self.log_box.insert("end", log_text)
        end_index = self.log_box.index("end-1c")
        self.log_box.tag_add(tag_name, start_index, end_index)
        
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def send_webhook(self):
        url = self.webhook_url.get().strip()
        if not url:
            self.log("Hata: Webhook URL boş olamaz! Lütfen geçerli bir link girin. ❌", color=ERROR_RED)
            return

        payload = {}
        
        if self.mention_switch.get():
            payload["allowed_mentions"] = {"parse": ["everyone", "roles", "users"]}
        else:
            payload["allowed_mentions"] = {"parse": []}

        content = self.msg_content.get("1.0", "end-1c").strip()
        if content and content != "Normal mesaj içeriği (İsteğe bağlı)...":
            payload["content"] = content

        embed = {}
        title = self.embed_title.get().strip()
        if title: embed["title"] = title
        
        desc = self.embed_desc.get("1.0", "end-1c").strip()
        if desc and desc != "Açıklama (Description)...": embed["description"] = desc
        
        color_hex = self.embed_color.get().strip()
        if color_hex:
            try:
                embed["color"] = int(color_hex.lstrip('#'), 16)
            except ValueError:
                self.log("Uyarı: Geçersiz renk kodu (Hex). Renk yoksayıldı. ⚠️", color="#f59e0b")

        author_name = self.embed_author_name.get().strip()
        author_icon = self.embed_author_icon.get().strip()
        if author_name:
            embed["author"] = {"name": author_name}
            if author_icon: embed["author"]["icon_url"] = author_icon

        footer_text = self.embed_footer_text.get().strip()
        footer_icon = self.embed_footer_icon.get().strip()
        if footer_text:
            embed["footer"] = {"text": footer_text}
            if footer_icon: embed["footer"]["icon_url"] = footer_icon

        image_url = self.embed_image.get().strip()
        if image_url: embed["image"] = {"url": image_url}

        thumb_url = self.embed_thumb.get().strip()
        if thumb_url: embed["thumbnail"] = {"url": thumb_url}

        if embed:
            payload["embeds"] = [embed]

        if not payload.get("content") and not payload.get("embeds") and not self.file_path:
            payload["content"] = "Koleth Hook Master'dan selamlar! (Boş Mesaj)"

        if self.schedule_switch.get():
            time_str = self.schedule_time.get().strip()
            try:
                target_time = datetime.strptime(time_str, "%H:%M").time()
                now = datetime.now()
                target_dt = datetime.combine(now.date(), target_time)
                if target_dt <= now:
                    target_dt += timedelta(days=1)
                
                delay = (target_dt - now).total_seconds()
                self.log(f"Mesaj {time_str} saatine zamanlandı. Arka planda bekleniyor... ⏳", color="#f59e0b")
                
                threading.Thread(target=self._execute_send, args=(url, payload, self.file_path, delay), daemon=True).start()
                return
            except ValueError:
                self.log("Hata: Geçersiz saat formatı! Lütfen HH:MM şeklinde girin (Örn: 14:30). ❌", color=ERROR_RED)
                return

        self._execute_send(url, payload, self.file_path, 0)

    def _execute_send(self, url, payload, file_path, delay):
        if delay > 0:
            time.sleep(delay)
            self.log("Zamanlanan mesaj gönderiliyor... 🚀", color=TEXT_MUTED)

        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    response = requests.post(url, data={"payload_json": json.dumps(payload)}, files={"file": f})
            else:
                response = requests.post(url, json=payload)
            
            if response.status_code in [200, 204]:
                self.log("Mesaj Başarıyla Gönderildi! ✅", color=SUCCESS_GREEN)
            else:
                self.log(f"Hata: Discord API {response.status_code} döndürdü! ❌", color=ERROR_RED)
                self.log(f"Detay: {response.text}", color=ERROR_RED)
        except Exception as e:
            self.log(f"Hata: Bağlantı sorunu yaşandı! ❌", color=ERROR_RED)
            self.log(f"Detay: {str(e)}", color=ERROR_RED)

    # --- PROFİL YÖNETİMİ (JSON) ---

    def load_profiles(self):
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_profiles_to_file(self):
        try:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"Hata: Profiller kaydedilemedi! ({str(e)}) ❌", color=ERROR_RED)

    def update_profile_menu(self):
        profile_names = list(self.profiles.keys())
        if not profile_names:
            profile_names = ["Profil Bulunamadı"]
            self.profile_var.set("Profil Bulunamadı")
        else:
            if self.profile_var.get() not in profile_names:
                self.profile_var.set(profile_names[0])
                
        self.profile_menu.configure(values=profile_names)

    def save_profile(self):
        name = self.profile_name_entry.get().strip()
        if not name:
            self.log("Hata: Kaydetmek için bir profil adı girin! ❌", color=ERROR_RED)
            return

        profile_data = {
            "webhook_url": self.webhook_url.get().strip(),
            "msg_content": self.msg_content.get("1.0", "end-1c").strip(),
            "mentions": self.mention_switch.get(),
            "author_name": self.embed_author_name.get().strip(),
            "author_icon": self.embed_author_icon.get().strip(),
            "title": self.embed_title.get().strip(),
            "description": self.embed_desc.get("1.0", "end-1c").strip(),
            "color": self.embed_color.get().strip(),
            "image": self.embed_image.get().strip(),
            "thumbnail": self.embed_thumb.get().strip(),
            "footer_text": self.embed_footer_text.get().strip(),
            "footer_icon": self.embed_footer_icon.get().strip()
        }

        self.profiles[name] = profile_data
        self.save_profiles_to_file()
        self.update_profile_menu()
        self.profile_var.set(name)
        self.profile_name_entry.delete(0, "end")
        self.log(f"Profil '{name}' başarıyla kaydedildi! 💾", color=SUCCESS_GREEN)

    def load_profile(self):
        selected = self.profile_var.get()
        if selected not in self.profiles:
            self.log("Hata: Geçerli bir profil seçilmedi! ❌", color=ERROR_RED)
            return

        data = self.profiles[selected]

        self.webhook_url.delete(0, "end")
        self.webhook_url.insert(0, data.get("webhook_url", ""))

        self.msg_content.delete("1.0", "end")
        self.msg_content.insert("1.0", data.get("msg_content", ""))

        if data.get("mentions", False):
            self.mention_switch.select()
        else:
            self.mention_switch.deselect()

        self.embed_author_name.delete(0, "end")
        self.embed_author_name.insert(0, data.get("author_name", ""))

        self.embed_author_icon.delete(0, "end")
        self.embed_author_icon.insert(0, data.get("author_icon", ""))

        self.embed_title.delete(0, "end")
        self.embed_title.insert(0, data.get("title", ""))

        self.embed_desc.delete("1.0", "end")
        self.embed_desc.insert("1.0", data.get("description", ""))

        self.embed_color.delete(0, "end")
        self.embed_color.insert(0, data.get("color", ""))

        self.embed_image.delete(0, "end")
        self.embed_image.insert(0, data.get("image", ""))

        self.embed_thumb.delete(0, "end")
        self.embed_thumb.insert(0, data.get("thumbnail", ""))

        self.embed_footer_text.delete(0, "end")
        self.embed_footer_text.insert(0, data.get("footer_text", ""))

        self.embed_footer_icon.delete(0, "end")
        self.embed_footer_icon.insert(0, data.get("footer_icon", ""))

        self.log(f"Profil '{selected}' yüklendi! 📂", color=SUCCESS_GREEN)

    def delete_profile(self):
        selected = self.profile_var.get()
        if selected in self.profiles:
            del self.profiles[selected]
            self.save_profiles_to_file()
            self.update_profile_menu()
            self.log(f"Profil '{selected}' silindi! 🗑️", color=SUCCESS_GREEN)
        else:
            self.log("Hata: Silinecek geçerli bir profil seçilmedi! ❌", color=ERROR_RED)

if __name__ == "__main__":
    app = KolethWebhookMaster()
    app.mainloop()
