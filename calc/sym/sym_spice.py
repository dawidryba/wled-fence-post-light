"""Symulacje SPICE lampki (ngspice 47, `brew install ngspice`). Każdy test: netlista → ngspice -b → pomiary .meas → asercje.

python3 calc/sym/sym_spice.py [nazwa_testu …]  → wyniki + .cache/sym/*.txt (surowe logi)
Wartości elementów wg schemat.md; modele i ich źródła w calc/sym/modele.lib (przybliżone, nie od producentów).
Wynik: PASS / WARN (działa, ale mały zapas lub założenie niezweryfikowane) / FAIL.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "modele.lib")
OUT = os.path.join(HERE, "../../.cache/sym")
RESULTS = []


def spice(name, body, tran=None, control=""):
    """Uruchamia ngspice w trybie wsadowym; zwraca słownik pomiarów .meas (nazwy małymi literami)."""
    os.makedirs(OUT, exist_ok=True)
    # w bloku .control `meas` nie przyjmuje v(a,b) ani par('…') — zamiana na wektory pomocnicze
    lets, n = [], 0

    def sub(mt):
        nonlocal n
        n += 1
        expr = mt.group(1) if mt.group(1) else f"v({mt.group(2)})-v({mt.group(3)})"
        lets.append(f"let _x{n} = {expr}")
        return f"_x{n}"
    control = re.sub(r"par\('([^']*)'\)|v\((\w+),(\w+)\)", sub, control)
    control = "\n".join(lets) + "\n" + control
    net =f"* {name}\n.include {LIB}\n.options reltol=1e-4 abstol=1e-9 method=gear\n{body}\n"
    if tran:
        net += f".tran {tran}\n"
    net += f".control\nrun\n{control}\n.endc\n.end\n"
    path = os.path.join(OUT, f"{name}.cir")
    open(path, "w").write(net)
    p = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, timeout=600)
    log = p.stdout + p.stderr
    open(os.path.join(OUT, f"{name}.txt"), "w").write(log)
    meas = {}
    for m in re.finditer(r"^\s*(\w+)\s*=\s*([-+0-9.eE]+)", log, re.M):
        meas[m.group(1).lower()] = float(m.group(2))
    if "error" in log.lower() and not meas:
        raise RuntimeError(f"{name}: ngspice error, zobacz {path} / .txt\n{log[-2000:]}")
    return meas


def report(test, status, msg):
    RESULTS.append((test, status, msg))
    print(f"[{status}] {test}: {msg}")


# ---------------------------------------------------------------------------------------------------------------
def test_kalibracja_aod4185():
    """Model AOD4185 vs datasheet: Rds(on) @ -10 V / -4,5 V, ładunek bramki (układ testowy jak w datasheecie: VDS -20 V, ID -20 A)."""
    m = spice("kal_rds", """
Vg g 0 -10
Vd d 0 -0.25
M1 d g 0 AOD4185
Vg2 g2 0 -4.5
Vd2 d2 0 -0.25
M2 d2 g2 0 AOD4185
""", control="op\nlet r10 = abs(0.25/i(Vd))\nlet r45 = abs(0.25/i(Vd2))\nprint r10 r45")
    # print z ngspice: "r10 = 1.23e-02"
    r10, r45 = m.get("r10"), m.get("r45")
    # ładunek bramki: źródło prądowe 1 mA wyciąga ładunek z bramki, dren przez źródło prądowe 20 A do -20 V
    q = spice("kal_qg", """
