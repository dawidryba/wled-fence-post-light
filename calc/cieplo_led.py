"""Szacunek temperatury płytki LED (PCB2) przy konwekcji naturalnej — rząd wielkości, nie symulacja.

ΔT = P / (h · A). Płytka 73,6 × 14,4 mm, obie strony; h = 5–10 W/m²K (zamknięta obudowa / swobodny przepływ).
Moc na płytkę: 10 diod × 5 V × 40,5 mA × ABL; ~75% mocy LED zamienia się w ciepło (założenie, niezweryfikowane).
"""
A = 2 * 73.6e-3 * 14.4e-3
for abl in (0.35, 0.6, 1.0):
    p = 10 * 5 * 0.0405 * abl * 0.75
    print(f"ABL {abl:.0%}: ciepło {p:.2f} W → ΔT {p / (10 * A):.0f}–{p / (5 * A):.0f} K ponad temperaturę w lampce")
