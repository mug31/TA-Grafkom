# Animasi tokoh "Debu di Atas Mushaf" sesuai storyboard (12 panel, 24 fps, frame 1-2016).
# Aman dijalankan ulang: animasi tokoh dibersihkan dulu, lalu dikunci ulang.
# Jalankan: blender -b debu_di_atas_mushaf_lengkap.blend --python animasi_tokoh.py -- debu_di_atas_mushaf_lengkap.blend
import bpy, math, os, sys
from mathutils import Vector

R = math.radians
OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
sc = bpy.context.scene
vl = bpy.context.view_layer
O = bpy.data.objects

# ---------- panel (frame awal, dari marker) ----------
P = {m.name: m.frame for m in sc.timeline_markers}
P01, P02, P03, P04, P05, P06 = P["P01"], P["P02"], P["P03"], P["P04"], P["P05"], P["P06"]
P07, P08, P09, P10, P11, P12 = P["P07"], P["P08"], P["P09"], P["P10"], P["P11"], P["P12"]

# posisi & arah awal tiap tokoh (sama dengan generator): x, y, z, rotasi z
ATAS = 21.15
DASAR = {"Rami": (16.9, -0.9, -72), "Abu": (16.9, -2.15, -70), "Bayu": (16.9, -3.45, -66), "Piko": (16.9, -4.5, -64)}
JENDELA = Vector((-2.0, 4.0, 19.0))

# ---------- helper ----------
def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    a = ad.action
    try:
        return list(a.fcurves)
    except Exception:
        return [fc for l in a.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]

def kunci(obj, path, f, nilai, index=-1):
    if index >= 0:
        getattr(obj, path)[index] = nilai
    else:
        setattr(obj, path, nilai)
    obj.keyframe_insert(path, index=index, frame=f)

def pose(root, f, dx=0, dy=0, dz=0, rx=0, ry=0, rz=0, s=(1, 1, 1)):
    """Kunci lokasi/rotasi/skala tokoh relatif terhadap posisi dasarnya."""
    x, y, rzd = DASAR[root.name]
    kunci(root, "location", f, Vector((x + dx, y + dy, ATAS + dz)))
    kunci(root, "rotation_euler", f, Vector((R(rx), R(ry), R(rzd + rz))))
    kunci(root, "scale", f, Vector(s))

MULUT_TERAKHIR = {}
def mulut(tokoh, f, **nilai):
    o = O.get(f"{tokoh}_mulut")
    if not o or o.name not in vl.objects or not o.data.shape_keys:
        return                                  # tokoh tanpa shape key mulut
    kb = o.data.shape_keys.key_blocks
    lalu = MULUT_TERAKHIR.get(tokoh)
    if lalu and f - lalu[0] > 16:               # tahan ekspresi lama, lalu berganti cepat (8 frame)
        for nama in ("senang", "kaget", "sedih"):
            kb[nama].value = lalu[1].get(nama, 0.0)
            kb[nama].keyframe_insert("value", frame=f - 8)
    for nama in ("senang", "kaget", "sedih"):
        kb[nama].value = nilai.get(nama, 0.0)
        kb[nama].keyframe_insert("value", frame=f)
    MULUT_TERAKHIR[tokoh] = (f, nilai)

def tampil(objs, f, muncul):
    for o in objs:
        o.hide_viewport = o.hide_render = not muncul
        o.keyframe_insert("hide_viewport", frame=f)
        o.keyframe_insert("hide_render", frame=f)

def konstan(objs):
    for o in objs:
        for fc in fcurves(o):
            if fc.data_path.startswith("hide"):
                for k in fc.keyframe_points:
                    k.interpolation = 'CONSTANT'

def napas(root, kuat=0.025):
    """Gerak hidup halus (naik-turun), kecuali saat hening panel 8."""
    for fc in fcurves(root):
        if fc.data_path == "location" and fc.array_index == 2:
            for a, b in ((1, P08 + 60), (P09, P11)):
                m = fc.modifiers.new('NOISE')
                m.scale, m.strength, m.phase = 18, kuat, hash(root.name) % 50
                m.use_restricted_range, m.frame_start, m.frame_end = True, a, b
                m.blend_in = m.blend_out = 10

