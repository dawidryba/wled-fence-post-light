"""
Obudowa lampki na słupek 80×80 (elektronika: PCB1 80×80 + 4× PCB2 LED „wiatraczek").

Uruchom: /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd build.py

Dane wejściowe: ~/Projekty/pcb/lampka-slupek/obudowa_3d/WYMIARY.md (+ elektronika_zlozenie.step).
Układ lampki: Z w górę, Z=0 dolna krawędź korpusu, X/Y od osi lampki.

JEDEN WYDRUK PETG (korpus + daszek), drukowany DASZKIEM NA STOLE. AMS, 3 strefy poziome
(jedna warstwa = jeden kolor): czarny dół Z 0…39, transparentny pas Z 39…79 (ze słupkami PCB),
czarny daszek Z 79…83. Eksport: 3 STL = części jednego obiektu.
  - przewężenia (żebra) Z 0…25 trzymające słupek, faza wejściowa od dołu,
  - ogranicznik słupka: 4 drukowane kliny wsuwane od dołu w rowki na jaskółczy ogon w narożnikach, PO włożeniu
    elektroniki (PCB1 ma ten sam obrys co słupek, więc stały ogranicznik by ją zablokował). Z zewnątrz nic nie widać,
  - 4 słupki Ø6×7 pod PCB1 (tulejki wtapiane M2,5); elektronikę wkłada się od dołu,
  - rowki odpowietrzające 1 mm od spodu daszka, do jego krawędzi (widoczne tylko od dołu).
"""

import os
import FreeCAD as App
import Part
import Import
import MeshPart

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORTS = os.path.join(HERE, "exports")
STEP = next(p for p in (os.path.join(HERE, "..", "pcb", "step", "electronics_assembly.step"),
                        os.path.expanduser("~/Projekty/pcb/lampka-slupek/obudowa_3d/elektronika_zlozenie.step")) if os.path.exists(p))

# ---------------------------------------------------------------------------
# Parametry (mm)
# ---------------------------------------------------------------------------
OUT = 90.0              # obrys korpusu
WALL = 4.0
H_BODY = 79.0           # korpus Z 0…79
Z_COLOR = 39.0          # granica czarny dół / transparentny pas

ROOF = 100.0
ROOF_T = 4.0            # daszek Z 79…83

POST = 80.0             # słupek ogrodzeniowy
Z_STOP = 25.0           # wierzch słupka opiera się o łby wkrętów

# Przewężenia trzymające słupek (Z 0…Z_STOP)
RIB_OFFSETS = (-20.0, 20.0)   # położenia żeber na każdej ścianie (od osi ściany)
RIB_W = 8.0
RIB_GAP = 0.25          # luz żebro ↔ słupek na stronę
RIB_LEAD = 2.0          # wysokość fazy wejściowej od dołu

# Kliny-ograniczniki: wysokość daszka, więc drukują się w jego czarnych warstwach, bez dodatkowych zmian koloru
WEDGE_H = ROOF_T
WEDGE_LEG = 10.0        # przyprostokątna przy ściance: zaokrąglony narożnik słupka też się oprze
WEDGE_GAP = 0.1         # luz w rowku i do ścianek
SLOT_NECK = 2.4         # szerokość rowka przy wnętrzu
SLOT_WIDE = 3.4         # szerokość na dnie
SLOT_DEPTH = 2.2        # głębokość po przekątnej narożnika

# Słupki pod PCB1
PCB_POST_XY = 31.0
PCB_POST_D = 6.0
PCB_TOP_Z = 72.0
INSERT_D = 3.3          # tulejka wtapiana M2,5
INSERT_DEPTH = 5.0

# Odpowietrzenie (para ze słupka): rowki od spodu daszka, od wnętrza do krawędzi daszka
# (nad ścianką tworzą kanał 1 mm, widoczne tylko od dołu). Ściany X− i X+.
VENT_H = 1.0
VENT_Y = ((8.0, 30.0), (-30.0, -8.0))


# ---------------------------------------------------------------------------
def box(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, App.Vector(x0, y0, z0))


def cyl(x, y, z0, z1, d):
    return Part.makeCylinder(d / 2.0, z1 - z0, App.Vector(x, y, z0))


def rot4(shape):
    """Kopie obrócone o 0/90/180/270° wokół Z, zsumowane."""
    out = shape
    for a in (90, 180, 270):
        s = shape.copy()
        s.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), a)
        out = out.fuse(s)
    return out


def clean(s):
    return s.removeSplitter()


# ---------------------------------------------------------------------------
# Lampka (jedna bryła)
# ---------------------------------------------------------------------------
e, i, r = OUT / 2.0, OUT / 2.0 - WALL, ROOF / 2.0
lamp = box(-e, -e, 0, e, e, H_BODY).cut(box(-i, -i, 0, i, i, H_BODY))
lamp = lamp.fuse(box(-r, -r, H_BODY, r, r, H_BODY + ROOF_T))

