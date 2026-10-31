# Lampka na słupek: dokumentacja wymiarowa elektroniki do projektu obudowy 3D

Stan: 2026-09-17. Źródła danych: zrzuty EasyEDA Pro (`../.cache/review_dump_pcb1.json`, `review_dump_pcb2.json`), eksporty STEP
z EasyEDA (`PCB1_glowna.step`, `PCB2_LED.step`), wymagania z `../notes.md`, złożenie i weryfikacja w FreeCAD 1.0.2 (skrypty w `skrypty/`).
Wszystkie wymiary w mm. Te same dane w wersji maszynowej są w `wymiary.json`.

Dokument jest samowystarczalny: nie potrzebujesz EasyEDA. Obudowę projektujesz wokół złożenia `elektronika_zlozenie.step`,
które jest już ustawione w układzie lampki opisanym niżej.

> **Uwaga:** dokument powstał na etapie projektowania obudowy. Aktualna obudowa (`enclosure/`) zamiast stałych ograniczników ma 4 drukowane kliny wsuwane w rowki w narożnikach, a PCB1 ma pełny obrys 80×80 bez ścięć.

---

## 1. Co to jest

Lampka nakładana na słupek ogrodzeniowy 80×80 mm. W środku są dwa rodzaje płytek:
- **PCB1**: płytka główna 80×80 × 1,6. Leży poziomo pod daszkiem i jest przykręcona 4 śrubami M2,5 do słupków wystających z daszka.
  Elementy ma po obu stronach.
- **PCB2** ×4: płytki LED 73,6 × 14,4 × 1,6. Stoją pionowo i wisią pod płytką główną. Są wlutowane wypustkami w szczeliny
  PCB1 i ułożone w „wiatraczek” wzdłuż czterech ścian. Diody świecą poziomo na zewnątrz, przez transparentny pas obudowy.

Do lampki wchodzą od dołu, przez słupek, dwa kable Cat5e: wejście do J1 i wyjście do J2.

## 2. Układ współrzędnych i transformacje

**Układ lampki** (w nim są `elektronika_zlozenie.step`, `wymiary.json` i rysunki):
- Z w górę, **Z = 0 to dolna krawędź obudowy**.
- X i Y poziomo, początek układu w osi lampki (środek kwadratu 90×90).
- Widok z góry, od daszka: X w prawo, Y w górę. Obudowa jest symetryczna, więc „przód” lampki wybierasz dowolnie
  (patrz asymetrie w p. 6).

**PCB1: EasyEDA → lampka.** W EasyEDA strona „TOP” płytki głównej jest skierowana **w dół**, do wnętrza słupka.
Widok TOP w EasyEDA to więc widok od spodu lampki. W STEP z EasyEDA powierzchnia BOTTOM płytki ma z_e = 0, a TOP z_e = 1,6.

```
X = x_e      Y = −y_e      Z = 72,0 − z_e          (obrót 180° wokół osi X + przesunięcie; to nie jest lustro)
macierz 4×4: [[1,0,0,0],[0,−1,0,0],[0,0,−1,72],[0,0,0,1]]
```

**PCB2: układ lokalny → lampka.** Układ lokalny płytki LED:
- x_l biegnie wzdłuż płytki (−36,8…36,8);
- y_l mierzysz od dolnej krawędzi (korpus 0…14,4, wypustki 14,4…17,0);
- z_l to grubość (0 = tył/radiator, 1,6 = strona diod).

W gnieździe LBn o środku (cx, cy) i obrocie θ z EasyEDA:
x_l → R(θ)·x̂_e, y_l → −ẑ_e, z_l → R(θ)·ŷ_e (na zewnątrz). Punkt (0; 14,4; 0,8) trafia w (cx; cy; 1,6)_e.
Potem stosujesz transformację PCB1. Implementacja: funkcja `led2l()` w `skrypty/dokumentacja.py`.

