import pandas as pd
import numpy as np
import random


def kozmik_felaket_simulasyonu(saniye=3600, dosya_adi="tua_telemetri.csv"):
    print(f"🚀 TUA 1 Saatlik 'Yörünge & Radyasyon' Simülasyonu Başlatılıyor... ({saniye} saniye)")

    zaman = np.arange(0, saniye, 1)

    irtifa_ham = np.interp(zaman, [0, 600, 3600], [0, 400000, 400000])
    irtifa_ham[600:] += np.cos(zaman[600:] * 0.01) * 20
    irtifa_ham += np.random.normal(0, 2.0, saniye)

    hiz_ham = np.interp(zaman, [0, 600, 3600], [0, 7660, 7660])
    hiz_ham[600:] += np.sin(zaman[600:] * 0.05) * 5
    hiz_ham += np.random.normal(0, 0.5, saniye)

    basinc_ham = 1013.25 * np.exp(-irtifa_ham / 8400)
    basinc_ham += np.random.normal(0, 0.2, saniye)
    basinc_ham = np.maximum(basinc_ham, 0.0)

    dis_sicaklik_ham = np.interp(irtifa_ham, [0, 100000, 400000], [15, -70, -100])
    dis_sicaklik_ham[600:] = -50 + 80 * np.sin(zaman[600:] * 0.005)
    dis_sicaklik_ham += np.random.normal(0, 0.3, saniye)
    ic_sicaklik_ham = 20.0 + np.random.normal(0, 0.2, saniye)

    batarya_ham = np.linspace(100.0, 40.0, saniye)
    batarya_ham += np.random.normal(0, 0.05, saniye)

    pitch_ham = np.interp(zaman, [0, 100, 600, 3600], [90, 70, 0, 0]) + np.random.normal(0, 0.1, saniye)
    roll_ham = np.random.normal(0, 0.1, saniye)
    yaw_ham = np.random.normal(0, 0.1, saniye)

    gps_enlem_ham = np.linspace(36.0, 45.0, saniye)
    gps_enlem_ham += np.random.normal(0, 0.0001, saniye)
    gps_boylam_ham = np.linspace(34.0, 60.0, saniye)
    gps_boylam_ham += np.random.normal(0, 0.0001, saniye)

    sinyal_ham = np.interp(zaman, [0, 600, 3600], [-40, -95, -95]) + np.random.normal(0, 0.5, saniye)
    ivme_ham = np.where(zaman <= 600, 3.2, 0.0) + np.random.normal(0, 0.02, saniye)

    data = {
        "Zaman_s": zaman, "Irtifa_m": irtifa_ham, "Hiz_ms": hiz_ham, "Ivme_G": ivme_ham,
        "Dis_Sicaklik_C": dis_sicaklik_ham, "Ic_Sicaklik_C": ic_sicaklik_ham,
        "Basinc_hPa": basinc_ham, "Batarya_Yuzde": batarya_ham,
        "Pitch_deg": pitch_ham, "Roll_deg": roll_ham, "Yaw_deg": yaw_ham,
        "GPS_Enlem": gps_enlem_ham, "GPS_Boylam": gps_boylam_ham,
        "Sinyal_dBm": sinyal_ham
    }

    radyasyon = np.ones(saniye) * 0.2

    # =================================================================
    # 2. KOZMİK FELAKETLER (Senkronize ve Gerçekçi Bozma)
    # =================================================================

    # A) DEVASA RADYASYON FIRTINASI (Rastgele Zaman ve Uzunluk)
    firtina_uzunluk = random.randint(100, 500)
    firtina_bas = random.randint(750, saniye - firtina_uzunluk - 100)
    firtina_bit = firtina_bas + firtina_uzunluk
    radyasyon[firtina_bas:firtina_bit] = np.random.normal(1500, 300, firtina_uzunluk)
    print(f"☢️ UYARI: {firtina_bas}-{firtina_bit} saniyeleri arası GÜNEŞ FIRTINASI simüle ediliyor!")

    # Fırtınanın TÜM sensörleri (eksikler dahil) aynı anda etkilemesi:
    data["Irtifa_m"][firtina_bas:firtina_bit] += np.random.normal(0, 15000, firtina_uzunluk)
    data["Hiz_ms"][firtina_bas:firtina_bit] += np.random.normal(0, 800, firtina_uzunluk)
    data["Pitch_deg"][firtina_bas:firtina_bit] += np.random.normal(0, 60, firtina_uzunluk)
    data["Roll_deg"][firtina_bas:firtina_bit] += np.random.normal(0, 60, firtina_uzunluk)
    data["Yaw_deg"][firtina_bas:firtina_bit] += np.random.normal(0, 60, firtina_uzunluk)
    data["GPS_Enlem"][firtina_bas:firtina_bit] += np.random.normal(0, 2.5, firtina_uzunluk)
    data["GPS_Boylam"][firtina_bas:firtina_bit] += np.random.normal(0, 2.5, firtina_uzunluk)
    data["Sinyal_dBm"][firtina_bas:firtina_bit] += np.random.normal(0, 30, firtina_uzunluk)
    data["Basinc_hPa"][firtina_bas:firtina_bit] += np.random.normal(0, 200, firtina_uzunluk)
    data["Ivme_G"][firtina_bas:firtina_bit] += np.random.normal(0, 2.0, firtina_uzunluk)
    data["Dis_Sicaklik_C"][firtina_bas:firtina_bit] += np.random.normal(0, 40.0, firtina_uzunluk)
    data["Ic_Sicaklik_C"][firtina_bas:firtina_bit] += np.random.normal(0, 15.0, firtina_uzunluk)
    data["Batarya_Yuzde"][firtina_bas:firtina_bit] += np.random.normal(0, 5.0, firtina_uzunluk)

    # B) ANLIK BİT DÖNMELERİ (Bit-Flips / Bireysel Atmalar)
    sensor_listesi = list(data.keys())
    sensor_listesi.remove("Zaman_s")

    for sensor in sensor_listesi:
        # 🚀 KRİTİK DEĞİŞİKLİK: Her sensör kendi payına düşen rastgele atma (3-20) sayısını alır
        atma_sayisi = random.randint(3, 20)
        for _ in range(atma_sayisi):
            idx = random.randint(0, saniye - 1)

            # Karakteristik bozulmalar
            if sensor == "Irtifa_m":
                data[sensor][idx] = random.choice([-999999, 1000000])
            elif sensor == "Hiz_ms":
                data[sensor][idx] = -50000
            elif "deg" in sensor:
                data[sensor][idx] = 999.9
            elif "GPS" in sensor:
                data[sensor][idx] = 0.0
            elif sensor == "Sinyal_dBm":
                data[sensor][idx] = 0.0
            else:
                data[sensor][idx] = 9999.0

    # C) SİNYAL KOPMALARI (NaN - Boş Veri)
    kopma_sayisi = random.randint(5, 12)
    for _ in range(kopma_sayisi):
        idx = random.randint(100, saniye - 100)
        sure = random.randint(5, 30)

        # 🚀 KRİTİK DEĞİŞİKLİK: Kopma anında TÜM sensörler veri göndermeyi aynı anda keser
        for sensor in sensor_listesi:
            data[sensor][idx: idx + sure] = np.nan

    # Radyasyonu sözlüğe ekle
    data["Radyasyon_uSvh"] = radyasyon

    # =================================================================
    # 3. KAYIT AŞAMASI
    # =================================================================
    print("💾 Veriler CSV formatına dökülüyor...")
    df = pd.DataFrame(data)
    df.to_csv(dosya_adi, index=False)
    print(f"🔥 TAMAMLANDI: '{dosya_adi}' oluşturuldu (Boyut: {saniye} satır).")


if __name__ == "__main__":
    kozmik_felaket_simulasyonu()