# żebro na ścianie X+: przekrój XZ z fazą wejściową, wyciągnięty wzdłuż Y
xr = POST / 2.0 + RIB_GAP
rib_w = Part.makePolygon([App.Vector(i + 0.5, 0, 0), App.Vector(i + 0.5, 0, Z_STOP), App.Vector(xr, 0, Z_STOP),
                          App.Vector(xr, 0, RIB_LEAD), App.Vector(i, 0, 0), App.Vector(i + 0.5, 0, 0)])
rib = Part.Face(rib_w).extrude(App.Vector(0, RIB_W, 0))
feat = None
for o in RIB_OFFSETS:
    rb = rib.copy()
    rb.translate(App.Vector(0, o - RIB_W / 2.0, 0))
    feat = rb if feat is None else feat.fuse(rb)

lamp = lamp.fuse(rot4(feat))


def diag_prism(pts, z0, z1):
    """Graniastosłup w narożniku (+,+): u po przekątnej od narożnika wnętrza, v w poprzek."""
    k = 2 ** 0.5 / 2.0
    xy = [App.Vector(i + (u + v) * k, i + (u - v) * k, z0) for u, v in pts]
    return Part.Face(Part.makePolygon(xy + [xy[0]])).extrude(App.Vector(0, 0, z1 - z0))


def dovetail(neck, wide, depth, z0, z1):
    return diag_prism([(-1, -neck / 2.0), (0, -neck / 2.0), (depth, -wide / 2.0), (depth, wide / 2.0), (0, neck / 2.0), (-1, neck / 2.0)], z0, z1)


z_top = Z_STOP + WEDGE_H
lamp = lamp.cut(rot4(dovetail(SLOT_NECK, SLOT_WIDE, SLOT_DEPTH, -1, z_top)))
wc = i - WEDGE_GAP
wedge_body = Part.Face(Part.makePolygon([App.Vector(wc, wc, Z_STOP), App.Vector(wc, wc - WEDGE_LEG, Z_STOP), App.Vector(wc - WEDGE_LEG, wc, Z_STOP),
                                         App.Vector(wc, wc, Z_STOP)])).extrude(App.Vector(0, 0, WEDGE_H - WEDGE_GAP))
wedge = clean(wedge_body.fuse(dovetail(SLOT_NECK - 2 * WEDGE_GAP, SLOT_WIDE - 2 * WEDGE_GAP, SLOT_DEPTH - WEDGE_GAP, Z_STOP, z_top - WEDGE_GAP)))
wedges = rot4(wedge)
for sx in (-1, 1):
    for sy in (-1, 1):
        px, py = sx * PCB_POST_XY, sy * PCB_POST_XY
        lamp = lamp.fuse(cyl(px, py, PCB_TOP_Z, H_BODY + 0.01, PCB_POST_D))
        lamp = lamp.cut(cyl(px, py, PCB_TOP_Z - 1, PCB_TOP_Z + INSERT_DEPTH, INSERT_D))

for y0, y1 in VENT_Y:
    for sx in (-1, 1):
        lamp = lamp.cut(box(min(sx * (i - 0.5), sx * (r + 1)), y0, H_BODY,
                            max(sx * (i - 0.5), sx * (r + 1)), y1, H_BODY + VENT_H))
lamp = clean(lamp)

big = ROOF
zones = {
    "Lampka_czarny_dol": (-1, Z_COLOR),
    "Lampka_pas_transparentny": (Z_COLOR, H_BODY),
    "Lampka_czarny_daszek": (H_BODY, H_BODY + ROOF_T + 1),
}
parts = {n: clean(lamp.common(box(-big, -big, z0, big, big, z1))) for n, (z0, z1) in zones.items()}

# ---------------------------------------------------------------------------
# Elektronika (STEP)
# ---------------------------------------------------------------------------
tmp = App.newDocument("step_tmp")
Import.insert(STEP, tmp.Name)
elec = []   # (etykieta, bryła w układzie lampki, czy PCB1)
for o in tmp.Objects:
    if o.TypeId != "Part::Feature" or not o.Shape.Solids:
        continue
    s = o.Shape.copy()
    s.Placement = o.getGlobalPlacement()
    bb = s.BoundBox
    is_pcb1 = bb.XLength > 79 and bb.YLength > 79 and abs(bb.ZMin - 70.4) < 0.05
    for sol in s.Solids:
        elec.append((o.Label, sol, is_pcb1))
App.closeDocument(tmp.Name)

# ---------------------------------------------------------------------------
# Dokument + eksport
# ---------------------------------------------------------------------------
os.makedirs(EXPORTS, exist_ok=True)
for f in os.listdir(EXPORTS):
    if os.path.isfile(os.path.join(EXPORTS, f)):
        os.remove(os.path.join(EXPORTS, f))
doc = App.newDocument("lampka_slupek")
for name, shp in parts.items():
    doc.addObject("Part::Feature", name).Shape = shp