**Kontrola poprawności** (sprawdzona na danych i w złożeniu):
- diody każdej płytki LED leżą **na zewnątrz** jej lica;
- elementy strony TOP (ESP, złącza, elektrolity) są pod płytką główną (Z < 70,4);
- elementy strony BOTTOM (Mini560, SMD) są nad nią (Z > 72);
- wypustki LED nie przecinają bryły PCB1: wspólna objętość 0, bo mieszczą się w szczelinach.

## 3. Obudowa: wymagania (dane wejściowe od użytkownika)

| Parametr | Wartość | Uwagi |
|---|---|---|
| Obrys zewnętrzny korpusu | 90 × 90 | X, Y ∈ [−45; 45] |
| Ścianka | 4 | wnętrze 82 × 82, X, Y ∈ [−41; 41] |
| Wysokość całkowita | 83 | korpus Z 0…79, daszek Z 79…83 |
| Daszek | 100 × 100 × 4, czarny | X, Y ∈ [−50; 50], Z 79…83 |
| Pas transparentny | 40 mm pod daszkiem | **Z 39…79** |
| Dół korpusu | czarny | Z 0…39 |
| Słupek | 80 × 80, nasuwany od dołu | luz 1 mm na stronę do wnętrza 82 |
| Ograniczniki zagłębienia słupka | na **Z = 25** | wierzch słupka opiera się na Z = 25; ograniczniki muszą wystawać do wnętrza ponad 1 mm (poza 40) |
| Przewężenia trzymające słupek | 6 szt., między nimi szczeliny ~2 mm otwarte od dołu (wentylacja) | wg notes.md; kształt do zaprojektowania |
| Słupki śrub | Ø6 × 7 wystające spod daszka, w (±31; ±31) | otwory nieprzelotowe w daszku, tulejki wtapiane M2,5 |
| Materiał | PETG, druk własny | |
| Mocowanie daszka do korpusu | **nierozstrzygnięte** (otwarte w notes.md) | |

## 4. Płytka główna PCB1

### 4.1 Obrys, położenie, otwory

- Obrys 80,0 × 80,0 (STEP: 79,974, tolerancja eksportu), narożniki R1, grubość 1,6.
- Położenie: X, Y ∈ [−40; 40]. **Z 70,4 (dolna powierzchnia) … 72,0 (górna, oparta o słupki)**. Do wewnętrznej ścianki zostaje 1,0 mm z każdej strony.
- Otwory montażowe NPTH Ø2,7 (pod M2,5) w **(−31; −31), (31; −31), (31; 31), (−31; 31)**. Wartości symetryczne, więc są identyczne w obu układach.
- Inne otwory w płytce (THT, przelotki) nie mają znaczenia dla obudowy.

### 4.2 Szczeliny na wypustki płytek LED (NPTH, owalne, szerokość 1,8)

Część prosta szczeliny = wypustka + 0,2 mm luzu. Wypustka A ma 10 mm i jest zasilająca, wypustka B ma 8 mm (dane).
Różne długości kluczują płytkę: odwrócona nie wejdzie.

| Gniazdo | Szczelina A 12,0 × 1,8: środek | Szczelina B 10,0 × 1,8: środek | Oś długa | Płytka LED świeci w stronę |
|---|---|---|---|---|
| LB1 | (−25; −37) | (23; −37) | X | **Y−** |
| LB2 | (37; −25) | (37; 23) | Y | **X+** |
| LB3 | (25; 37) | (−23; 37) | X | **Y+** |
| LB4 | (−37; 25) | (−37; −23) | Y | **X−** |

Wokół szczelin na obu stronach PCB1 są pady lutownicze (±1,8 od osi szczeliny, wys. 1,2). Wypustka wystaje nad górną powierzchnię PCB1
o **1,0 mm (do Z 73,0)**, do tego dochodzi lut. W pasie |X| lub |Y| = 34,5…39,5 przy szczelinach po stronie daszka nie może być żadnej części obudowy.

### 4.3 Strona W DÓŁ (EasyEDA TOP, pod płytką): elementy i wysokości

Wysokość liczysz od dolnej powierzchni PCB1 (Z = 70,4) w dół. Bbox podany w układzie lampki (patrz rys. 3, lewy).

