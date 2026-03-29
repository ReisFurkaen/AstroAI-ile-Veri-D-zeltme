import os
import customtkinter as ctk
import pandas as pd
import threading
import subprocess
import json
import time  # 🚀 YENİ: Süre hesaplamak için eklendi
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# =====================================================================
# TEMEL GÖRSEL AYARLAR
# =====================================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TUAGroundStationGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.geometry("1300x850")
        self.root.minsize(1000, 750)
        self.root.title("TUA Astro Hackathon - Telemetri Kontrol İstasyonu v2.0")

        self.settings_path = os.path.join(os.path.dirname(__file__), "tua_settings.json")

        self.baslik_font = ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
        self.kod_font = ctk.CTkFont(family="Consolas", size=13)
        self.normal_font = ctk.CTkFont(family="Segoe UI", size=14)

        self.settings = {
            "appearance_mode": ctk.StringVar(value="dark"),
            "window_opacity": ctk.DoubleVar(value=1.0),
            "kirli_csv": ctk.StringVar(value="tua_telemetri.csv"),
            "temiz_csv": ctk.StringVar(value="temiz_tua_telemetri.csv")
        }
        self._load_settings_from_file()

        self.sensorler = [
            ("Irtifa_m", "İrtifa (Metre)", "🏔"), ("Hiz_ms", "Hız (m/s)", "🚀"),
            ("Ivme_G", "İvme (G)", "☄️"), ("Basinc_hPa", "Atmosferik Basınç", "🌪"),
            ("Dis_Sicaklik_C", "Dış Sıcaklık", "❄️"), ("Ic_Sicaklik_C", "İç Sıcaklık", "🔥"),
            ("Batarya_Yuzde", "Batarya (%)", "🔋"), ("Pitch_deg", "Jiroskop - Pitch", "📐"),
            ("Roll_deg", "Jiroskop - Roll", "🔄"), ("Yaw_deg", "Jiroskop - Yaw", "🧭"),
            ("GPS_Enlem", "GPS Enlem", "📍"), ("GPS_Boylam", "GPS Boylam", "📍"),
            ("Sinyal_dBm", "İletişim Sinyali", "📡"), ("Radyasyon_uSvh", "Kozmik Radyasyon", "☢️")
        ]

        self.pages = {}
        self.nav_buttons = {}

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_container()

        self.select_page("dashboard")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        self._save_settings_to_file()
        self.root.quit()
        self.root.destroy()
        os._exit(0)

    def _load_settings_from_file(self):
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    for key, value in saved_data.items():
                        if key in self.settings: self.settings[key].set(value)
                ctk.set_appearance_mode(self.settings["appearance_mode"].get())
                self.root.attributes("-alpha", self.settings["window_opacity"].get())
            except:
                pass

    def _save_settings_to_file(self):
        try:
            data_to_save = {k: v.get() for k, v in self.settings.items()}
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4)
        except:
            pass

    def show_toast(self, message, is_error=False):
        color = "#d9534f" if is_error else "#2a7fff"
        toast = ctk.CTkLabel(self.root, text=message, corner_radius=20, fg_color=color, text_color="white",
                             font=("Segoe UI", 12, "bold"), height=40, padx=20)
        toast.place(relx=0.5, rely=0.9, anchor="center")
        self.root.after(3000, toast.destroy)

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkScrollableFrame(self.root, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar_frame, text="Veri Düzeltme", font=self.baslik_font).pack(pady=(30, 20))
        self._create_nav_item("📊 Kontrol Merkezi", "dashboard")
        self._create_nav_item("⚙️ Ayarlar", "settings")
        ctk.CTkLabel(self.sidebar_frame, text="TELEMETRİ GRAFİKLERİ", font=("Segoe UI", 12, "bold"),
                     text_color="gray").pack(pady=(25, 5), anchor="w", padx=20)
        for s_id, isim, ikon in self.sensorler:
            self._create_nav_item(f"{ikon} {isim}", s_id)

    def _create_nav_item(self, text, page_name):
        group = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        group.pack(fill="x", padx=10, pady=3)
        ind = ctk.CTkFrame(group, width=4, height=30, corner_radius=10, fg_color="transparent")
        ind.pack(side="left", padx=(0, 5))
        btn = ctk.CTkButton(group, text=text, anchor="w", height=40, corner_radius=20,
                            fg_color="transparent", text_color=("#000000", "#ffffff"),
                            hover_color=("#c8c8c8", "#444444"), font=self.normal_font,
                            command=lambda: self.select_page(page_name))
        btn.pack(side="left", fill="x", expand=True)
        self.nav_buttons[page_name] = (btn, ind)

    def select_page(self, page_name):
        for name, (btn, ind) in self.nav_buttons.items():
            if name == page_name:
                ind.configure(fg_color="#2a7fff")
                btn.configure(fg_color=("#c8c8c8", "#3a3a3a"), text_color="#2a7fff", font=("Segoe UI", 14, "bold"))
            else:
                ind.configure(fg_color="transparent")
                btn.configure(fg_color="transparent", text_color=("#000000", "#ffffff"), font=self.normal_font)

        for name, frame in self.pages.items():
            if name == page_name:
                frame.pack(fill="both", expand=True)
                if name not in ["dashboard", "settings"] and len(frame.winfo_children()) == 1:
                    self._draw_sensor_graph(name, frame)
            else:
                frame.pack_forget()

    def _build_main_container(self):
        self.main_content = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.pages["dashboard"] = self._create_dashboard_page()
        self.pages["settings"] = self._create_settings_page()
        for s_id, isim, ikon in self.sensorler:
            frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
            ctk.CTkLabel(frame, text=f"{ikon} {isim} Analizi", font=self.baslik_font).pack(pady=(0, 10), anchor="w",
                                                                                           padx=10)
            self.pages[s_id] = frame

    def _create_dashboard_page(self):
        frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        ctk.CTkLabel(frame, text="Sistem Kontrol Merkezi", font=self.baslik_font).pack(pady=(0, 20), anchor="w",
                                                                                       padx=10)
        info_box = ctk.CTkFrame(frame, corner_radius=15, border_width=1, border_color=("#d1d1d1", "#3d3d3d"))
        info_box.pack(fill="x", pady=10, padx=5)
        info_txt = ctk.CTkTextbox(info_box, height=100, fg_color="transparent", font=self.normal_font, wrap="word")
        info_txt.insert("1.0",
                        "Başmühendis Paneli:\n1. Dosyaları temizleyerek çakışmaları önleyin.\n2. Kozmik simülasyonu başlatarak radyasyonlu verileri üretin.\n3. Pipeline motorunu çalıştırarak verileri filtreleyin.")
        info_txt.configure(state="disabled")
        info_txt.pack(fill="x", padx=15, pady=10)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=25, padx=5)

        self.btn_temizle_dosya = ctk.CTkButton(btn_frame, text="🗑️ Verileri\nSıfırla", height=70, corner_radius=20,
                                               command=self._clear_csv_files)
        self.btn_temizle_dosya.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_uret = ctk.CTkButton(btn_frame, text="☢️ 1. Simülasyon\nAteşle", height=70, corner_radius=20,
                                      fg_color="#d9534f", command=self._run_veri_uretici)
        self.btn_uret.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_temizle_pipe = ctk.CTkButton(btn_frame, text="✨ 2. Onarımı\nBaşlat", height=70, corner_radius=20,
                                              fg_color="#28a745", command=self._run_veri_temizleyici)
        self.btn_temizle_pipe.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_yenile = ctk.CTkButton(btn_frame, text="🔄 Sistemi\nYenile", height=70, corner_radius=20,
                                        fg_color="#007bff", hover_color="#0056b3", command=self._refresh_system)
        self.btn_yenile.pack(side="left", fill="x", expand=True, padx=(5, 0))

        self.log_console = ctk.CTkTextbox(frame, height=350, corner_radius=15, font=self.kod_font, fg_color="#1e1e1e",
                                          text_color="#00ff00")
        self.log_console.pack(fill="both", expand=True, padx=5, pady=20)
        self._write_log("Yer İstasyonu v2.0 başlatıldı. Tüm sistemler normal.")
        return frame

    def _create_settings_page(self):
        frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        ctk.CTkLabel(frame, text="Sistem Yapılandırması", font=self.baslik_font).pack(pady=(0, 20), anchor="w", padx=10)
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self._add_setting_header(scroll, "🎨 Görünüm")
        self.tema_switch = ctk.CTkSwitch(scroll, text="Koyu Mod", command=self._tema_degistir)
        if ctk.get_appearance_mode() == "Dark": self.tema_switch.select()
        self.tema_switch.pack(anchor="w", padx=20, pady=10)

        self._add_setting_header(scroll, "📁 Dosya Yolları")
        self._add_setting_input(scroll, "Ham Veri CSV:", self.settings["kirli_csv"])
        self._add_setting_input(scroll, "Temizlenmiş Veri CSV:", self.settings["temiz_csv"])
        return frame

    def _add_setting_header(self, master, text):
        ctk.CTkLabel(master, text=text, font=("Segoe UI", 16, "bold"), text_color="#2a7fff").pack(anchor="w",
                                                                                                  pady=(20, 10),
                                                                                                  padx=10)

    def _add_setting_label(self, master, text):
        ctk.CTkLabel(master, text=text, font=self.normal_font).pack(anchor="w", padx=20)

    def _add_setting_input(self, master, label_text, variable):
        self._add_setting_label(master, label_text)
        ctk.CTkEntry(master, textvariable=variable, font=self.kod_font, width=400).pack(anchor="w", padx=20, pady=5)

    def _tema_degistir(self):
        mode = "dark" if self.tema_switch.get() == 1 else "light"
        ctk.set_appearance_mode(mode)
        self.settings["appearance_mode"].set(mode)

    def _clear_csv_files(self):
        k, t = self.settings["kirli_csv"].get(), self.settings["temiz_csv"].get()
        deleted = False
        for f in [k, t]:
            if os.path.exists(f):
                os.remove(f)
                deleted = True
                self._write_log(f"SİLİNDİ: {f} dosyası temizlendi.")

        if not deleted:
            self._write_log("BİLGİ: Silinecek veri dosyası bulunamadı.")

        self.show_toast("✓ Veriler Sıfırlandı.")

    def _refresh_system(self):
        self._write_log("SİSTEM: Önbellek temizleme komutu alındı...")
        start_time = time.time()
        for s_id, isim, ikon in self.sensorler:
            frame = self.pages[s_id]
            for widget in frame.winfo_children()[1:]:
                widget.destroy()

        elapsed = (time.time() - start_time) * 1000  # ms cinsinden
        self._write_log(f"SİSTEM: Grafikler ve önbellek sıfırlandı. Süre: {elapsed:.2f} ms")
        self.show_toast("✓ Sistem Yenilendi")

    def _run_veri_uretici(self):
        self.btn_uret.configure(state="disabled")
        self._write_log("\n--- SİMÜLASYON BAŞLATILIYOR ---")
        self._write_log("İşlem: Radyasyonlu veri seti üretimi...")
        threading.Thread(target=self._execute_script, args=("veri_uretici.py", "Üretim", "tua_telemetri.csv"),
                         daemon=True).start()

    def _run_veri_temizleyici(self):
        self.btn_temizle_pipe.configure(state="disabled")
        self._write_log("\n--- ONARIM MOTORU BAŞLATILIYOR ---")
        self._write_log("İşlem: AI tabanlı telemetri veri düzeltmesi...")
        threading.Thread(target=self._execute_script, args=("veri_temizleyici.py", "Onarım", "temiz_tua_telemetri.csv"),
                         daemon=True).start()

    def _execute_script(self, script_name, process_type, target_file):
        import sys
        python_exe = sys.executable
        start_time = time.time()

        try:
            self.root.after(0, lambda: self._write_log(
                f"ÇALIŞTIRILIYOR: {script_name} dosyası Python üzerinden tetiklendi."))
            res = subprocess.run([python_exe, script_name], capture_output=True, text=True, encoding='utf-8')

            elapsed_time = time.time() - start_time

            if res.returncode == 0:
                self.root.after(0, lambda: self._write_log(
                    f"BAŞARILI: {process_type} tamamlandı. ({elapsed_time:.2f} saniye)"))

                if res.stdout:
                    for line in res.stdout.split('\n'):
                        if "⭐" in line or "🔬" in line or "[ONAY]" in line:
                            # Lambda içinde l=line yaparak o anki döngü değerini hapsediyoruz
                            self.root.after(0, lambda l=line.strip(): self._write_log(l))

                if os.path.exists(target_file):
                    try:
                        df = pd.read_csv(target_file)
                        row_count = len(df)
                        speed = row_count / elapsed_time if elapsed_time > 0 else 0
                        self.root.after(0, lambda: self._write_log(
                            f"İSTATİSTİK: Toplam {row_count} paket işlendi. Hız: {speed:.1f} satır/saniye"))
                    except:
                        pass

                self.root.after(0, lambda: self.show_toast(f"✓ {process_type} Bitti"))
            else:
                self.root.after(0, lambda: self._write_log(f"HATA ALINDI ({script_name}):\n{res.stderr}"))
                self.root.after(0, lambda: self.show_toast(f"✗ HATA!", is_error=True))

        except Exception as e:
            self.root.after(0, lambda: self._write_log(f"SİSTEM ÇÖKMESİ: {e}"))
        finally:
            self.root.after(0, lambda: self.btn_uret.configure(state="normal"))
            self.root.after(0, lambda: self.btn_temizle_pipe.configure(state="normal"))
            self.root.after(0, lambda: self._write_log("SİSTEM: Beklemeye geçildi.\n"))

    def _write_log(self, text):
        self.log_console.configure(state="normal")
        # Saat bilgisi ile log yazdırma
        current_time = time.strftime("%H:%M:%S")
        self.log_console.insert("end", f"[{current_time}] {text}\n")
        self.log_console.see("end")
        self.log_console.configure(state="disabled")

    def _draw_sensor_graph(self, s_id, parent_frame):
        temiz_csv_p = self.settings["temiz_csv"].get()
        kirli_csv_p = self.settings["kirli_csv"].get()

        df_kirli = None
        df_temiz = None

        if not os.path.exists(kirli_csv_p):
            ctk.CTkLabel(parent_frame, text="⚠ Ham veri dosyası yok. Önce 1. Simülasyonu Ateşleyin.",
                         font=self.normal_font, text_color="#d9534f").pack(pady=100)
            return

        try:
            # 📂 1. İki dosyayı ayrı ayrı okuyoruz
            df_kirli = pd.read_csv(kirli_csv_p)
            if df_kirli.empty:
                raise ValueError("Ham veri dosyası tamamen boş!")

            if os.path.exists(temiz_csv_p):
                df_temiz = pd.read_csv(temiz_csv_p)

            # Zaman eksenini her zaman orijinal kirli veriden al
            if "Zaman_s" in df_kirli.columns:
                zaman = df_kirli["Zaman_s"]
            elif "Zaman" in df_kirli.columns:
                zaman = df_kirli["Zaman"]
            else:
                zaman = pd.Series(range(len(df_kirli)))

            mode = ctk.get_appearance_mode()

            fig, ax = plt.subplots(figsize=(10, 5), facecolor='#2b2b2b' if mode == "Dark" else '#f0f0f0')
            ax.set_facecolor('#1e1e1e' if mode == "Dark" else '#ffffff')

            ax.text(0.5, 0.5, 'Manje Tech', transform=ax.transAxes,
                    fontsize=90, color='gray', alpha=0.10,
                    ha='center', va='center', rotation=0, zorder=0)

            # 🚀 2. "Temiz_" ön ekini attık, direkt s_id ile arıyoruz
            has_dirty = s_id in df_kirli.columns
            has_clean = df_temiz is not None and s_id in df_temiz.columns

            min_y, max_y = float('inf'), float('-inf')

            # Min ve Max sınırlarını iki dosyayı da hesaplayarak buluyoruz
            if has_dirty:
                valid_dirty = df_kirli[s_id].dropna()
                if len(valid_dirty) > 0:
                    min_y = min(min_y, valid_dirty.min())
                    max_y = max(max_y, valid_dirty.max())
            if has_clean:
                valid_clean = df_temiz[s_id].dropna()
                if len(valid_clean) > 0:
                    min_y = min(min_y, valid_clean.min())
                    max_y = max(max_y, valid_clean.max())

            if pd.isna(min_y) or pd.isna(max_y) or min_y == float('inf') or max_y == float('-inf'):
                min_y, max_y = 0, 100

            if min_y == max_y:
                min_y -= 10
                max_y += 10

            padding = (max_y - min_y) * 0.1
            if padding == 0: padding = 10

            x_min, x_max = zaman.min(), zaman.max()
            if pd.isna(x_min) or pd.isna(x_max) or x_min == x_max:
                x_min, x_max = 0, max(1, len(zaman))

            ax.set_xlim(x_min, x_max)
            ax.set_ylim(min_y - padding, max_y + padding)

            line_dirty, = ax.plot([], [], color='#ff4d4d', label='Ham Veri (Kirli)',
                                  alpha=0.7) if has_dirty else (None,)
            line_clean, = ax.plot([], [], color='#00cc44', label='AstroAI (Temiz)', linewidth=2) if has_clean else (
                None,)

            col = 'white' if mode == "Dark" else 'black'
            ax.set_title(f"{s_id} Analizi", color=col)
            ax.set_xlabel("Zaman", color=col)
            ax.set_ylabel("Değer", color=col)
            ax.tick_params(colors=col)
            ax.legend()
            ax.grid(True, alpha=0.2)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=parent_frame)
            canvas.draw()

            total_points = len(zaman)
            total_frames = 120

            def update(frame):
                # 🌿 İVMELENDİRİCİ MATEMATİK
                t = frame / total_frames if total_frames > 0 else 1
                if t < 0.5:
                    progress = 2 * t * t
                else:
                    progress = -1 + (4 - 2 * t) * t

                idx = int(progress * total_points)
                if idx == 0: idx = 1

                lines = []
                # 🚀 3. Çizim sırasında kirli_df ve temiz_df'den ayrı ayrı verileri çekiyoruz
                if has_dirty:
                    line_dirty.set_data(zaman[:idx], df_kirli[s_id][:idx])
                    lines.append(line_dirty)
                if has_clean:
                    line_clean.set_data(zaman[:idx], df_temiz[s_id][:idx])
                    lines.append(line_clean)
                return lines

            canvas.anim = animation.FuncAnimation(
                fig, update, frames=total_frames + 1, interval=5, blit=False, repeat=False
            )

            toolbar_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
            toolbar_frame.pack(fill="x", side="bottom", padx=10, pady=5)

            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()

            toolbar.configure(background="#2b2b2b" if mode == "Dark" else "#f0f0f0")
            for button in toolbar.children.values():
                button.configure(background="#2b2b2b" if mode == "Dark" else "#f0f0f0")

            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        except Exception as e:
            ctk.CTkLabel(parent_frame, text=f"Grafik Çizim Hatası: {e}", text_color="red").pack(pady=50)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    os.environ['TK_SILENCE_DEPRECATION'] = '1'
    TUAGroundStationGUI().run()