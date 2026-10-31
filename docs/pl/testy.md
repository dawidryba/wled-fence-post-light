# Testy i symulacje elektroniki (2026-09-17)

Uruchomienie (ngspice 47 z Homebrew, Python 3):
```
PY=python3
$PY calc/test_obliczenia.py      # napięcia znamionowe, moce rezystorów, PTC, spadki/ABL, zatrzask UVP, straty Q1
$PY calc/sym/sym_spice.py        # SPICE: model AOD4185, łańcuch 6 lampek, włącz/wyłącz Q2, odwrotna polaryzacja, bramki, łącze danych
```
Dane wejściowe to zrzuty z EasyEDA w `.cache/` (odświeżone 2026-09-17 po zmianach PCB2). Po zmianach w projekcie trzeba je zrzucić ponownie.
Ostatni wynik: `.cache/testy_wynik.txt`. Razem 24 testy: **19 PASS, 5 WARN, 0 FAIL**.

## Wyniki

| Obszar | Wynik | Najważniejsze liczby |
|---|---|---|
| Netlisty PCB1 / PCB2 vs specyfikacja | PASS | 59 elementów / 25 sieci; 24 / 15 |
| Schemat ↔ PCB | PASS | te same elementy, footprinty, wartości, numery; C4 celowo poza PCB |
| Pinouty z API LCSC (AOD4185, 2N7002, BZT52C12, SMBJ15A, SMBJ5.0A, SN74AHCT125, SKC6812) | PASS | 71 pinów zgodnych z sieciami; test wykrywa zamianę D/S (kontrola testu) |
| Stany spoczynkowe | PASS | Q1_G, Q2_G, RELAY_G, BUF_A1, LED_RET mają rezystory |
| Odsprzęganie | PASS | U4–C15 2,5 mm; LED–C 100 nF ≤ 3 mm; ESP–C13/C14 ≈ 9 mm (moduł ma własne) |
| Model AOD4185 (kalibracja) | PASS | Rds(on) 12,1 / 18,9 mΩ; Qg 50 nC (datasheet 42 typ / 55 max) |
| Odwrotna polaryzacja −12 V | PASS | 0 µA, V12P = 0 V |
| Napięcia bramek, VIN 8–18 V | PASS | Vgs Q1/Q2 od −7,3 do −12,0 V (limit ±20); słaby Q3 i GPIO 2,64 V → −10,9 V; ESP w resecie → 0 V (wyłączony) |
| Włączenie łańcucha przez Q2 | PASS | udar 61 A (IDM 115 A), kilka ms; Tj +11 K; V12LOG (ESP) min 10,2 V |
| Wyłączenie Q2 pod pełnym obciążeniem | PASS | chwilowa moc 2 W (szyna zapada się w 8 ms); obawa o długą pracę liniową przez R2 47 k się nie potwierdziła |
| Łącze danych 5 m | PASS | BUF_A1 −0,10…4,93 V; T0H 400 → 404 ns, T1H 800 → 805 ns; opóźnienie 37 ns |
| Poziomy logiczne | PASS | ESP VOH min 2,64 V → BUF_A1 2,61 V (VIH 2,0); wyjście bufora 5 V vs VIH LED 3,38 V |
| Moce rezystorów, F1, F2, straty Q1 | PASS | R10 79 mW; F1 1,15 A / 1,61 A @70 °C; Q1 0,8 W bez ABL, 0,16 W przy ABL 35% |
| **Stan ustalony 6 lampek 100% bez ABL** | WARN | 6,5 A; ostatnia lampka 7,0 V < 8 V → **ABL w WLED obowiązkowy** (35%, `calc/spadek_cat5e.py`) |
| **Zatrzask UVP JW5068A** | WARN | po wyłączeniu relay V12LED schodzi do 3 V dopiero po ≈ 0,4 s; szybsze ponowne włączenie może zostawić diody zgaszone (bringup p. 4) |
| **D4 SMBJ5.0A** | WARN | VRWM 5,0 V, a szyna do 5,2 V: upływ rośnie, ale VBR ≥ 6,4 V, więc bez wpływu na pracę; przy zwarciu 12→5 V ochrona tylko częściowa |
| **BOM płytki LED** | WARN | J1 (pady wypustek) ma numer dostawcy `PZ254V-11-04P` (listwa) i jest w BOM → **przed eksportem wyłączyć z BOM** |
| T0H z WLED | uwaga | WLED nadaje 400 ns = maksimum z karty SK6812; łącze dokłada 4 ns (bez kumulacji, bo każda lampka regeneruje sygnał) |

## Założenia i ograniczenia (niezweryfikowane)
- Modele w `calc/sym/modele.lib` są zbudowane z parametrów kart katalogowych, nie pochodzą od producentów (AOS nie udostępnia modelu AOD4185).
  2N7002 (CJ), PESD5V0S1BA (Cd 35 p) i BZT52C12 mają parametry typowe.
- Mini560 jest modelowany jako obciążenie stałej mocy z 22 µF na wejściu (szacunek). Nie symulowano soft-startu ani zatrzasku.
- Model cieplny TO-252 to drabinka Fostera z RθJC 2,4 K/W i stałymi czasowymi typowymi dla obudowy (szacunek), płytka 45 K/W.
- Kabel: pętla 0,245 Ω i 2,5 µH na 5 m (indukcyjność szacowana), linia 100 Ω / 26 ns. Zasilacz: idealne 12 V + 30 mΩ.
  Prawdziwy zasilacz przy udarze 49 A może na chwilę wejść w zabezpieczenie nadprądowe (bringup p. 4, oscyloskop).
- SOA AOD4185 w pracy liniowej nie jest sprawdzone (brak danych liczbowych z wykresu). Symulacja pokazuje jednak tylko krótkie impulsy.
- Nie zweryfikowane testami: pinout ESP32 MiniKit (z biblioteki r0oland, do sprawdzenia na module), orientacja padów Mini560
  (potwierdzona przez użytkownika na starej płytce), footprint KF235 (wydruk 1:1).