| Element | X | Y | Z | Wys. | Źródło |
|---|---|---|---|---|---|
| **U3** ESP32 MiniKit (tylko w 1. lampce łańcucha), obwiednia | −33,5 … −2,5 | −26,5 … 12,5 | 54,40 … 70,40 | 16,0 | **SZACUNEK** (p. 8) |
| **J1** KF235-3.81 4×2P, WEJŚCIE, obwiednia | −16,0 … 16,0 | 18,2 … 31,8 | 55,40 … 70,40 | 15,0 | **SZACUNEK** (model LCSC 14,8) |
| **J2** KF235-3.81 4×2P, WYJŚCIE, obwiednia | 18,2 … 31,8 | −15,8 … 16,2 | 55,40 … 70,40 | 15,0 | **SZACUNEK** |
| C1 elektrolit 8×10,5 | −0,6 … 8,6 | 0,4 … 9,6 | 60,35 … 70,40 | 10,1 | model |
| C5 elektrolit | 15,9 … 25,1 | −32,1 … −22,9 | 60,35 … 70,40 | 10,1 | model |
| C8 elektrolit | −1,3 … 7,8 | −34,6 … −25,4 | 60,35 … 70,40 | 10,1 | model |
| TP1 | −1,6 … 1,6 | −3,6 … −0,4 | 62,07 … 70,40 | 8,3 | model |
| TP2 | 7,4 … 10,6 | −10,1 … −6,9 | 62,07 … | 8,3 | model |
| TP3 | −17,6 … −14,4 | −34,4 … −31,2 | 62,07 … | 8,3 | model |
| TP4 | −0,6 … 2,6 | −12,1 … −8,9 | 62,07 … | 8,3 | model |
| TP5 | −18,1 … −14,9 | 14,4 … 17,6 | 62,07 … | 8,3 | model |
| TP6 | 28,4 … 31,6 | 16,4 … 19,6 | 62,07 … | 8,3 | model |
| TP7 | −21,6 … −18,4 | 26,9 … 30,1 | 62,07 … | 8,3 | model |
| TP8 | 7,4 … 10,6 | −14,1 … −10,9 | 62,07 … | 8,3 | model |
| TP9 | 27,9 … 31,1 | −25,6 … −22,4 | 62,07 … | 8,3 | model |
| TP10 | −19,6 … −16,4 | 20,4 … 23,6 | 62,07 … | 8,3 | model |
| TP11 | 17,4 … 20,6 | 20,4 … 23,6 | 62,07 … | 8,3 | model |

Dodatkowe dane o złączach i module ESP:
- **Tory J1 w układzie lampki:** 8 torów w X = −13,34 / −9,53 / −5,72 / −1,91 / 1,91 / 5,72 / 9,53 / 13,34 (raster 3,81).
  Kolejność: DANE, GND ×4, +12V ×3. Otwory w dwóch rzędach, Y = 22,5 i 27,5.
- **Tory J2:** otwory w X = 22,5 i 27,5, tory w Y = 13,54 (DANE), 9,73 / 5,92 / 2,11 / −1,70 (GND), −5,51 / −9,32 / −13,13 (+12V).
- **Listwy U3** (2×10, raster 2,54): X = −29,43 i −6,57, Y od −18,43 do 4,43. Pin 1 w (−29,43; −18,43), czyli na końcu anteny.
- **USB ESP32** jest na końcu modułu Y ≈ +12,5 i wychodzi w kierunku +Y, w stronę J1. Szczegóły w p. 6.6.

Najniższy punkt całej elektroniki: **Z ≈ 54,4** (U3, szacunek). Bez U3, czyli w lampkach bez ESP: Z ≈ 55,4 (J1/J2, szacunek), a z samych modeli: 56,0 (dół płytek LED).

### 4.4 Strona DO DASZKA (EasyEDA BOTTOM, nad płytką): elementy i wysokości

Wysokość liczysz od górnej powierzchni PCB1 (Z = 72,0) w górę. Spód daszka jest na Z = 79,0, więc dostępne jest 7,0 mm (rys. 3, prawy).

