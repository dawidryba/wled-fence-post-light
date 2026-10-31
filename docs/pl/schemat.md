# Schemat — lampka słupkowa WLED RGBW (wersja 2, 2026-09-16, po weryfikacji niezależnej)

Dwie płytki:
- **MAIN** — płytka główna, jedna na słupek, ten sam projekt w każdej lampce (lutuje użytkownik, elementy 1206).
- **LED** — płytka diod, 4 szt. na lampkę (montuje JLCPCB).

Zasilanie 12 V po Cat5e. Jasność ograniczana w WLED (ABL) — konkretne ustawienia i procedura pomiaru w `bringup.md`.
Poza PCB: **bezpiecznik 7,5 A zwłoczny / ATO przy zasilaczu** (udar przy włączeniu 25–50 A < 1 ms). Uwaga: zwarcie na końcu łańcucha to ~7,7 A — ten bezpiecznik go nie przepali; ogranicza zasilacz 10 A.
Legenda wariantów: **[E]** tylko w lampce z ESP, **[S]** tylko w lampkach bez ESP, bez oznaczenia = zawsze.

## Sieci
| Sieć | Opis |
|---|---|
| VIN | +12 V z zacisku IN (przed ochroną) |
| V12P | +12 V po ochronie przed odwrotną polaryzacją |
| V12SW | +12 V przełączane (Q2 albo drut na padach Q2) → lokalna Mini560 LED i zacisk OUT |
| V12LED | V12SW za bezpiecznikiem F1 |
| V5LED | 5 V dla LED i bufora (Mini560 LED) |
| V12LOG / V5ESP | [E] zasilanie ESP (za F2, Mini560 logiki) |
| DATA_IN / DATA_OUT | dane z / do kabla |
| BUF_A1 | wejście bufora (środek zworki JP1) |
| LED_DIN / LED_RET | dane do płytki LED 1 / powrót z płytki LED 4 |
| RELAY | [E] GPIO26 → sterowanie P-MOSFET-em |

## MAIN — połączenia
### Zaciski (Cat5e)
| Ref | Część | +12 V | GND | DATA |
|---|---|---|---|---|
| J1 IN | KF235-3.81, 4 × 2P łączone (8 torów, raster 3,81 mm, sprężynowe, AliExpress; footprint „KF235-3.81-8P (4x2P)”, 16 padów w 2 rzędach) | tory 1–3 VIN | tory 4–7 GND | tor 8 DATA_IN |
| J2 OUT | KF235-3.81, 4 × 2P | tory 1–3 V12SW | tory 4–7 GND | tor 8 DATA_OUT |

Cat5e (po 1 żyle na zacisk, bez skręcania): 1 pomarańczowy, 2 biało-pomarańczowy, 3 brązowy (+12 V) · 4 niebieski, 5 biało-niebieski, 6 biało-brązowy, 7 biało-zielony (GND) · 8 zielony (DATA, obok swojej pary GND).

### Ochrona wejścia (zawsze)
| Ref | Część | Połączenia |
|---|---|---|
| Q1 | AOD4185 C400894 (P-MOSFET, TO-252: G, D=tab, S) | D=VIN, S=V12P, G=Q1_G |
| R1 | 47 k 1206 (C137270) | Q1_G – GND |
| ZD1 | BZT52C12 C173429 (SOD-123) | katoda=V12P, anoda=Q1_G (Vgs ≤ 12 V) |
| D1 | SMBJ15A C113988 (SMB) | katoda=V12P, anoda=GND |
| C1 | 220 µF 35 V 8×10, 105 °C 5000 h (C134820, Lelon VZH) | V12P – GND |
| C2, C3 | 10 µF 25 V 1206 (C14860), 100 nF 1206 (C24497) | V12P – GND |

