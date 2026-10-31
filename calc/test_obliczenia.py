"""Obliczeniowe sprawdzenie wytrzymałości elementów i zachowania zasilania (bez SPICE).

.venv/bin/python calc/test_obliczenia.py
Źródła: datasheety w datasheets/ (AOD4185, JW5068A, 1812L300, SKC6812), karty producentów MLCC/rezystorów (numery z schematu),
calc/spadek_cat5e.py (spadki), calc/sym/sym_spice.py (przebiegi). Wartości oznaczone (szac.) — szacunki do potwierdzenia pomiarem.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RESULTS = []

VIN_NOM, VIN_MAX = 12.0, 13.2          # zasilacz 12 V, +10% (regulacja potencjometrem)
V_TVS_CLAMP = 24.4                     # SMBJ15A Vc @ Ipp 24,6 A
V5_MAX = 5.2                           # wyjście Mini560 bez obciążenia (bringup: 5,0–5,2 V)
V5_FAULT = 9.2                         # SMBJ5.0A Vc @ 65,2 A (zwarcie klucza przetwornicy)


def report(test, status, msg):
    RESULTS.append((test, status, msg))
    print(f"[{status}] {test}: {msg}")


def test_napiecia_znamionowe():
    # (element, napięcie znamionowe, najgorsze napięcie pracy, najgorsze chwilowe, źródło)
    parts = [
        ("C1/C5 VZH 220 µF 35 V", 35, VIN_MAX, V_TVS_CLAMP, "Lelon VZH"),
        ("C2/C6/C11 CL31B106KAHNNNE 25 V", 25, VIN_MAX, V_TVS_CLAMP, "Samsung CL31B106KAHNNNE"),
        ("C3/C7/C12 CL31B104KBCNNNC 50 V", 50, VIN_MAX, V_TVS_CLAMP, "Samsung CL31B104KBCNNNC"),
        ("C8 VZH 470 µF 16 V", 16, V5_MAX, V5_FAULT, "Lelon VZH"),
        ("C9/C13 10 µF 25 V (szyna 5 V)", 25, V5_MAX, V5_FAULT, "Samsung"),
        ("PCB2 C11 CL21A106KAYNNNE 25 V", 25, V5_MAX, V5_FAULT, "Samsung"),
        ("PCB2 C1–C10 CC0603KRX7R9BB104 50 V", 50, V5_MAX, V5_FAULT, "Yageo"),
        ("Q1/Q2 AOD4185 VDS 40 V", 40, VIN_MAX, V_TVS_CLAMP, "datasheet AOD4185"),
        ("U1/U2 JW5068A VIN abs. max 28 V", 28, VIN_MAX, V_TVS_CLAMP, "datasheet JW5068A"),
        ("D1 SMBJ15A VRWM 15 V", 15, VIN_MAX, None, "karta SMBJ"),
        ("D4 SMBJ5.0A VRWM 5,0 V", 5.0, V5_MAX, None, "karta SMBJ"),
        ("F1 1812L300/30GR Vmax 30 V", 30, VIN_MAX, V_TVS_CLAMP, "datasheet 1812L300"),
        ("F2 JK-nSMD050-30 Vmax 30 V", 30, VIN_MAX, V_TVS_CLAMP, "karta JK-nSMD"),
    ]
    bad, warn, out = [], [], []
    for name, rated, work, peak, src in parts:
        if work > rated:
            (warn if work - rated <= 0.25 else bad).append(f"{name}: praca {work} V > {rated} V")
        elif peak and peak > rated:
            warn.append(f"{name}: chwilowo {peak} V > {rated} V")
        elif work > 0.8 * rated and not name.startswith(("D1", "D4")):     # TVS dobiera się z VRWM tuż nad napięciem pracy
            warn.append(f"{name}: praca {work} V = {work / rated:.0%} znamionowego")
        else:
            out.append(name)
    report("napięcia znamionowe elementów", "FAIL" if bad else ("WARN" if warn else "PASS"),
           "; ".join(bad + warn) + f" | z zapasem: {', '.join(out)}")


def test_moce_rezystorow():
    p = {  # rezystor 1206 = 0,25 W (Uniroyal 1206W4F / Yageo RC1206)
        "R10/R11 2,2 k przy 13,2 V": VIN_MAX ** 2 / 2200,
        "R10 2,2 k przy zacisku TVS 24,4 V (chwilowo)": V_TVS_CLAMP ** 2 / 2200,
        "R1/R2 47 k (Vgs 12 V)": 12 ** 2 / 47e3,
        "R3 4,7 k (ZD2 przewodzi przy 13,2 V)": (VIN_MAX - 12) ** 2 / 4700,
        "R7 220 Ω przy pomyłce +12 V na DANE (D2 ~7 V)": (12 - 7) ** 2 / 220,
    }
    bad = {k: v for k, v in p.items() if v > 0.25 and "chwilowo" not in k}
    report("moce rezystorów 1206 (0,25 W)", "FAIL" if bad else "PASS", ", ".join(f"{k}: {v * 1e3:.0f} mW" for k, v in p.items()))


def test_bezpieczniki_ptc():
    p_lamp = 40 * 0.0405 * 5 / 0.88                     # 9,2 W — 100% bez ABL
    i_f1 = p_lamp / 8.0                                  # najniższe napięcie regulacji JW5068A
    hold_f1_70 = 1.61                                    # datasheet 1812L300: hold 3,00 A @25 °C, 1,61 A @70 °C (schemat.md)
    i_f2 = 1.2 / 0.85 / 8.0                              # ESP32 z Wi-Fi średnio ~240 mA @5 V (szac.); piki TX trwają ms — PTC reaguje na średnią
    hold_f2_25 = 0.5
    hold_f2_70 = hold_f2_25 * 0.62                       # typowe obniżenie dla PTC 1206 przy 70 °C (szac., brak karty JK w datasheets/)
    st = "PASS" if i_f1 < 0.8 * hold_f1_70 else "WARN"
    report("F1 (tor LED) — prąd trzymania w 70 °C", st, f"lampka 100% przy VIN 8 V: {i_f1:.2f} A vs hold @70 °C {hold_f1_70} A ({i_f1 / hold_f1_70:.0%})")
    report("F2 (ESP) — prąd trzymania w 70 °C", "PASS" if i_f2 < 0.8 * hold_f2_70 else "WARN",
           f"ESP średnio przy VIN 8 V: {i_f2:.2f} A vs hold @70 °C ≈ {hold_f2_70:.2f} A (szac.) — obniżenie z temperaturą NIEZWERYFIKOWANE (brak karty JK-nSMD050)")


def test_spadki_i_abl():
    import io
    import contextlib
    import spadek_cat5e as s
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        s.main() if hasattr(s, "main") else exec(open(os.path.join(HERE, "spadek_cat5e.py")).read(), {"__name__": "__main__"})
    txt = buf.getvalue()
    line = next(l for l in txt.splitlines() if l.startswith("Bezpieczny ABL"))
    report("spadki napięcia w łańcuchu 6 lampek (calc/spadek_cat5e.py)", "WARN",
           f"{line.strip()} — WLED musi mieć ograniczenie prądu (bringup.md: max current 3600 mA); bez ABL SPICE: ostatnia lampka 7,0 V")


def test_zatrzask_uvp():
    """JW5068A: UVP wyjścia (FB < 65%) → zatrzask; restart dopiero po spadku VIN < UVLO 3 V. Czas rozładowania C5+C6+wejście modułu przez R10."""
    c = 220e-6 + 10e-6 + 22e-6                           # C5 + C6 + kondensatory modułu (szac. 22 µF)
    v_start = 6.0                                        # przetwornica przestaje obciążać wejście mniej więcej przy utracie regulacji (szac.)
    t = 2200 * c * math.log(v_start / 3.0)
    report("zatrzask UVP po wyłączeniu przez WLED", "WARN",
           f"V12LED spada z ~{v_start:.0f} V do UVLO 3 V w ≈ {t:.2f} s (R10 2,2 k × {c * 1e6:.0f} µF) — ponowne włączenie relay szybciej niż ~0,5 s "
           "może zostawić diody zgaszone do następnego cyklu; test w bringup.md p. 4 (wyłącz/włącz po 0,5 / 2 / 5 s). Zachowanie zatrzasku wg datasheetu, niezmierzone.")


def test_straty_q1():
    for i, label in ((6.5, "6 lampek 100% bez ABL (SPICE)"), (2.9, "6 lampek przy ABL 35%")):
        rds_hot = 0.019                                  # AOD4185 Rds(on) @ -10 V, Tj 125 °C typ. (datasheet)
        p = i ** 2 * rds_hot
        dt = p * 50                                      # RθJA 50 K/W (1 in² 2 oz, datasheet) — nasza płytka 1 oz, ale duże pola VIN/V12P
        report(f"Q1 straty — {label}", "PASS" if 60 + dt < 125 else "WARN", f"{i} A → {p:.2f} W, ΔT ≈ {dt:.0f} K (przy 60 °C w obudowie → {60 + dt:.0f} °C)")


def test_d4_uplyw():
    report("D4 SMBJ5.0A na szynie 5 V", "PASS",
           f"praca ≤ {V5_MAX} V, VBR min 6,4 V @ 10 mA → upływ ≪ 10 mA (≤ 0,8 mA @ 5,0 V wg karty); przy 12 V na szynie 5 V zwiera → F1 (trip 5 A) zadziała, "
           "U4 i diody mogą jednak zobaczyć do ~9 V przez czas zadziałania PTC (sekundy) — ochrona częściowa")


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    print(f"\n{len(RESULTS)} testów: {sum(r[1] == 'PASS' for r in RESULTS)} PASS, {sum(r[1] == 'WARN' for r in RESULTS)} WARN, {len(fails)} FAIL")
    sys.exit(1 if fails else 0)