| Element | X | Y | Z | Wys. | Źródło |
|---|---|---|---|---|---|
| **U1** Mini560 Pro (5 V LED), obwiednia | −4,9 … 25,1 | −32,5 … −14,5 | 72,0 … 77,4 | 5,4 | **SZACUNEK** (model EasyEDA ma 1,9, to uproszczona płytka) |
| **U2** Mini560 Pro (5 V ESP), obwiednia | −27,0 … −9,0 | −22,0 … 8,0 | 72,0 … 77,4 | 5,4 | **SZACUNEK** |
| Q1 TO-252 | 5,7 … 12,3 | 10,4 … 20,4 | … 74,34 | 2,3 | model |
| Q2 TO-252 | 13,7 … 20,3 | −7,9 … 2,1 | … 74,34 | 2,3 | model |
| D1 SMB | 3,6 … 9,0 | 2,4 … 6,0 | … 74,10 | 2,1 | model |
| D4 SMB | −13,4 … −8,0 | −32,0 … −28,4 | … 74,10 | 2,1 | model |
| U4 SOIC-14 | −6,8 … 1,8 | 14,0 … 20,0 | … 74,00 | 2,0 | model |
| C2, C3, C6, C7, C9–C15 (1206) | patrz `wymiary.json` | | … 73,30 | 1,3 | model |
| C6 (najbliżej słupka) | 26,0 … 27,6 | −29,9 … −26,6 | … 73,30 | 1,3 | model |
| D2, D3, Q3, F1, F2, ZD1, ZD2, R1–R12 | patrz `wymiary.json` | | ≤ 73,1 | ≤ 1,1 | model |
| JP1 zworka lutownicza (pady) | −5,3 … −2,8 | ~11,0 | płaska | ~0 | dane |
| Wyprowadzenia THT (J1, J2, U3, TP1–TP11) | nad swoimi padami | | do ~73,6…74,0 | ≤ 2,0 | model TP 1,6; KF235 1,9; listwy U3 po przycięciu **DO ZMIERZENIA** |
| Wypustki płytek LED + lut | przy szczelinach (p. 4.2) | | do ~73,5 | ~1,5 | dane |

**Wniosek dla daszka:** pod całym obrysem 80×80, z wyjątkiem 4 słupków, spód daszka nie może schodzić poniżej ~Z 78
(Mini560 szac. 77,4 + luz). Żeber i napisów wypukłych po wewnętrznej stronie daszka nie dawaj niżej niż ~1 mm od jego spodu.

## 5. Płytki LED PCB2 (4 identyczne)

### 5.1 Obrys (układ lokalny, `wymiary.json → plytki_LED_PCB2.obrys_lokalny_wielokat`)

- Korpus 73,6 × 14,4 (x_l −36,8…36,8; y_l 0…14,4), grubość 1,6.
- **Wypustka A** (5V, GND): x_l −29…−19 (10 mm), y_l 14,4…17,0 (2,6 mm).
- **Wypustka B** (DIN, DOUT): x_l 20…28 (8 mm), y_l 14,4…17,0.
- Odciążenia 1×1 mm przy nasadach: x_l −30…−29, −19…−18, 19…20, 28…29 dla y_l 13,4…14,4.
- Wypustka przechodzi przez PCB1 (1,6) i wystaje 1,0 mm.
- Brzegi z panelu (mouse bites) mogą mieć zadziorki ~0,3 mm.

### 5.2 Diody

- SKC6812RGBW, obudowa 5050, 10 szt. w jednym rzędzie na **y_l = 4,45**.
- Położenie wzdłuż płytki: x_l = 32,143 / 25,0 / 17,857 / 10,714 / 3,571 / −3,571 / −10,714 / −17,857 / −25,0 / −32,143 (skok 7,143).
- Korpus 5,0 × 4,9, wysokość nad płytką **1,627** (model 3D; notes: 1,65). Na płytce: y_l 1,95…6,95.
- Świecą prostopadle do płytki (główna oś wzdłuż z_l, na zewnątrz lampki).
- Inne elementy od strony diod (0603, 0805) nie przekraczają 1,3 mm, czyli są niższe od diod.
- Tył płytki (strona do środka lampki) nie ma elementów: to miedź GND, która działa jako radiator.
  Można tam przykleić pasek Al ≤ 1 mm na izolującej taśmie termoprzewodzącej, maks. 12,4 mm wysokości. W złożeniu go nie ma.