doc.addObject("Part::Feature", "Elektronika").Shape = Part.makeCompound([s for _, s, _ in elec])
doc.addObject("Part::Feature", "Kliny").Shape = wedges
doc.recompute()
doc.saveAs(os.path.join(EXPORTS, "lampka_slupek.FCStd"))

for name, shp in parts.items():
    m = MeshPart.meshFromShape(Shape=shp, LinearDeflection=0.05, AngularDeflection=0.3)
    m.write(os.path.join(EXPORTS, name.lower() + ".stl"))
lamp.exportStep(os.path.join(EXPORTS, "lampka.step"))
row = []
for n in range(4):
    w = wedge.copy()
    bb = w.BoundBox
    w.translate(App.Vector(-bb.XMin, -bb.YMin + n * 15.0, -bb.ZMin))
    row.append(w)
MeshPart.meshFromShape(Shape=Part.makeCompound(row), LinearDeflection=0.05, AngularDeflection=0.3).write(os.path.join(EXPORTS, "lampka_kliny_x4.stl"))
row[0].exportStep(os.path.join(EXPORTS, "lampka_klin.step"))

# ---------------------------------------------------------------------------
# Weryfikacja
# ---------------------------------------------------------------------------
print("\n=== RAPORT ===")
for name, shp in list(parts.items()) + [("Lampka", lamp)]:
    bb = shp.BoundBox
    print(f"{name}: valid={shp.isValid()} solids={len(shp.Solids)} vol={shp.Volume:.0f} "
          f"bbox X {bb.XMin:.1f}…{bb.XMax:.1f} Y {bb.YMin:.1f}…{bb.YMax:.1f} Z {bb.ZMin:.1f}…{bb.ZMax:.1f}")

# 1) położenie końcowe: kolizje i najbliższe elementy
bad, near = 0, []
for label, sol, _ in elec:
    bb = sol.BoundBox
    bb.enlarge(3.0)
    if not bb.intersect(lamp.BoundBox):
        continue
    d = lamp.distToShape(sol)[0]
    if d < 3.0:
        near.append((d, label))
    if d < 1e-6 and lamp.common(sol).Volume > 1e-3:
        print(f"  KOLIZJA ↔ {label}")
        bad += 1
near.sort()
print("Najbliższe elementy:", ", ".join(f"{d:.2f} {l[:26]}" for d, l in near[:8]))

# 2) montaż: elektronika wkładana od dołu — obrys każdej bryły wyciągnięty od Z=0 do jej góry
#    nie może wchodzić w lampkę (PCB1: pełny kwadrat 80×80; reszta: bbox). Sprawdzam bryły przy ściankach.
insert_bad = 0
for label, sol, is_pcb1 in elec:
    bb = sol.BoundBox
    if is_pcb1:
        sweep = box(-40, -40, 0, 40, 40, bb.ZMax)
    elif max(abs(bb.XMin), abs(bb.XMax), abs(bb.YMin), abs(bb.YMax)) > 33:
        sweep = box(bb.XMin, bb.YMin, 0, bb.XMax, bb.YMax, bb.ZMax)
    else:
        continue
    v = lamp.common(sweep).Volume
    if v > 1e-3:
        print(f"  WKŁADANIE: {label} zahacza ({v:.2f} mm³)")
        insert_bad += 1
print(f"Wkładanie elektroniki od dołu: {'OK' if insert_bad == 0 else 'PROBLEM'}")
print("KOLIZJE:", bad, "| OK" if bad == 0 and insert_bad == 0 else "| PROBLEM")

# 3) kliny: pasują w rowki, słupek opiera się o nie na Z_STOP, rowek nie wychodzi na zewnątrz
post = box(-POST / 2.0, -POST / 2.0, -50, POST / 2.0, POST / 2.0, Z_STOP)
slot_reach = i + (SLOT_DEPTH + SLOT_WIDE / 2.0) * 2 ** 0.5 / 2.0
post_above = box(-POST / 2.0, -POST / 2.0, Z_STOP, POST / 2.0, POST / 2.0, Z_STOP + 1)
print(f"Słupek ↔ lampka: {post.common(lamp).Volume:.3f} mm³ | klin ↔ lampka: {wedges.common(lamp).Volume:.3f} mm³ | klin ↔ słupek: {post.common(wedges).Volume:.3f} mm³")
print(f"Oparcie słupka (ostry narożnik): {post_above.common(wedge).Volume / 1.0:.1f} mm² | ścianka za rowkiem: {e - slot_reach:.2f} mm | rowek do Z {z_top:.1f} (czarny do {Z_COLOR:.0f})")
print(f"Kliny ↔ elektronika: {min(wedges.distToShape(sol)[0] for _, sol, _ in elec if sol.BoundBox.ZMin < 60):.1f} mm | klin: {wedge.Volume:.0f} mm³, valid={wedge.isValid()}, solids={len(wedge.Solids)}")