Vs s 0 0
Vdd dd 0 -20
Rl d dd 1
M1 d g s AOD4185
Ig g 0 DC 0 PWL(0 0 1n 1m)
""", tran="1u 80m", control="""
meas tran t_th when v(g)=-1.9 cross=1
meas tran t_pl_end when v(d)=-1 cross=1
meas tran t_10 when v(g)=-10 cross=1
let qg10 = t_10 * 1m
let qgd_end = t_pl_end * 1m
print qg10 qgd_end""")
    ok = r10 and 0.010 <= r10 <= 0.015 and r45 and r45 <= 0.022
    qg = q.get("qg10", 0) * 1e9
    ok_q = 30 <= qg <= 55
    report("kalibracja AOD4185", "PASS" if ok and ok_q else "WARN",
           f"Rds(on) -10 V = {r10*1e3:.1f} mΩ (ds 12,5/15), -4,5 V = {r45*1e3:.1f} mΩ (ds 16/20); Qg(-10 V) = {qg:.0f} nC (ds 42/55), "
           f"ładunek do końca plateau Millera = {q.get('qgd_end', 0)*1e9:.0f} nC (ds Qgs+Qgd ≈ 16)")
    return r10


# ---------------------------------------------------------------------------------------------------------------
# Tor zasilania: zasilacz → lampka 1 [E] (Q1, Q2+Q3, F1, U1, F2, U2) → 5 m Cat5e → lampki 2…6 [S] (Q1, drut S–D Q2, F1, U1).
# Kabel 5 m, 3 żyły +12 V i 4 GND, 24 AWG 0,0842 Ω/m (calc/spadek_cat5e.py): pętla 0,14 + 0,105 Ω; indukcyjność pętli ~0,5 µH/m (szacunek).
N_LAMPS = 6
P_FULL = 40 * 0.0405 * 5 / 0.9       # 40 diod × 40,5 mA × 5 V / sprawność 0,9 (szacunek) = 9 W
P_IDLE = 40 * 0.29e-3 * 5 / 0.8 + 0.3   # prąd statyczny diod 0,29 mA (datasheet SK6812) + własny moduł (szacunek)
P_ESP = 1.5                         # ESP32 z Wi-Fi, średnio (szacunek)


def chain(p_led, gpio, r2="47k", q3="N2N7002", vpsu="12", lamps=N_LAMPS, extra=""):
    """Netlista łańcucha. p_led: wyrażenie mocy LED na lampkę (może zależeć od time). gpio: źródło napięcia GPIO26."""
    s = [f"Vpsu psu 0 {vpsu}", "Rpsu psu j1_1 0.03",
         f"Vgpio gpio 0 {gpio}", "R4 gpio relg 100", "R5 relg 0 100k", f"MQ3 q3d relg 0 {q3}",
         f"R2 q2g v12p_1 {r2}", "DZ2 q2g v12p_1 BZT52C12", "R3 q2g q3d 4.7k",
         "Vsq2 v12p_1 q2s 0", "MQ2 v12sw_1 q2g q2s AOD4185",
         "RF2 v12p_1 v12log 0.7", "C11 v12log 0 10u", "R11 v12log 0 2.2k", f"XU2 v12log 0 MINI560 params: P={P_ESP}",
         "Bpq2 0 tq2 I = max(V(v12p_1,v12sw_1) * I(Vsq2), 0)", "XT2 tq2 0 TERM_TO252",
         "Bpq1 0 tq1 I = max(V(j1_1,v12p_1) * abs(I(Vsq1)), 0)", "XT1 tq1 0 TERM_TO252"]
    for k in range(1, lamps + 1):
        s += [f"Vsq{k} j1_{k} q1d_{k} 0" if k == 1 else f"Rj{k} j1_{k} q1d_{k} 1m",
              f"MQ1_{k} q1d_{k} q1g_{k} v12p_{k} AOD4185", f"R1_{k} q1g_{k} 0 47k", f"DZ1_{k} q1g_{k} v12p_{k} BZT52C12",
              f"DD1_{k} 0 v12p_{k} SMBJ15A", f"C1_{k} v12p_{k} c1_{k} 220u", f"Rc1_{k} c1_{k} 0 0.12", f"C2_{k} v12p_{k} 0 10u",
              ]
        if k > 1:
            s.append(f"Rdrut{k} v12p_{k} v12sw_{k} 2m")                # drut S–D zamiast Q2
        s += [f"RF1_{k} v12sw_{k} v12led_{k} 0.05", f"C5_{k} v12led_{k} c5_{k} 220u", f"Rc5_{k} c5_{k} 0 0.12",
              f"C6_{k} v12led_{k} 0 10u", f"R10_{k} v12led_{k} 0 2.2k",
              f"Cin{k} v12led_{k} 0 22u",
              f"Bu1_{k} v12led_{k} 0 I = ({p_led}) / max(V(v12led_{k}), 6) * min(max((V(v12led_{k}) - 3) / 3, 0), 1)"]
        if k < lamps:
            s += [f"Rk{k} v12sw_{k} lk{k} 0.245", f"Lk{k} lk{k} j1_{k + 1} 2.5u"]
    return "\n".join(s) + "\n" + extra


def test_stan_ustalony_pelna_moc():
    """Wszystkie lampki 100% (ABL wyłączony — najgorszy przypadek): napięcia V12LED, straty Q1/Q2, prąd F1."""
    m = spice("ustalony", chain(P_FULL, "3.3"), tran="1m 300m 250m", control="""