### 5.3 Złożenie płytek LED (układ lampki)

| Gniazdo | Lico wewn. / zewn. | Zakres wzdłuż | Z | Czoło diod | Środki diod (LED1 … LED10) |
|---|---|---|---|---|---|
| LB1 (świeci Y−) | Y = −36,2 / −37,8 | X −37,8 … 35,8 | 56,0 … 70,4 (+ wypustki do 73,0) | Y = −39,43 | X = 31,14 → −33,14, co 7,143 |
| LB2 (świeci X+) | X = 36,2 / 37,8 | Y −37,8 … 35,8 | jw. | X = 39,43 | Y = 31,14 → −33,14 |
| LB3 (świeci Y+) | Y = 36,2 / 37,8 | X −35,8 … 37,8 | jw. | Y = 39,43 | X = −31,14 → 33,14 |
| LB4 (świeci X−) | X = −36,2 / −37,8 | Y −35,8 … 37,8 | jw. | X = −39,43 | Y = −31,14 → 33,14 |

- **Wiatraczek:** każda płytka jednym końcem dochodzi do lica zewnętrznego sąsiadki (np. LB1 kończy się na X = −37,8 = lico zewn. LB4),
  a drugim zostawia **0,41 mm szczeliny** do lica wewnętrznego drugiej sąsiadki. Zweryfikowane w złożeniu, bez przecięć.
- **Linia diod: Z = 60,45.** Korpusy diod: Z 57,95…62,95.
- Względem pasa transparentnego (Z 39…79): linia diod jest 21,45 nad dolną krawędzią pasa i 18,55 pod górną.
  Całe płytki LED (Z 56…70,4) i płytka główna (Z 70,4…72) mieszczą się w pasie.
- **Czoło diod → wewnętrzna ścianka: 1,57 mm** (41 − 39,43). Do zewnętrznej powierzchni ścianki: 5,57 mm.
- Końce płytek LED są 3,2 mm od ścianek bocznych (|37,8| wobec 41).

## 6. Interfejsy mechaniczne dla obudowy

### 6.1 Słupki śrub i mocowanie płytki głównej
- 4 słupki **Ø6 × 7** od spodu daszka (Z 79) do Z 72,0, osie w (±31; ±31). Pełnią też funkcję jedynego podparcia PCB1:
  górna powierzchnia płytki opiera się o czoła słupków.
- Tulejki wtapiane M2,5 w otworach nieprzelotowych. Śruby M2,5 wkręcasz od dołu, łeb jest po stronie elementów (Z 70,4 w dół).
  Długość ≈ 1,6 + wkręcenie w tulejkę; np. M2,5×6 dla tulejki 4 mm, dobierz do tulejki.
- **Ograniczenie średnicy słupka:** słupek w **(31; −31)** ma tylko **0,60 mm** odstępu do C6 (1206, wys. 1,3) po stronie daszka.
  Maksymalna średnica w tym miejscu to ~Ø6,6 bez luzu, więc zostań przy Ø6. Pozostałe odstępy słupków:
  ≥ 2,3 mm do wypustek LED, 6,8 mm do U2 (−31; −31), 10–15 mm od innych elementów.
- Ścianka słupka Ø6 z tulejką M2,5 (otwór ~Ø3,2–4,0) ma 1–1,4 mm: dobierz krótką/wąską tulejkę albo wzmocnij słupek od strony daszka,
  np. stożkiem lub żebrem nad Z 77,5, poza strefą Mini560.