def terbang(root, mulai, akhir, tujuan):
    """Terbang meninggalkan mushaf ke arah cahaya, mengecil, lalu hilang."""
    x, y, _ = DASAR[root.name]
    tengah = Vector((x - 3, y + 1.5, ATAS + 3))
    pose(root, mulai, s=(1, 1, 1))
    d1 = tengah - Vector((x, y, ATAS))
    pose(root, (mulai + akhir) // 2, d1.x, d1.y, d1.z, rx=-10, s=(0.85, 0.85, 0.85))
    d2 = tujuan - Vector((x, y, ATAS))
    pose(root, akhir, d2.x, d2.y, d2.z, rx=-20, s=(0.35, 0.35, 0.35))

# ---------- bersihkan animasi tokoh lama ----------
TOKOH = [O[n] for n in DASAR]
for root in TOKOH:
    for o in [root] + list(root.children_recursive):
        if o.name.startswith(("Piko_Badan", "Piko_Jambul_Utama")):
            continue                                   # animasi bawaan teman tetap
        o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:
            o.data.shape_keys.animation_data.action = None    # keyframe dibuang, driver (lidah Bayu) tetap
        o.hide_viewport = o.hide_render = False

# animasi bawaan Piko (1-160) diulang terus sebagai gerak idle
for n in ("Piko_Badan", "Piko_Jambul_Utama"):
    for fc in fcurves(O[n]):
        if not any(m.type == 'CYCLES' for m in fc.modifiers):
            fc.modifiers.new('CYCLES')

# ======================================================================
# ABU — tertua, gerak lambat & berat
abu = O["Abu"]
pose(abu, 1)
pose(abu, P03 + 30)                                       # masih tidur
pose(abu, P03 + 50, dz=0.05, s=(0.94, 0.94, 1.12))        # menguap: meregang
pose(abu, P03 + 80, dz=0.05, s=(0.94, 0.94, 1.12))
pose(abu, P03 + 100, s=(1.03, 1.03, 0.97))
pose(abu, P03 + 115)
pose(abu, P05 + 15)
pose(abu, P05 + 40, rx=-15, rz=-30)                       # menoleh ke Bayu di jendela
pose(abu, P05 + 110, rx=-12, rz=-10)
pose(abu, P06 + 20, rz=5)                                 # menyambut Bayu, sedikit bangga
pose(abu, P06 + 35, dz=0.25, rz=5, s=(0.95, 0.95, 1.06))
pose(abu, P06 + 48, rz=5, s=(1.06, 1.06, 0.94))
pose(abu, P06 + 60, rz=5, s=(1.04, 1.04, 1.04))
pose(abu, P07 + 110, s=(1.04, 1.04, 1.04))
pose(abu, P07 + 130, rx=-8, s=(1.07, 1.07, 1.07))         # "Benda paling dihormati, dong"
pose(abu, P07 + 200, rx=-8, s=(1.07, 1.07, 1.07))
pose(abu, P08 + 20)
pose(abu, P09 + 100)
pose(abu, P09 + 170, rx=22, s=(1.0, 1.0, 0.92))           # menunduk sadar
pose(abu, P10 + 5, rx=22, s=(1.0, 1.0, 0.92))
pose(abu, P10 + 14, dz=0.5, s=(0.9, 0.9, 1.15))           # kaget, pintu terbuka
pose(abu, P10 + 24, s=(1.08, 1.08, 0.9))
pose(abu, P10 + 32, rz=-20)
pose(abu, P11 + 40, rz=-20)
terbang(abu, P11 + 45, P12 - 4, JENDELA + Vector((1, 0, 0)))
mulut("Abu", 1)
mulut("Abu", P03 + 40)
mulut("Abu", P03 + 55, kaget=1.0)                         # "Hoaam..."
mulut("Abu", P03 + 85, kaget=1.0)
mulut("Abu", P03 + 105, senang=0.6)                       # "...tenang kayak biasa"
mulut("Abu", P06 + 15, senang=1.0)
mulut("Abu", P07 + 110, senang=0.3)
mulut("Abu", P07 + 125, senang=1.0)
mulut("Abu", P08 + 30)
mulut("Abu", P09 + 120)
mulut("Abu", P09 + 170, sedih=1.0)                        # "Astaghfirullah..."
mulut("Abu", P10 + 8, sedih=1.0)
mulut("Abu", P10 + 14, kaget=1.0)
mulut("Abu", P11 + 25, kaget=1.0)
mulut("Abu", P11 + 45, senang=0.8)                        # "Alhamdulillah... akhirnya"

# ======================================================================
# RAMI — pencatat hari, agak cemas
rami = O["Rami"]
pose(rami, 1)
pose(rami, P04 + 10)
pose(rami, P04 + 25, dx=-0.15, rx=14)                     # condong ke goresan hitungan
for i in range(8):                                        # menggores satu garis
    pose(rami, P04 + 32 + i * 6, dx=-0.15 - 0.05 * (i % 2), rx=14 + 3 * (i % 2))
pose(rami, P04 + 90, dx=-0.15, rx=14)
pose(rami, P04 + 105)
pose(rami, P04 + 115, dz=0.12, s=(0.97, 0.97, 1.04))      # "Hari ke-211, lho"
pose(rami, P04 + 125)
pose(rami, P05 + 18)
pose(rami, P05 + 42, rx=-15, rz=-35)                      # menoleh ke jendela
pose(rami, P05 + 110, rx=-12, rz=-15)
pose(rami, P06 + 30)
pose(rami, P09 + 60)
pose(rami, P09 + 90, rx=10)                               # "Ya pergi..."
pose(rami, P09 + 100, rx=0)
pose(rami, P09 + 110, rx=10, s=(1.0, 1.0, 0.94))
pose(rami, P10 + 8, rx=10, s=(1.0, 1.0, 0.94))
pose(rami, P10 + 16, dz=0.45, s=(0.9, 0.9, 1.12))
pose(rami, P10 + 26, s=(1.06, 1.06, 0.92))
pose(rami, P10 + 34, rz=-20)
pose(rami, P11 + 35, rz=-20)
terbang(rami, P11 + 40, P12 - 8, JENDELA + Vector((0, 0, 1.2)))

# ======================================================================
# PIKO — terkecil, polos; ekspresi lewat 4 set wajah
piko = O["Piko"]
pose(piko, 1)
pose(piko, P04 + 140)
for i, sudut in enumerate((6, -6, 6, -4)):                # melamun, bergoyang pelan
    pose(piko, P04 + 160 + i * 25, ry=sudut, rz=10)
pose(piko, P05 + 10)
pose(piko, P05 + 38, rx=-18, rz=-30)
pose(piko, P05 + 110, rx=-14, rz=-12)
pose(piko, P06 + 25, dz=0.2)
pose(piko, P06 + 35)
pose(piko, P09 + 20)
pose(piko, P09 + 45, rx=8, s=(1.0, 1.0, 0.93))            # "Kalau nanti dibaca lagi..."
pose(piko, P10 + 4, rx=8, s=(1.0, 1.0, 0.93))
pose(piko, P10 + 12, dz=0.6, s=(0.85, 0.85, 1.2))
pose(piko, P10 + 22, s=(1.12, 1.12, 0.88))
pose(piko, P10 + 30, rz=-20)
pose(piko, P11 + 30, rz=-20)
terbang(piko, P11 + 35, P12 - 12, JENDELA + Vector((-1, 0, 0.5)))

WAJAH = {n: [o for o in O if o.name.startswith(f"Piko_{n}_")] for n in ("Normal", "Senang", "Kaget", "Sedih")}
for c in bpy.data.collections["Piko_Utama"].children:     # visibilitas diatur per objek
    c.hide_render = False
    c.hide_viewport = False                               # di file teman set wajah lain dinonaktifkan di viewport
    def cari(lc):
        if lc.name == c.name:
            return lc
        for ch in lc.children:
            r = cari(ch)
            if r:
                return r
    cari(vl.layer_collection).hide_viewport = False
for o in sum(WAJAH.values(), []):
    o.animation_data_clear()

def wajah_piko(f, nama):
    for n, objs in WAJAH.items():
        tampil(objs, f, n == nama)

for f, nama in ((1, "Normal"), (P04 + 160, "Senang"), (P04 + 235, "Sedih"), (P05 + 30, "Normal"),
                (P06 + 20, "Senang"), (P08, "Normal"), (P09 + 30, "Sedih"), (P10 + 10, "Kaget"),
                (P11 + 30, "Senang")):
    wajah_piko(f, nama)
konstan(sum(WAJAH.values(), []))

# ======================================================================
# BAYU — pendatang, gerak cepat & memantul
bayu = O["Bayu"]
bx, by, _ = DASAR["Bayu"]
bagian_bayu = list(bayu.children_recursive)
tampil(bagian_bayu, 1, False)
tampil(bagian_bayu, P05 + 15, True)
def bayu_di(f, posisi, rz=0, rx=0, s=(1, 1, 1)):
    d = posisi - Vector((bx, by, ATAS))
    pose(bayu, f, d.x, d.y, d.z, rx=rx, rz=rz, s=s)
bayu_di(1, JENDELA + Vector((0, 2.0, 0)))
bayu_di(P05 + 15, JENDELA + Vector((0, -1.0, 0)), rz=0)
bayu_di(P05 + 50, Vector((6, -1.0, 24.5)), rz=360, s=(0.9, 0.9, 1.1))   # terbawa angin, berputar
bayu_di(P05 + 90, Vector((13, -4.0, 24.8)), rz=720)
bayu_di(P05 + 125, Vector((bx - 0.6, by - 0.4, ATAS + 1.6)), rz=1040)  # "Assalamu'alaikum..."
bayu_di(P06 + 10, Vector((bx, by, ATAS + 1.2)), rz=1080)
pose(bayu, P06 + 22, rz=1080, s=(1.3, 1.3, 0.65))                      # mendarat: squash
pose(bayu, P06 + 28, dz=0.3, rz=1080, s=(0.85, 0.85, 1.2))             # stretch
pose(bayu, P06 + 36, rz=1080, s=(1.08, 1.08, 0.93))
pose(bayu, P06 + 44, rz=1080)
# panel 7: melompat ke tepi rak lalu melihat ke bawah
for i, dx in enumerate((-0.35, -0.7, -1.0)):
    f = P07 + 10 + i * 16
    pose(bayu, f, dx=dx + 0.35, rz=1080)
    pose(bayu, f + 8, dx=dx + 0.17, dz=0.35, rz=1080, s=(0.9, 0.9, 1.1))
    pose(bayu, f + 16, dx=dx, rz=1080, s=(1.1, 1.1, 0.9))
pose(bayu, P07 + 70, dx=-1.0, rz=1080)
pose(bayu, P07 + 85, dx=-1.0, rx=28, rz=1080)                          # "Kok ditaruh tinggi banget?"
pose(bayu, P07 + 140, dx=-1.0, rx=28, rz=1080)
pose(bayu, P07 + 160, dx=-1.0, rz=1080)
pose(bayu, P07 + 185, dx=-0.4, dz=0.3, rz=1080)
pose(bayu, P07 + 205, rz=1080)
pose(bayu, P08 + 15, rz=1080 + 30)                                     # menatap Abu, bertanya polos
pose(bayu, P08 + 160, rz=1080 + 30)
pose(bayu, P09 + 60, rz=1080 + 10, s=(1.0, 1.0, 0.95))
pose(bayu, P10 + 6, rz=1080 + 10, s=(1.0, 1.0, 0.95))
pose(bayu, P10 + 13, dz=0.6, rz=1080, s=(0.85, 0.85, 1.2))
pose(bayu, P10 + 22, rz=1080 - 20, s=(1.12, 1.12, 0.88))
pose(bayu, P10 + 30, rz=1080 - 20)
pose(bayu, P11 + 25, rz=1080 - 20)
x0, y0, rz0 = DASAR["Bayu"]
DASAR["Bayu"] = (x0, y0, rz0 + 1060)
terbang(bayu, P11 + 30, P12 - 16, JENDELA + Vector((0.5, 0, -0.5)))
DASAR["Bayu"] = (x0, y0, rz0)
mulut("Bayu", 1)
mulut("Bayu", P05 + 100, senang=1.0)
mulut("Bayu", P07 + 80, kaget=0.8)
mulut("Bayu", P08 + 10)
mulut("Bayu", P09 + 60, sedih=0.5)
mulut("Bayu", P10 + 10, kaget=1.0)
mulut("Bayu", P11 + 30, senang=1.0)
kilau = O.get("Bayu_kilau")                                            # kilau berputar (Bayu versi generator)
if kilau and kilau.name in vl.objects:
    kilau.animation_data_clear()
    kunci(kilau, "rotation_euler", 1, 0.0, index=2)
    kunci(kilau, "rotation_euler", sc.frame_end, R(720), index=2)
    for fc in fcurves(kilau):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'

# semua tokoh hilang setelah terbang (sebelum panel 12)
for root in TOKOH:
    objs = [o for o in root.children_recursive if o.type in ('MESH', 'CURVE') and not o.name.startswith(
        ("Piko_Senang_", "Piko_Kaget_", "Piko_Sedih_", "Piko_Normal_"))]
    tampil(objs, P12 - 2, False)
    if root.name != "Bayu":
        tampil(objs, 1, True)
for n, objs in WAJAH.items():
    tampil(objs, P12 - 2, False)
for root in TOKOH:
    konstan(root.children_recursive)
    napas(root)

# ======================================================================
# LINGKUNGAN: pintu terbuka (panel 10), tangan mengusap & mengangkat mushaf (panel 11)
pintu = O["pintu"]
pintu.animation_data_clear()
kunci(pintu, "rotation_euler", 1, 0.0, index=2)
kunci(pintu, "rotation_euler", P10 + 8, 0.0, index=2)
kunci(pintu, "rotation_euler", P10 + 70, R(-75), index=2)

# Lengan kanan (dibuat oleh lengan_kanan.py): Empty "Tangan" = pergelangan, armature "Lengan_Kanan" = bahu.
# Orang berdiri di depan rak menghadap +x, jadi sisi kanannya ada di -y.
tangan = O["Tangan"]
bahu = O["Lengan_Kanan"]
mushaf = O["mushaf_tertutup"]
for o in (tangan, bahu, mushaf):
    o.animation_data_clear()
m0 = Vector((17.6, -3.0, 20.15))                           # posisi mushaf di rak
mushaf.location = m0
BAHU0 = Vector((13.0, -5.8, 16.4))                         # bahu saat berdiri tegak
JANGKAUAN = 0.93 * 6.6                                     # lengan atas + bawah, sisakan tekukan siku
def tangan_di(f, p, rz=0, rx=0):
    p = Vector(p)
    kunci(tangan, "location", f, p)
    kunci(tangan, "rotation_euler", f, Vector((R(rx), 0, R(rz))))
    d = p - BAHU0                                           # condong/jinjit kalau target terlalu jauh
    kunci(bahu, "location", f, BAHU0 + d.normalized() * (d.length - JANGKAUAN) if d.length > JANGKAUAN else BAHU0)
tangan_di(P11 - 1, (12.2, -5.0, 17.2), -25)                # di luar frame, di bawah
tangan_di(P11 + 30, (15.5, -3.2, 21.9), -10)               # meraih sampul dengan kain
for i in range(4):                                         # mengusap sampul
    tangan_di(P11 + 38 + i * 12, (16.2, -4.6 if i % 2 == 0 else -1.4, 21.75))
tangan_di(P11 + 84, (16.2, -3.0, 21.75))                   # selesai mengelap, lalu cut ke panel 12
tangan_di(P12 - 1, (15.9, -3.0, 22.0))
lengan = [tangan, bahu] + list(tangan.children_recursive) + list(bahu.children_recursive)
tampil(lengan, 1, False)                                   # lengan hanya muncul di panel 11
tampil(lengan, P11 - 1, True)
tampil(lengan, P12, False)
konstan(lengan)
lap = O["lapisan_debu"]
tampil([lap, O["hitungan_rami"]], P11 + 80, False)        # debu & goresan hitungan tersapu bersih
tampil([lap, O["hitungan_rami"]], 1, True)
konstan([lap, O["hitungan_rami"]])

sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SELESAI", OUT)