meas tran v1 avg v(v12led_1) from=280m to=300m
meas tran v6 avg v(v12led_6) from=280m to=300m
meas tran ipsu avg i(Vsq1) from=280m to=300m
meas tran vgs1 avg v(q1g_1,v12p_1) from=280m to=300m
meas tran vgs2 avg v(q2g,v12p_1) from=280m to=300m
meas tran pq1 avg v(tq1) from=280m to=300m
meas tran if1 avg par('(v(v12sw_1)-v(v12led_1))/0.05') from=280m to=300m""")
    v6 = m["v6"]
    i = abs(m["ipsu"])
    status = "PASS" if v6 >= 8 else "WARN"
    report("stan ustalony 6 lampek 100%", status,
           f"prąd z zasilacza {i:.2f} A, V12LED lampka 1 = {m['v1']:.2f} V, lampka 6 = {v6:.2f} V (JW5068A: 5 V gwarantowane od 8 V); "
           f"Vgs Q1 = {m['vgs1']:.1f} V, Vgs Q2 = {m['vgs2']:.1f} V; F1 {abs(m['if1']):.2f} A (hold 1,61 A @70 °C)")


def test_wlaczenie_q2():
    """WLED włącza relay (GPIO26 0→3,3 V) przy rozładowanym łańcuchu: udar przez Q2, energia i Tj, zapad V12LOG (zasilanie ESP)."""
    m = spice("wlaczenie", chain(P_IDLE, "PWL(0 0 100m 0 100.01m 3.3)"), tran="10u 400m", control="""
meas tran ipk max i(Vsq2) from=100m to=400m
meas tran tjq2 max v(tq2) from=100m to=400m
meas tran vlog min v(v12log) from=100m to=400m
meas tran vp1 min v(v12p_1) from=100m to=400m
meas tran v6 avg v(v12led_6) from=380m to=400m
meas tran ipsu max i(Vsq1) from=100m to=400m
meas tran ppk max par('(v(v12p_1)-v(v12sw_1))*i(Vsq2)') from=100m to=400m""")
    ipk, tj = abs(m["ipk"]), m["tjq2"]
    ok = tj + 60 < 150 and m["vlog"] > 6.5
    report("włączenie łańcucha przez Q2", "PASS" if ok else "WARN",
           f"szczyt prądu Q2 {ipk:.1f} A (IDM 115 A), szczyt mocy {m['ppk']:.0f} W, prąd z zasilacza max {abs(m['ipsu']):.0f} A, przyrost Tj Q2 {tj:.1f} K (przy 60 °C otoczenia → {60 + tj:.0f} °C), "
           f"min V12P {m['vp1']:.2f} V, min V12LOG (ESP) {m['vlog']:.2f} V (próg ~6,5 V: Mini560 Vout ≤ VIN−3 V + LDO ESP)")


def _wylaczenie(r2):
    m = spice(f"wylaczenie_{r2}", chain(P_FULL, "PWL(0 3.3 200m 3.3 200.01m 0)", r2=r2), tran="20u 900m", control="""
meas tran tjq2 max v(tq2) from=200m to=900m
meas tran pmax max v(tq2) from=200m to=900m
meas tran t_off when v(v12led_1)=3 fall=1
meas tran vgs_end avg v(q2g,v12p_1) from=880m to=900m
meas tran ppk max par('(v(v12p_1)-v(v12sw_1))*i(Vsq2)') from=200m to=900m
meas tran t_lin_end when v(v12sw_1)=1 fall=1""")
    return m


def test_wylaczenie_q2_pod_obciazeniem():
    """ESP resetuje się / WLED wyłącza relay przy świecących lampkach (najgorszy przypadek): Q2 wyłącza się przez R2 47 k — praca liniowa."""
    m = _wylaczenie("47k")
    m10 = _wylaczenie("10k")
    tj, tj10 = m["tjq2"], m10["tjq2"]
    ppk = abs(m.get("ppk", 0))
    status = "PASS" if tj + 60 < 125 else ("WARN" if tj + 60 < 150 else "FAIL")
    report("wyłączenie Q2 pod pełnym obciążeniem", status,
           f"R2 = 47 k: szczyt mocy w Q2 {ppk:.0f} W, przyrost Tj {tj:.0f} K → {60 + tj:.0f} °C przy 60 °C otoczenia, "
           f"V12LED lampki 1 spada do 3 V po {m.get('t_off', float('nan'))*1e3 - 200:.0f} ms; "
           f"dla porównania R2 = 10 k: przyrost Tj {tj10:.0f} K (Vgs włączenia wtedy {-12*10/14.7:.1f} V). "
           "Uwaga: SOA tranzystorów trench w pracy liniowej bywa gorsza niż wynika z samej temperatury — niezweryfikowane.")


def test_odwrotna_polaryzacja():
    m = spice("odwrotna", chain(P_IDLE, "0", vpsu="-12", lamps=1), tran="10u 100m", control="""