### Przełącznik zasilania LED i łańcucha
| Ref | Część | Połączenia |
|---|---|---|
| Q2 [E] | AOD4185 C400894 | S=V12P, D=V12SW, G=Q2_G |
| [S] | **drut na padach Q2**: pad D (tab) ↔ pad S, Q2 niemontowany | V12P – V12SW (nie da się zamontować obu naraz) |
| R2 | 47 k 1206 — **zawsze montowany** (bramka Q2 nie wisi, gdyby ktoś wlutował Q2 w [S]) | Q2_G – V12P (domyślnie wyłączony) |
| ZD2 [E] | BZT52C12 | katoda=V12P, anoda=Q2_G |
| R3 [E] | 4,7 k 1206 (C17936) | Q2_G – Q3_D (Vgs ≈ −10,9 V) |
| C4 | **usunięty (2026-09-17)**: poza PCB i BOM (addIntoPcb = false). RC na bramce dawał narastanie ≈ 0,4 ms, a nie miękki start. Symbol został na schemacie. | — |
| Q3 [E] | 2N7002 C8545 (SOT-23) | D=Q3_D, S=GND, G=RELAY_G |
| R4 [E] | 100 Ω 1206 (C17901) | RELAY – RELAY_G |
| R5 [E] | 100 k 1206 (C17900) | RELAY_G – GND |

W lampce z ESP: **Q2, ZD2, R3, Q3, R4, R5 montowane** (R2 zawsze). W pozostałych: **drut S–D na padach Q2**, reszta pusta.

### Zasilanie LED (zawsze)
| Ref | Część | Połączenia |
|---|---|---|
| F1 | **1812L300/30GR C48985875** (PTC 1812: hold 3,00 A @25 °C / 2,01 A @60 °C / 1,61 A @70 °C, trip 5 A, 30 V) | V12SW – V12LED |
| C5 | 220 µF 35 V 8×10, 105 °C 5000 h (C134820, Lelon VZH) | V12LED – GND |
| C6, C7 | 10 µF 25 V 1206, 100 nF 1206 | V12LED – GND |
| R10 | 2,2 k 1206 (C17948), 65 mW | V12LED – GND: rozładowanie po wyłączeniu (JW5068A zatrzaskuje UVP przy Vout < ~3,25 V; restart dopiero po spadku VIN < UVLO) |
| U1 | Mini560 PRO 5 V (JW5068A: VIN 4–26 V, abs. max 28 V, Vout ≤ VIN − 3 V → regulacja 5 V gwarantowana od 8 V); footprint LCSC C9900015474 | IN+=V12LED, IN−=GND, OUT+=V5LED, OUT−=GND |
| C8 | 470 µF **16 V** 8×10, 105 °C 5000 h (C164069) — lutować po zmierzeniu 5 V na U1 | V5LED – GND |
| C9, C10 | 10 µF 1206, 100 nF 1206 | V5LED – GND |
| D4 | SMBJ5.0A C113974 (SMB; VRWM 5 V, VBR ≥ 6,4 V, IR ≤ 800 µA, Vc 9,2 V) | katoda=V5LED, anoda=GND: przy zwarciu klucza przetwornicy (12 V na 5 V) zwiera szynę → zadziała F1 |

### Zasilanie ESP [E]
| Ref | Część | Połączenia |
|---|---|---|
| F2 [E] | JK-nSMD050-30 1206 C720075 (0,5 A / 30 V) | V12P – V12LOG |
| C11, C12 [E] | 10 µF 25 V 1206, 100 nF 1206 | V12LOG – GND |
| U2 [E] | Mini560 Pro 5 V | IN+=V12LOG, OUT+=V5ESP, IN−/OUT−=GND |
| C13, C14 [E] | 10 µF 1206, 100 nF 1206 | V5ESP – GND |
| R11 [E] | 2,2 k 1206 (C17948) | V12LOG – GND: rozładowanie wejścia U2 (zatrzask UVP JW5068A po krótkim zaniku zasilania) |
| U3 [E] | ESP32 D1 Mini (**nie podłączać USB przy zasilaniu 12 V** — VCC MiniKit może być połączony z VBUS, niezweryfikowane) (MH-ET LIVE, 40 pin; footprint tylko 2 rzędy zgodne z D1 Mini, rozstaw 22,86 mm) | pin 35 VCC(USB)=V5ESP, pin 33 GND, pin 31 IO16=ESP_DATA, pin 6 IO26=RELAY |

Wybór GPIO: IO16 — zalecany przez WLED dla ESP32; IO26 — nie jest pinem bootowania (0, 2, 4, 5, 12, 15 omijamy).
Pinout wg biblioteki r0oland/ESP32_mini_KiCad_Library — **zweryfikować z kupionym modułem**.