- **Łby śrub** (sprawdzone jako Ø5 × 2 pod płytką): odstęp 2,7 mm do płytek LED, 2,0 mm do obwiedni U3 w (−31; −31), ≥ 3,1 mm do TP.
  Przy (−31; −31) wg przeglądu PCB pod łbem biegnie ścieżka V5LED, a obok jest antena ESP.
  **Zalecenie: łeb ≤ Ø4,5 z podkładką nylonową albo śruba nylonowa w (−31; −31).**

### 6.2 Luz w ściankach
- PCB1 do wewnętrznej ścianki: 1,0 mm na stronę. Najdalej wysunięte punkty elektroniki: ±39,99 (krawędź PCB1).
- Czoło diod do ścianki: 1,57 mm. Końce płytek LED: 3,2 mm.
- Na ściankach w strefie Z 54…79 nie dawaj żadnych występów do wnętrza (poniżej |41|) ani zaczepów, żeby elektronika przeszła przy montażu.
  Wyjątek to elementy z zapasem > 1,5 mm poza płytkami LED, np. prowadnice w narożnikach powyżej 72.
- Jeśli korpus nasuwasz na elektronikę przykręconą do daszka, górna krawędź korpusu przechodzi wzdłuż całej elektroniki.
  Ograniczniki słupka (Z 25) są poniżej najniższego punktu (54,4), więc nie kolidują.

### 6.3 Słupek 80×80
- Wierzch słupka Z = 25. Najniższy punkt elektroniki Z ≈ 54,4, więc **29,4 mm wolnej przestrzeni** nad słupkiem na przewody.
- **Do potwierdzenia:** czy słupek jest pusty w środku i czy kable Cat5e wychodzą z jego wierzchu wewnątrz obrysu (notes.md tego nie precyzuje).

### 6.4 Kable i dostęp do zacisków J1/J2
- Kable wchodzą od dołu (Z < 25) w obrys wnętrza, między płytkami LED (wnętrze pierścienia |X|, |Y| < 36,2 dla Z ≥ 56),
  i dochodzą do zacisków poziomo **od strony środka płytki**: do J1 w kierunku −Y (lico wejścia Y ≈ 18,2), do J2 w kierunku −X (lico X ≈ 18,2).
- **Wolne miejsce przed J1** (kierunek −Y, pas X −16…16, Z 55–70):
  - X −16…−2,5 (tory DANE, GND, GND): **5,7 mm** do ESP (U3). W lampkach bez ESP: > 25 mm.
  - X −0,6…8,6: 8,6 mm do C1.
  - X 8,6…16: > 25 mm.
  - TP5 wchodzi 1,1 mm w skrajny pas (X −16…−14,9, 0,6 mm przed obwiednią), już poza osią skrajnego toru (X −13,34).
  - Przewody przy ESP trzeba od razu zagiąć w dół (−Z). Pod J1 i U3 do słupka jest ~30 mm.
- **Wolne miejsce przed J2** (kierunek −X, pas Y −15,8…16,2): 7,6 mm do TP2 i TP8 (Y −14…−7), 9,6 mm do C1 (Y 0,4…9,6), dalej ≥ 15 mm.
- **Przyciski/dźwignie zacisków** KF235 są od strony przeciwnej do płytki, czyli od dołu lampki.
  Dostęp jest od spodu przez wnętrze 82×82, 55–70 mm od dolnej krawędzi obudowy, gdy lampka jest zdjęta ze słupka.
  Szczegóły zacisku (kierunek wejścia przewodu, położenie przycisku): **DO ZMIERZENIA**.

### 6.5 Wentylacja i ciepło
- Przy pełnej jasności diody wydzielają ~8 W; płytki LED stoją w pasie Z 56–70.
- PCB1 zamyka przekrój nad płytkami LED. Zostaje tylko ~1 mm szczeliny obwodowej (≈ 320 mm²) i luzy w szczelinach wypustek,
  więc ciepłe powietrze gromadzi się pod PCB1.
- Wg notes.md: szczeliny ~2 mm między 6 przewężeniami trzymającymi słupek, otwarte od dołu. Rozważ też otwory w górnej części korpusu
  lub pod okapem daszka (Z ~74–79), bez szkody dla wyglądu. To decyzja projektanta obudowy, niezweryfikowana termicznie.