meas tran ipsu avg i(Vsq1) from=90m to=100m
meas tran vp avg v(v12p_1) from=90m to=100m
meas tran vds1 avg v(j1_1,v12p_1) from=90m to=100m""")
    i = abs(m["ipsu"])
    report("odwrotna polaryzacja −12 V", "PASS" if i < 1e-3 and abs(m["vp"]) < 0.5 else "FAIL",
           f"prąd {i*1e6:.1f} µA, V12P = {m['vp']:.3f} V, Vds Q1 = {m['vds1']:.1f} V (BVDSS −40 V)")


def test_napiecia_bramek():
    """Vgs Q1/Q2 w zakresie VIN 8…18 V (18 V ≈ przewodzenie SMBJ15A) i przy słabym Q3 (Vth 2,5 V, GPIO VOH 2,64 V = 0,8·3,3 V)."""
    res = []
    for v in (8, 12, 14.4, 18):
        m = spice(f"bramki_{v}", chain(P_IDLE, "3.3", vpsu=str(v), lamps=1), tran="1m 100m 90m", control="""
meas tran vgs1 avg v(q1g_1,v12p_1) from=95m to=100m
meas tran vgs2 avg v(q2g,v12p_1) from=95m to=100m""")
        res.append((v, m["vgs1"], m["vgs2"]))
    w = spice("bramki_slaby_q3", chain(P_IDLE, "2.64", q3="N2N7002_SLABY", lamps=1), tran="1m 100m 90m", control="""
meas tran vgs2 avg v(q2g,v12p_1) from=95m to=100m""")
    z = spice("bramki_gpio_hiz", chain(P_IDLE, "0", lamps=1).replace("R4 gpio relg 100", "R4 gpio relg 1G"), tran="1m 100m 90m", control="""
meas tran vgs2 avg v(q2g,v12p_1) from=95m to=100m""")
    ok = all(-20 < a <= -4.5 and -20 < b <= -4.5 for v, a, b in res if v >= 8) and w["vgs2"] <= -4.5 and z["vgs2"] > -1
    report("napięcia bramek Q1/Q2", "PASS" if ok else "FAIL",
           "; ".join(f"VIN {v} V: Vgs Q1 {a:.1f}, Q2 {b:.1f}" for v, a, b in res)
           + f"; słaby Q3 + GPIO 2,64 V: Vgs Q2 {w['vgs2']:.1f} V; GPIO odłączony (boot/reset): Vgs Q2 {z['vgs2']:.2f} V "
           "(wymagane −4,5…−20 V gdy włączony — Rds(on) podane od −4,5 V, abs. max ±20 V)")


# ---------------------------------------------------------------------------------------------------------------
# Dane: lampka n (U4 bramka 2: LED_RET → BUF_Y2) → R9 100 Ω → D3 ESD → J2 → 5 m Cat5e (para DATA + biało-zielony GND,
# Z0 100 Ω, v = 0,64 c → 26 ns; 0,84 Ω) → J1 lampki n+1 → D2 ESD → R7 220 Ω → JP1 (K) → BUF_A1 (R8 10 k, U4 Ci) → U4 bramka 1 → LED_DIN
# → LB1 → R1 330 Ω (płytka LED) → DIN LED1. Wzorzec WLED/NeoPixelBus SK6812: bit 0 = 400/850 ns, bit 1 = 800/450 ns.
T0H, T0L, T1H, T1L = 400e-9, 850e-9, 800e-9, 450e-9


def _bits(pattern):
    t, pts = 1e-9, ["0 0"]
    for b in pattern:
        hi, lo = (T1H, T1L) if b == "1" else (T0H, T0L)
        pts += [f"{t:.4e} 0", f"{t + 1e-9:.4e} 5", f"{t + hi:.4e} 5", f"{t + hi + 1e-9:.4e} 0"]
        t += hi + lo
    return "PWL(" + " ".join(pts) + ")", t


def test_lacze_danych_5m():
    pattern = "0101100100110101"
    src, tend = _bits(pattern)
    m = spice("dane_5m", f"""
