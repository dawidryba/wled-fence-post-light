"""Szerokości ścieżek zasilania płytki głównej wg IPC-2221 (warstwa zewnętrzna, 1 oz = 35 µm).

I = k · ΔT^0.44 · A^0.725, k = 0,048 (zewnętrzna), A w mil², ΔT w °C.
"""
K, MIL_MM = 0.048, 0.0254
T_MIL = 35e-3 / MIL_MM  # 1 oz


def width_mm(i, dt):
    area = (i / (K * dt ** 0.44)) ** (1 / 0.725)
    return area / T_MIL * MIL_MM


NETS = [  # sieć, prąd projektowy [A], uzasadnienie
    ("VIN/V12P/V12SW (tor łańcucha)", 10.0, "zasilacz 10 A; zwarcie na końcu łańcucha ~7,7 A"),
    ("VIN/V12P/V12SW (praca, ABL 35%)", 4.5, "6 lampek, notes.md"),
    ("V12LED", 2.0, "Mini560 poza regulacją, notes.md"),
    ("V5LED (wyjście U1)", 1.62, "40 × 40,5 mA"),
    ("V5LED (gałąź do 1 płytki LED)", 0.41, "10 × 40,5 mA"),
    ("V5ESP", 0.5, "szczyt ESP32 (niezweryfikowane)"),
    ("V12LOG", 0.3, "0,5 A × 5 V / 12 V / sprawność"),
]

if __name__ == "__main__":
    for name, i, why in NETS:
        print(f"{name:34} {i:5.2f} A  ΔT10: {width_mm(i, 10):5.2f} mm  ΔT20: {width_mm(i, 20):5.2f} mm   ({why})")
    assert 4.0 < width_mm(10, 20) < 5.5            # znany punkt: 10 A / 20 °C / 1 oz ≈ 4,7 mm