### 6.6 Antena ESP32 i USB (tylko lampka z ESP)
- Antena modułu jest na końcu **Y −26,5…−20, X −33,5…−2,5, Z ~54–70** (strefa bez miedzi na PCB1).
  W jej pobliżu nie dawaj metalu: wkładek, blaszek, ekranów, radiatora Al na LB4/LB1.
- Już w projekcie w pobliżu anteny są: masa płytki LB4 (lico wewn. X −36,2, 2,7 mm od obrysu modułu), LB1 (Y −36,2, 9,7 mm)
  oraz śruba i tulejka w (−31; −31), ~4,5 mm. Stąd zalecenie śruby nylonowej w tym narożniku. Wpływ na zasięg: niezweryfikowany.
- Port USB ESP jest na przeciwnym końcu modułu (Y ≈ +12,5), skierowany w +Y, i ma przed sobą tylko 5,7 mm do J1.
  **Dostęp do USB z zewnątrz nie jest wymagany** (USB nie wolno podłączać przy zasilaniu 12 V). Programowanie odbywa się przed montażem albo przez Wi-Fi (OTA).
  Dokładna pozycja gniazda: **DO ZMIERZENIA**.

## 7. Złożenie: pliki i weryfikacja

- `elektronika_zlozenie.step` / `.FCStd` zawierają:
  - `PCB1_glowna` (płytka + modele elementów);
  - `PCB2_LED_w_LB1…LB4`;
  - `Obwiednie_bez_modeli_3D` z prostopadłościanami: U3 (H16, szacunek), J1/J2 (H15), U1/U2 Mini560 (H5,4, szacunek).
  
  Warstwy miedzi i sitodruku usunięto. Modele U1/U2 z EasyEDA (1,9 mm) zostały, obwiednie je obejmują.
- **Bounding box całego zespołu:** X −39,99…39,99; Y −39,99…39,99; **Z 54,4…77,4** (bez szacunków: Z 56,0…74,34).
  Strona w dół: X −33,5…31,8, Y −34,6…31,8, Z 54,4…70,4 (+ płytki LED do obrysu ±39,43). Strona daszka: Z 72,0…77,4.
- **Kolizje brył (FCStd/STEP, `skrypty/weryfikuj_zlozenie.py`): brak.** Sprawdzono:
  - płytki LED parami;
  - płytki LED z PCB1 (wypustki w szczelinach: wspólna objętość 0, min. odstęp 0,013);
  - płytki LED z elementami PCB1;
  - obwiednie z modelami.

Najmniejsze odstępy (bryła do bryły, `skrypty/weryfikacja_wyniki.json`):

| Para | Odstęp |
|---|---|
| Płytki LED w narożnikach wiatraczka | 0,41 |
| Słupek Ø6 (31; −31) ↔ C6 (strona daszka) | **0,60** |
| Tył LB1 ↔ TP3 / C8 | **1,85 / 2,05** (radiator 1 mm + taśma zostawia ~0,6–0,8) |
| Tył LB4 ↔ obwiednia ESP U3 | 2,7 |
| Tył LB2 ↔ J2 (obwiednia), LB3 ↔ J1 | 4,4 |
| Słupki Ø6 ↔ wypustki LED | 2,3 / 2,7 |
| Łeb Ø5 ↔ płytki LED / U3 | 2,7 / 2,0 |
| J1 ↔ U3 (przewody) | 5,7 |
| Zespół ↔ wewnętrzna ścianka | 1,0 (PCB1), 1,57 (czoło diod) |
| Zespół ↔ wierzch słupka (Z 25) | 29,4 |
| Zespół ↔ spód daszka (Z 79) | 1,6 (przy Mini560 5,4 szac.); 4,66 wg modeli |

## 8. DO ZMIERZENIA / NIEZWERYFIKOWANE

1. **Mini560 Pro (U1, U2): rzeczywista wysokość** nad PCB1. Szacunek 5,4 pochodzi z `calc/geometria.py` (źródło nieudokumentowane),
   model EasyEDA ma tylko 1,9. Decyduje o luzie pod daszkiem (7,0 dostępne).