Vcc vcc 0 5
Vret ret 0 {src}
XU4a ret y2 vcc 0 AHCT125
R9 y2 dout 100
XD3a dout 0 ESD
T1 dout 0 far 0 Z0=100 TD=26n
Rline far jin 0.84
XD2a jin 0 ESD
R7 jin bufa 220
R8 bufa 0 10k
XU4b bufa ledin vcc 0 AHCT125
Rtr ledin lb 0.5
R1 lb din 330
Cdin din 0 5p
.subckt ESD a k
D1 a m PESDHALF
D2 k m PESDHALF
.ends
""", tran=f"0.1n {tend:.4e}", control=f"""
meas tran vmax max v(bufa)
meas tran vmin min v(bufa)
meas tran vjmax max v(jin)
meas tran vjmin min v(jin)
meas tran dinmin_hi max v(din)
meas tran t0h_in trig v(ret) val=2.5 rise=1 targ v(ret) val=2.5 fall=1
meas tran t0h_out trig v(din) val=2.5 rise=1 targ v(din) val=2.5 fall=1
meas tran t1h_in trig v(ret) val=2.5 rise=2 targ v(ret) val=2.5 fall=2
meas tran t1h_out trig v(din) val=2.5 rise=2 targ v(din) val=2.5 fall=2
meas tran dly trig v(ret) val=2.5 rise=1 targ v(din) val=2.5 rise=1""")
    t0, t1 = m["t0h_out"] * 1e9, m["t1h_out"] * 1e9
    over = m["vmax"] <= 5.5 and m["vmin"] >= -0.5
    ok_t = 250 <= t0 <= 400 + 15 and 650 <= t1 <= 1000
    status = "PASS" if over and ok_t else "WARN"
    report("łącze danych 5 m (lampka → lampka)", status,
           f"na wejściu bufora (BUF_A1) {m['vmin']:.2f}…{m['vmax']:.2f} V (dopuszczalne −0,5…5,5 V), na zacisku J1 {m['vjmin']:.2f}…{m['vjmax']:.2f} V; "
           f"T0H {m['t0h_in']*1e9:.0f} → {t0:.0f} ns (SK6812: 250–400 ns), T1H {m['t1h_in']*1e9:.0f} → {t1:.0f} ns (650–1000 ns), "
           f"opóźnienie {m['dly']*1e9:.0f} ns. Uwaga: WLED nadaje T0H = 400 ns = maksimum z datasheetu — każde wydłużenie wychodzi poza kartę.")


def test_poziomy_logiczne():
    """DC: ESP 3,3 V → R6 100 Ω → JP1 (E) → BUF_A1 (R8 10 k) wobec VIH 2,0 V; wyjście bufora vs VIH diody 0,65·VDD przy VDD 5,2 V."""
    vesp_min = 3.3 * 0.8                         # ESP32 VOH ≥ 0,8·VDD (karta ESP32)
    v_bufa = vesp_min * 10e3 / (10e3 + 100)
    voh = 5.0 - 30 * 1e-6                        # obciążenie wejściem LED (µA) — Rout modelu 30 Ω
    vih_led = 0.65 * 5.2                         # VDD diody do 5,2 V (wyjście Mini560 bez obciążenia)
    ok = v_bufa >= 2.0 + 0.3 and voh >= vih_led + 0.5
    report("poziomy logiczne DC", "PASS" if ok else "FAIL",
           f"BUF_A1 przy ESP VOH min {vesp_min:.2f} V: {v_bufa:.2f} V (VIH AHCT 2,0 V); wyjście bufora ≈ {voh:.2f} V (VCC = V5LED) "
           f"vs VIH LED {vih_led:.2f} V; LED zasilane z tej samej szyny co bufor — brak zasilania diod przez linię danych po wyłączeniu Q2")


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    sel = sys.argv[1:]
    for t in tests:
        if not sel or t.__name__ in sel:
            t()
    bad = [r for r in RESULTS if r[1] == "FAIL"]
    print(f"\n{len(RESULTS)} testów: {sum(r[1] == 'PASS' for r in RESULTS)} PASS, {sum(r[1] == 'WARN' for r in RESULTS)} WARN, {len(bad)} FAIL")
    sys.exit(1 if bad else 0)