### Dane
| Ref | Część | Połączenia |
|---|---|---|
| U4 | SN74AHCT125DR C155176 (SOIC-14) | 14 VCC=V5LED, 7 GND; 1 1OE=GND, 2 1A=BUF_A1, 3 1Y=LED_DIN; 4 2OE=GND, 5 2A=LED_RET, 6 2Y=BUF_Y2; 10 3OE=V5LED, 9 3A=GND; 13 4OE=V5LED, 12 4A=GND; 8, 11 NC |
| C15 | 100 nF 1206 | przy pinie 14 |
| JP1 | zworka lutownicza 3-padowa | A=ESP_DATA_R, środek=BUF_A1, B=DATA_IN_R ([E]: A–środek, [S]: B–środek) |
| R6 [E] | 100 Ω 1206 | ESP_DATA – ESP_DATA_R |
| R7 | 220 Ω 1206 | DATA_IN – DATA_IN_R |
| R8 | 10 k 1206 (C17902) | BUF_A1 – GND (stan zdefiniowany przy otwartej zworce) |
| R9 | 100 Ω 1206 | BUF_Y2 – DATA_OUT |
| D2, D3 | PESD5V0S1BA C2827694 (SOD-323, dwukierunkowa) | DATA_IN – GND, DATA_OUT – GND (przy zaciskach) |
| R12 | 100 k 1206 (C17900) | LED_RET – GND: wejście U4.5 nie pływa przy wyjętej płytce LB4 |

Bufor zasilany z V5LED: po wyłączeniu LED bufor też jest bez zasilania, a wejście 74AHCT125 przyjmuje do 5,5 V
niezależnie od VCC (clamp tylko VI < 0) → brak zasilania diod przez linię danych.

### Gniazda płytek LED (wypustki w szczelinach)
| Szczelina | 5V | GND | DIN | DOUT |
|---|---|---|---|---|
| LB1 | V5LED | GND | LED_DIN | D12 |
| LB2 | V5LED | GND | D12 | D23 |
| LB3 | V5LED | GND | D23 | D34 |
| LB4 | V5LED | GND | D34 | LED_RET |

### Punkty testowe
TP1 V12P · TP2 V12SW · TP3 V5LED · TP4 V5ESP [E] · TP5 LED_DIN · TP6 DATA_OUT · TP7, TP8 GND · **TP9 V12LED · TP10 BUF_A1 · TP11 Q2_G [E]**

## LED — połączenia (4 szt. na lampkę, JLCPCB) — wersja jednorzędowa (2026-09-17)
| Ref | Część | Połączenia |
|---|---|---|
| LED1…LED10 | SKC6812RGBW-WS-B C5380879 (5050, 1 GND, 2 DIN, 3 VDD, 4 DOUT) | 1 rząd × 10, skok 7,14 mm (140/m), łańcuch LED1 → LED10 |
| C1…C10 | 100 nF 0603 C14663 (basic) | VDD–GND przy każdej diodzie |
| C11 | 10 µF 0805 25 V X5R (C15850, basic) | 5V–GND przy wypustce |
| R1 | 330 Ω 0603 (C23138, basic) | J1.DIN → LED1.DIN (zalecenie datasheetu: rezystor na wejściu) |
| R2 | 330 Ω 0603 (C23138, basic) | LED10.DOUT → J1.DOUT (zalecenie datasheetu: rezystor na wyjściu) |
| J1 | footprint `LAMPKA_LED_TAB` (do zrobienia): wypustka A 10 mm = 1 5V, 2 GND; B 8 mm = 3 DIN, 4 DOUT; pady obustronne | |
| Tył | wylewki GND i 5V + przelotki termiczne przy padach diod | |

Maks. prąd na płytkę LED: 10 × 40,5 mA = 0,41 A (5 V); lampka 40 diod = 8,1 W.
Wersja dwurzędowa (2 × 10/11) — później; geometria w `calc/geometria.py` (`N_ROWS = 2`).

