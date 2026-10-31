"""Spadek napięcia 12 V w łańcuchu 6 lampek na Cat5e i bezpieczny limit ABL w WLED (wersja 2).

Model (poprawki po niezależnej weryfikacji 2026-09-16):
- przewody: 3 żyły +12 V, 4 żyły GND, miedź 24 AWG 0,0842 Ω/m @20 °C, +8% na 40 °C,
- odcinki SEG_M między lampkami, zasilacz przy lampce 1 (LEAD_M),
- każda lampka dokłada R_BOARD w torze przelotowym (Q1, Q2 albo drut na padach Q2, 2 złącza, ścieżki),
- obciążenie: przetwornica = stała moc P_out/ETA,
- LED: N_LED × SKC6812RGBW, max 40,5 mA @ 5 V (datasheet); ESP ~1 W w lampce 1,
- WLED liczy prąd RGBW jako 1/4 na kanał, a realnie W = 16,5/40,5 → rzeczywista moc do WLED_ERR × szacunek,
- kryterium: JW5068A (Mini560 PRO) wymaga Vout ≤ VIN − 3 V → VIN ≥ 8 V dla 5 V (datasheet rev 0.31, s. 2).
"""
V_PSU, ETA, SEG_M, LEAD_M = 12.0, 0.88, 5.0, 0.5
R_CU = 0.0842 * 1.08
WIRES_PLUS, WIRES_GND = 3, 4
R_BOARD = 0.050
N_LED = 40                             # 4 płytki × 10 diod (wersja jednorzędowa)
P_LED_MAX = N_LED * 0.0405 * 5.0       # 8,1 W
WLED_ERR = 27.7 / (40.5 * 0.60)        # 60% wg WLED → do 27,7 mA/LED realnie (weryfikator)
VIN_MIN_REG = 8.0                      # datasheet JW5068A: Vout ≤ VIN − 3 V
VIN_MIN_PRACTICAL = 7.0                # orientacyjnie; fizycznie JW5068A reguluje od ~5,5–6 V (Dmax ~95%), abs. max wejścia 28 V
N = 6


def r_loop(length_m):
    return length_m * R_CU / WIRES_PLUS + length_m * R_CU / WIRES_GND


def backward(v_last, p_in):
    """Napięcie ostatniej lampki -> (wymagane napięcie zasilacza, napięcia lampek)."""
    v = [0.0] * len(p_in)
    v[-1], i_down = v_last, 0.0
    for k in range(len(p_in) - 1, -1, -1):
        if k < len(p_in) - 1:
            v[k] = v[k + 1] + i_down * (r_loop(SEG_M) + R_BOARD)
        i_down += p_in[k] / v[k]
    return v[0] + i_down * (r_loop(LEAD_M) + R_BOARD), v, i_down


def solve(fractions):
    """fractions[k] = rzeczywisty ułamek mocy maks. lampki k. Zwraca (napięcia, prąd) albo (None, None) = zapaść."""
    p_in = [P_LED_MAX * f / ETA + (1.0 if k == 0 else 0.0) for k, f in enumerate(fractions)]
    v_last = V_PSU
    while v_last > 0.5:
        vs, v, i = backward(v_last, p_in)
        if vs <= V_PSU:
            return v, i
        v_last -= 0.001
    return None, None


def worst_case(abl):
    """ABL (ułamek sumy łańcucha wg WLED) skupiony na końcu łańcucha; zwraca minimalne napięcie."""
    budget = abl * N * WLED_ERR           # rzeczywista "liczba pełnych lampek"
    worst = None
    for start in range(N):                # ile lampek od końca świeci
        fr = [0.0] * N
        left = budget
        for k in range(N - 1, start - 1, -1):
            fr[k] = min(1.0, left)
            left -= fr[k]
        v, _ = solve(fr)
        vmin = min(v) if v else 0.0
        worst = vmin if worst is None else min(worst, vmin)
    return worst


if __name__ == "__main__":
    # self-check 1: brak obciążenia (tylko ESP 1 W) -> ostatnia lampka ~V_PSU
    v, i = solve([0.0] * N)
    assert v and abs(v[-1] - V_PSU) < 0.05, v
    # self-check 2: jedna lampka bez ESP -> V = (V_PSU + sqrt(V_PSU^2 - 4*R*P)) / 2
    import math
    r1, p1 = r_loop(LEAD_M) + R_BOARD, P_LED_MAX / ETA
    exp_v = (V_PSU + math.sqrt(V_PSU ** 2 - 4 * r1 * p1)) / 2
    vs, _, _ = backward(exp_v, [p1])
    assert abs(vs - V_PSU) < 1e-6, (vs, exp_v)

    print(f"Pętla odcinka 5 m: {r_loop(SEG_M)*1000:.0f} mΩ + płytka {R_BOARD*1000:.0f} mΩ; LED max {P_LED_MAX:.2f} W/lampkę")
    for f in (0.4, 0.6):
        v, i = solve([f] * N)
        print(f"Równo {f:.0%} rzeczywiście: " + (" / ".join(f"{x:.2f}" for x in v) + f" V, {i:.2f} A" if v else "zapaść"))
    print(f"\nNajgorszy przypadek (jasność skupiona na końcu łańcucha, błąd szacunku WLED ×{WLED_ERR:.2f}):")
    safe = {VIN_MIN_REG: None, VIN_MIN_PRACTICAL: None}
    for abl_pct in range(20, 50, 5):
        vmin = worst_case(abl_pct / 100)
        for thr in safe:
            if vmin >= thr:
                safe[thr] = abl_pct
        print(f"  ABL {abl_pct:2d}% → min {vmin:5.2f} V")
    print(f"\nBezpieczny ABL: {safe[VIN_MIN_REG]}% (próg {VIN_MIN_REG} V, datasheet), {safe[VIN_MIN_PRACTICAL]}% (próg {VIN_MIN_PRACTICAL} V, orientacyjny)")