2. **ESP32 MiniKit (U3):**
   - sposób montażu: kołki wlutowane bezpośrednio (~7,5 mm) czy gniazda + kołki (~15–16 mm; w złożeniu przyjęto 16);
   - rzeczywisty obrys 31×39 i jego położenie względem listew (przyjęto wyśrodkowanie, szacunek z footprintu);
   - położenie gniazda USB i anteny;
   - długość kołków wystających nad PCB1.
3. **KF235-3.81 (J1, J2):**
   - wysokość (model LCSC C9900023269: 14,8), głębokość (12,55 + możliwe przesunięcie 0,8 względem rzędów otworów);
   - kierunek wejścia przewodu, położenie i kierunek przycisku, miejsce na narzędzie;
   - promień gięcia żył Cat5e.
4. Punkty testowe TP1–TP11: wysokość 8,3 wg modelu EasyEDA TESTPOINT-TH_BD3.2; rzeczywista część niepotwierdzona.
5. Elektrolity C1/C5/C8: 10,05 wg modelu (seria 8×10,5).
6. Dioda SK6812: 1,627 wg modelu, 1,65 wg notes.md; ±0,05 zmienia odstęp czoła od ścianki.
7. Radiator na tyle płytek LED: grubość z taśmą; przy LB1 jest tylko 1,85 mm do TP3 i 2,05 do C8.
8. Wymiary słupka rzeczywistego (80×80 ± ?), czy jest pusty i skąd wychodzą kable.
9. Wymiary śrub, łbów i tulejek M2,5 (przyjęto łeb Ø5 × 2).
10. Rozproszenie światła przy 1,57 mm od diody do ścianki: test „taśma za transparentną ścianką 5/10/15/20 mm” jest otwarty w notes.md.
11. Mocowanie daszka do korpusu: nierozstrzygnięte.
12. Nieaktualne stałe w `calc/geometria.py` (TALLEST_PART 17 dla WAGO, stare płytki LED 18,6 mm). Ten dokument ma pierwszeństwo.

## 9. Pliki

| Plik | Zawartość |
|---|---|
| `WYMIARY.md` | ten dokument |
| `wymiary.json` | dane maszynowo: układ i transformacje, obudowa, PCB1 (otwory, szczeliny, wszystkie elementy z bbox w układzie lampki i wysokością), PCB2 (wielokąt obrysu, wypustki, diody, położenia 40 diod w lampce), złożenie i odstępy |
| `elektronika_zlozenie.step` | złożenie w układzie lampki (do importu w FreeCAD) |
| `elektronika_zlozenie.FCStd` | to samo jako dokument FreeCAD |
| `rys1_widok_z_gory.png` | widok z góry: obudowa, słupek, PCB1, płytki LED, szczeliny, otwory, słupki, ESP, zaciski, antena, kierunek przewodów |
| `rys2_przekroj.png` | przekrój pionowy X = 0 z poziomami Z |
| `rys3_strefy_wysokosci.png` | mapy wysokości elementów po obu stronach PCB1 |
| `PCB1_glowna.step`, `PCB2_LED.step` | oryginalne eksporty EasyEDA (współrzędne EasyEDA) |
| `skrypty/zloz_elektronike.py` | budowa złożenia (freecadcmd) |
| `skrypty/weryfikuj_zlozenie.py` → `skrypty/weryfikacja_wyniki.json` | weryfikacja złożenia: bboxy, kolizje, odstępy |
| `skrypty/dokumentacja.py` | `wymiary.json` + rysunki (`python3`) |
| `skrypty/zbadaj_step.py` → `skrypty/step_obiekty.json` | spis obiektów w STEP-ach EasyEDA |

Kolejność ponownego generowania: `zloz_elektronike.py` → `weryfikuj_zlozenie.py` → `dokumentacja.py`.
Dwa pierwsze uruchamiasz przez `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c "exec(open('…').read())"` z katalogu `skrypty/`.