## EasyEDA Pro (stan 2026-09-16) — schemat WERSJA 2
- Projekt **"Lampka słupek RGBW"** (uuid 414e6d57adfb46f7ad409bed3dfba921), Board1 → Schematic1/P1 (A3) + PCB1.
- Schemat v2 narysowany klasycznie: szyny zasilania, symbole masy/zasilania, przewody w blokach
  (wejście, wyłącznik, zasilanie LED, zasilanie ESP, dane, gniazda płytek LED), etykiety na złączach i pinach U4/U3.
  Notatki o wariantach [E]/[S] i C4 = DNP w lewym górnym rogu arkusza.
- ERC: 0 błędów krytycznych, 0 błędów, 3 ostrzeżenia (atrybuty po nadaniu oznaczeń ×2; celowo wolne piny U3A/U3B/U4.8/U4.11).
- Import do PCB1 wykonany; `calc/verify_netlist.py` (v2) → **zgodna** (61 elementów z R10–R12 i D4, 25 sieci).
- Wartości (Value) wpisane dla R1–R12, C1–C15, F1, F2, ZD1, ZD2; C4 wyłączony z BOM.
- Niezależny przegląd schematu (2026-09-16): **ZIELONE** — połączenia 1:1 z PCB, pinouty zgodne z datasheetami.
- Zastępcze symbole/footprinty do podmiany przy PCB:
  - U3A/U3B: dwie listwy HDR 1×10 → **jeden footprint 2×10** z rozstawem rzędów 22,86 mm, pin 1 na końcu RST/TXD (strona przeciwna do USB),
    napis „USB” na sitodruku — zamiana/obrót listew podaje 5 V na 3V3 albo IO22. Pinout potwierdzony z r0oland i obrazkiem Nettigo.
  - JP1: HDR 1×3 → footprint zworki lutowniczej 3-padowej (brak w bibliotece — do narysowania).
  - LB1–LB4: HDR 1×4 → szczeliny z padami pod wypustki płytek LED.
  - Q2 w lampkach [S]: pady muszą pomieścić drut S–D (≥ 0,5 mm² / AWG 20, krótki; tab lutować mocniejszą grotą);
    **pad S (pin 3, 2,5×1,2 mm) powiększyć / dołożyć miedź** — płynie przez niego do 7 A łańcucha.
  - U1/U2 Mini560: orientacja padów footprintu C9900015474 **potwierdzona** — ten sam footprint na starej płytce działał (użytkownik, 2026-09-17).
- Tor przelotowy (J1 → Q1 → Q2/drut → J2 oraz GND) projektować na ≥ 10–12 A (zwarcie na końcu łańcucha ~7,7 A; zabezpieczenie zasilacza 10 A), duże pola miedzi pod TO-252.
- **Płytka LED** (Board2: schemat page 05c37932d6723f8c, PCB 0af1b9fc8a479dfe): wersja jednorzędowa — 10× LED, C1–C10 100 nF, C11 10 µF,
  R1/R2 330 Ω, J1 (1 5V, 2 GND, 3 DIN, 4 DOUT). DRC: 0 błędów, brak wolnych pinów. Netlista PCB zgodna: `calc/verify_led_netlist.py` (24 elementy, 15 sieci). Footprint LED: LED-SMD_4P-L5.0-W4.9-BR — porównać z padami z datasheetu przy layoucie.

## Do sprawdzenia przed PCB
- [ ] Wymiary i rozkład padów Mini560 Pro (pomiar posiadanego modułu).
- [ ] Pinout kupionego ESP32 D1 Mini.
- [ ] Symulacja miękkiego startu Q2 (R3; C4 usunięty) — czas narastania, prąd udarowy, straty w Q2.
- [ ] F1: prąd trzymania w temperaturze pracy obudowy.
- [ ] Wartości R1/R2 płytki LED i R7/R9 — próba na prototypie (datasheet: "subject to actual test").

## Stan PCB (2026-09-17, po przeglądzie)
- Netlisty ponownie zweryfikowane na stanie PCB (bez importu): `calc/verify_netlist.py .cache/pcb_netlist_main.json` → zgodna
  (C4 usunięty z EXPECTED; J1/J2 KF235 mają ten sam podział padów co WAGO), `calc/verify_led_netlist.py` → zgodna. DRC PCB1 = 0, PCB2 = 0.
