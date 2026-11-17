# Animasi tokoh "Debu di Atas Mushaf" sesuai storyboard (12 panel, 24 fps, frame 1-2016).
# Aman dijalankan ulang: animasi tokoh dibersihkan dulu, lalu dikunci ulang.
# Butuh rig dari lengan_kanan.py dan mulut_bicara.py (jalankan keduanya dulu).
# Jalankan: blender -b debu_di_atas_mushaf_lengkap.blend --python animasi_tokoh.py -- debu_di_atas_mushaf_lengkap.blend
import bpy, math, os, re, sys
from mathutils import Vector, Matrix

R = math.radians
OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
sc = bpy.context.scene
vl = bpy.context.view_layer
O = bpy.data.objects

# ---------- panel (frame awal, dari marker) ----------
P = {m.name: m.frame for m in sc.timeline_markers}
FPS = sc.render.fps
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

# ---------- bicara: mulut buka-tutup per suku kata (shape key "buka" dari mulut_bicara.py) ----------
# Belum ada rekaman suara, jadi durasi diperkirakan: bahasa Indonesia santai ±5-6,5 suku kata/detik
# + jeda tanda baca. Kalau dialog tidak muat sampai frame `akhir`, lajunya dinaikkan otomatis.
MULUT_BUKA = {
    "Abu": ["Abu_mulut_Rongga"],
    "Rami": ["Rami_mulut_Rongga"],
    "Piko": ["Piko_Normal_Mulut_1_BibirHitam", "Piko_Normal_Mulut_2_RonggaMarun", "Piko_Kaget_Mulut_1_BibirHitam",
             "Piko_Kaget_Mulut_2_RonggaMarun", "Piko_Senang_Mulut_Rongga", "Piko_Sedih_Mulut_Rongga"],
    "Bayu": ["Bayu_mulut"],
}
VOKAL = {"a": 1.0, "o": 0.8, "e": 0.7, "u": 0.55, "i": 0.5}   # seberapa lebar mulut terbuka
KETUKAN = 6.5                                              # panjang satu buka-tutup mulut (±3,7 per detik)
JEDA = {"...": 10, ".": 7, "?": 7, "!": 7, ",": 4}           # frame mulut terkatup
BIBIR = set("mbpw")                                          # konsonan yang mengatupkan bibir

def suku_kata(teks):
    """Teks -> [("s", vokal, bibir_katup) | ("jeda", frame)]. Diftong ai/au/oi/ei = satu suku kata."""
    hasil = []
    for tok in re.findall(r"\.\.\.|[.,?!]|[a-z'\-]+", teks.lower()):
        if tok in JEDA:
            hasil.append(("jeda", JEDA[tok]))
            continue
        for awal, v in re.findall(r"([^aiueo]*)(ai|au|oi|ei|[aiueo])", tok.replace("'", "").replace("-", "")):
            hasil.append(("s", v[0], bool(BIBIR & set(awal))))
    return hasil

def buka(tokoh, f, nilai):
    for n in MULUT_BUKA[tokoh]:
        kb = O[n].data.shape_keys.key_blocks["buka"]
        kb.value = nilai
        kb.keyframe_insert("value", frame=f)

def bicara(tokoh, mulai, teks, laju=5.5, akhir=None, kuat=1.0):
    """Mulut buka-tutup mulai frame `mulai`: puncak di tengah tiap suku kata, terkatup di jeda
    dan konsonan bibir (m/b/p/w). Kembalikan frame selesai."""
    seg = suku_kata(teks)
    while seg and seg[-1][0] == "jeda":                    # tanda baca penutup tidak makan waktu
        seg.pop()
    n = sum(1 for s in seg if s[0] == "s")
    jeda = sum(s[1] for s in seg if s[0] == "jeda")
    if akhir and mulai + n * FPS / laju + jeda > akhir:
        laju = n * FPS / (akhir - mulai - jeda)
    spf = FPS / laju                                       # frame per suku kata
    # Suku kata dikelompokkan ke ketukan mulut sepanjang KETUKAN frame (±3-4 buka-tutup
    # per detik) supaya mulut tidak "mengepak" tiap suku kata; durasi dialog tetap.
    f = float(mulai)
    ketukan = []                                           # ["s", awal, vokal, katup] atau ["jeda", awal, lama]
    for s in seg:
        if s[0] == "jeda":
            ketukan.append(["jeda", f, s[1]])
            f += s[1]
            continue
        _, v, katup = s
        k = ketukan[-1] if ketukan else None
        blok = int((f - mulai) // KETUKAN)                 # kisi waktu tetap: tempo mulut sama untuk semua
        if k and k[0] == "s" and k[4] == blok and not katup:
            k[2] = max(k[2], v, key=lambda x: VOKAL[x])      # pakai vokal paling terbuka dalam ketukan
        else:
            ketukan.append(["s", f, v, katup, blok])
        f += spf
    buka(tokoh, mulai - 2, 0.0)
    for i, k in enumerate(ketukan):
        akhir_k = ketukan[i + 1][1] if i + 1 < len(ketukan) else f
        if k[0] == "jeda":
            buka(tokoh, k[1] + 2, 0.0)
            buka(tokoh, k[1] + k[2] - 1, 0.0)
            continue
        _, awal, v, katup, _ = k
        buka(tokoh, awal, 0.0 if katup else 0.15 * kuat)
        buka(tokoh, (awal + akhir_k) / 2, VOKAL[v] * kuat * (0.85 + 0.15 * (i * 37 % 7) / 6))
    buka(tokoh, f + 2, 0.0)
    n_k = sum(1 for k in ketukan if k[0] == "s")
    print(f"KETUKAN {tokoh:5} {n_k} ketukan, {n_k / ((f - mulai) / FPS):.1f}/dtk")
    print(f"BICARA {tokoh:5} {mulai}-{round(f)} ({(f - mulai) / FPS:.1f} dtk) {n} suku kata, {laju:.1f}/dtk")
    return round(f)

def menguap(tokoh, mulai, lama, nilai=1.3):
    buka(tokoh, mulai - 2, 0.0)
    buka(tokoh, mulai + 6, nilai * 0.8)
    buka(tokoh, mulai + lama - 6, nilai)
    buka(tokoh, mulai + lama, 0.0)

def terbang(root, mulai, akhir, tujuan):
    """Terbang meninggalkan mushaf ke arah cahaya, mengecil, lalu hilang."""
    x, y, _ = DASAR[root.name]
    tengah = Vector((x - 1.5, y + 1.5, ATAS + 5))           # naik tinggi dulu, tidak lewat lengan pembaca
    pose(root, mulai, s=(1, 1, 1))
    pose(root, mulai + 8, dx=-0.3, dy=0.6, dz=2.8, s=(0.95, 0.95, 1.05))   # melompat kaget
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
pose(abu, P03 + 8)                                        # masih tidur
pose(abu, P03 + 14, dz=0.05, s=(0.94, 0.94, 1.12))        # menguap: meregang
pose(abu, P03 + 30, dz=0.05, s=(0.94, 0.94, 1.12))
pose(abu, P03 + 38, s=(1.03, 1.03, 0.97))
pose(abu, P03 + 48)
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
pose(abu, P09 + 125)
pose(abu, P09 + 150, rx=22, s=(1.0, 1.0, 0.92))           # menunduk sadar
pose(abu, P10 + 5, rx=22, s=(1.0, 1.0, 0.92))
pose(abu, P10 + 14, dz=0.5, s=(0.9, 0.9, 1.15))           # kaget, pintu terbuka
pose(abu, P10 + 24, s=(1.08, 1.08, 0.9))
pose(abu, P10 + 32, rz=-20)
pose(abu, P11 + 23, rz=-20)
terbang(abu, P11 + 28, P12 - 4, JENDELA + Vector((1, 0, 0)))
mulut("Abu", 1)
mulut("Abu", P03 + 60)
mulut("Abu", P03 + 90, senang=0.6)                        # "...tenang kayak biasa"
mulut("Abu", P06 + 15, senang=1.0)
mulut("Abu", P07 + 110, senang=0.3)
mulut("Abu", P07 + 125, senang=1.0)
mulut("Abu", P08 + 30)
mulut("Abu", P09 + 125)
mulut("Abu", P09 + 145, sedih=1.0)                        # "Astaghfirullah..."
mulut("Abu", P10 + 8, sedih=1.0)
mulut("Abu", P10 + 14, kaget=1.0)
mulut("Abu", P11 + 15, kaget=1.0)
mulut("Abu", P11 + 38, senang=0.8)                        # "Alhamdulillah... akhirnya"
menguap("Abu", P03 + 10, 22)                              # "Hoaam..."
bicara("Abu", P03 + 40, "udah pagi lagi, ya. Alhamdulillah, tenang kayak biasa.", laju=5.0, akhir=P04 - 3)
bicara("Abu", P06 + 6, "Wa'alaikumussalam. Masuk aja! Di sini paling aman, nggak ada yang pernah nyentuh.",
       akhir=P07 - 3)
bicara("Abu", P07 + 116, "Ini Al-Qur'an. Benda paling dihormati di rumah ini, dong.", akhir=P08 - 3)
bicara("Abu", P09 + 149, "Astaghfirullah... kita betah di sini justru karena Al-Qur'an ini ditinggalkan.",
       laju=5.0, akhir=P10 + 4)
bicara("Abu", P11 + 40, "Alhamdulillah... akhirnya.", laju=4.5, akhir=P12 - 1, kuat=0.8)

# ======================================================================
# RAMI — pencatat hari, agak cemas
rami = O["Rami"]
pose(rami, 1)
pose(rami, P04 + 2)
# mundur sedikit lalu condong: garis baru tepat di depan Rami, tidak tertutup badannya (shot POV dari atas)
RAMI_MUNDUR = 0.25
pose(rami, P04 + 4, dx=RAMI_MUNDUR, rx=14)                # condong ke goresan hitungan
for i in range(6):                                        # menggores satu garis sambil bicara
    pose(rami, P04 + 8 + i * 6, dx=RAMI_MUNDUR - 0.05 * (i % 2), rx=14 + 3 * (i % 2))
pose(rami, P04 + 40, dx=RAMI_MUNDUR, rx=14)
pose(rami, P04 + 44)
pose(rami, P04 + 50, dz=0.12, s=(0.97, 0.97, 1.04))       # "Hari ke-211, lho" (±P04+47)
pose(rami, P04 + 60)
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
pose(rami, P11 + 19, rz=-20)
terbang(rami, P11 + 24, P12 - 8, JENDELA + Vector((0, 0, 1.2)))
bicara("Rami", P04 + 6, "Hari ke dua ratus sebelas, lho. Terakhir dibuka pas malam dua puluh tujuh Ramadan.",
       laju=6.5, akhir=P04 + 128)
bicara("Rami", P09 + 88, "Ya pergi. Memang harusnya begitu.", laju=6.0, akhir=P09 + 145)

# ======================================================================
# PIKO — terkecil, polos; ekspresi lewat 4 set wajah
piko = O["Piko"]
pose(piko, 1)
pose(piko, P04 + 125)
for i, sudut in enumerate((6, -6, 6, -4)):                # melamun, bergoyang pelan
    pose(piko, P04 + 145 + i * 28, ry=sudut, rz=10)
pose(piko, P05 + 10)
pose(piko, P05 + 38, rx=-18, rz=-30)
pose(piko, P05 + 110, rx=-14, rz=-12)
pose(piko, P06 + 25, dz=0.2)
pose(piko, P06 + 35)
pose(piko, P09 + 2)
pose(piko, P09 + 12, rx=8, s=(1.0, 1.0, 0.93))            # "Kalau nanti dibaca lagi..."
pose(piko, P10 + 4, rx=8, s=(1.0, 1.0, 0.93))
pose(piko, P10 + 12, dz=0.6, s=(0.85, 0.85, 1.2))
pose(piko, P10 + 22, s=(1.12, 1.12, 0.88))
pose(piko, P10 + 30, rz=-20)
pose(piko, P11 + 15, rz=-20)
terbang(piko, P11 + 20, P12 - 12, JENDELA + Vector((-1, 0, 0.5)))

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

for f, nama in ((1, "Normal"), (P04 + 150, "Senang"), (P04 + 213, "Sedih"), (P05 + 30, "Normal"),
                (P06 + 20, "Senang"), (P08, "Normal"), (P09 + 2, "Sedih"), (P10 + 10, "Kaget"),
                (P11 + 20, "Senang")):
    wajah_piko(f, nama)
konstan(sum(WAJAH.values(), []))
bicara("Piko", P04 + 132, "Iya... dulu tiap habis Subuh ada yang ngaji. Sekarang sepi, cuma detak jam.",
       laju=5.3, akhir=P05 - 2, kuat=0.8)                 # pelan
bicara("Piko", P09 + 4, "Kalau nanti dibaca lagi, kita pindah ke mana?", laju=5.3, akhir=P09 + 86, kuat=0.7)  # lirih

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
pose(bayu, P11 + 13, rz=1080 - 20)
x0, y0, rz0 = DASAR["Bayu"]
DASAR["Bayu"] = (x0, y0, rz0 + 1060)
terbang(bayu, P11 + 18, P12 - 16, JENDELA + Vector((0.5, 0, -0.5)))
DASAR["Bayu"] = (x0, y0, rz0)
mulut("Bayu", 1)
mulut("Bayu", P05 + 30, senang=1.0)
mulut("Bayu", P07 + 72, kaget=0.6)                         # heran
mulut("Bayu", P08 + 10)
bicara("Bayu", P05 + 28, "Assalamu'alaikum... boleh numpang, nggak? Di luar anginnya kencang banget.",
       laju=6.0, akhir=P06 - 2)
bicara("Bayu", P07 + 36, "Eh, ini buku apa? Kok ditaruh tinggi banget?", laju=6.0, akhir=P07 + 112, kuat=0.8)
bicara("Bayu", P08 + 20, "Dihormati... tapi kok nggak pernah dibuka?", laju=5.0, akhir=P08 + 110)  # lalu hening
mulut("Bayu", P09 + 60, sedih=0.5)
mulut("Bayu", P10 + 10, kaget=1.0)
mulut("Bayu", P11 + 20, senang=1.0)
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
# LINGKUNGAN: pintu terbuka (panel 10), tangan mengusap debu di mushaf (panel 11), kamera pembuka
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
BAHU0 = Vector((12.4, -5.8, 21.9))                         # bahu setinggi sampul (pembaca naik bangku, rak 2 m), lengan mendatar di atas mushaf
JANGKAUAN = 0.93 * 6.6                                     # lengan atas + bawah, sisakan tekukan siku
def tangan_di(f, p, rz=0, rx=0):
    p = Vector(p)
    kunci(tangan, "location", f, p)
    kunci(tangan, "rotation_euler", f, Vector((R(rx), 0, R(rz))))
    d = p - BAHU0                                           # condong/jinjit kalau target terlalu jauh
    kunci(bahu, "location", f, BAHU0 + d.normalized() * (d.length - JANGKAUAN) if d.length > JANGKAUAN else BAHU0)
tangan_di(P11 - 1, (12.2, -5.0, 17.2), -25)                # di luar frame, di bawah
tangan_di(P11 + 20, (13.6, -5.0, 22.0), -18)               # naik dulu melewati tepi rak
tangan_di(P11 + 30, (15.5, -4.6, 22.0), -10)               # meraih sampul dengan kain
# mengusap bolak-balik tiga baris (dekat, tengah, jauh) supaya seluruh sampul tersapu
for f, x, y, rz in ((38, 15.65, -4.8, -8), (50, 15.65, -1.2, 6), (55, 16.7, -1.2, 6), (65, 16.7, -4.8, -8),
                    (70, 17.75, -4.8, -8), (80, 17.75, -1.2, 6), (86, 16.7, -3.0, 0)):
    tangan_di(P11 + f, (x, y, 21.85), rz)
tangan_di(P11 + 90, (16.3, -3.0, 22.1))                    # selesai mengelap, lalu cut ke panel 12
tangan_di(P12 - 1, (16.0, -3.0, 22.3))
lengan = [tangan, bahu] + list(tangan.children_recursive) + list(bahu.children_recursive)
tampil(lengan, 1, False)                                   # lengan hanya muncul di panel 11
tampil(lengan, P11 - 1, True)
tampil(lengan, P12, False)
konstan(lengan)

# Debu & goresan hitungan hilang per gumpalan tepat saat kain lewat di atasnya:
# tiap gumpalan diberi atribut "waktu_lap" (frame tersapu), Geometry Nodes menghapusnya mulai frame itu.
KAIN_TENGAH, KAIN_SETENGAH = Vector((0.9, 0.0)), 0.85      # jejak kain di bawah telapak (ruang lokal Tangan)
def pulau(me):
    induk = list(range(len(me.vertices)))
    def akar(i):
        while induk[i] != i:
            induk[i] = induk[induk[i]]; i = induk[i]
        return i
    for e in me.edges:
        induk[akar(e.vertices[0])] = akar(e.vertices[1])
    hasil = {}
    for i in range(len(me.vertices)):
        hasil.setdefault(akar(i), []).append(i)
    return list(hasil.values())

ng = bpy.data.node_groups.get("Hapus_Terlap")
if not ng:
    ng = bpy.data.node_groups.new("Hapus_Terlap", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    attr = N.new("GeometryNodeInputNamedAttribute"); attr.data_type = 'FLOAT'; attr.inputs["Name"].default_value = "waktu_lap"
    waktu = N.new("GeometryNodeInputSceneTime")
    cmp = N.new("FunctionNodeCompare"); cmp.data_type = 'FLOAT'; cmp.operation = 'LESS_EQUAL'
    hapus = N.new("GeometryNodeDeleteGeometry"); hapus.domain = 'POINT'
    L.new(gi.outputs[0], hapus.inputs["Geometry"])
    L.new(attr.outputs["Attribute"], cmp.inputs[0])
    L.new(waktu.outputs["Frame"], cmp.inputs[1])
    L.new(cmp.outputs["Result"], hapus.inputs["Selection"])
    L.new(hapus.outputs[0], go.inputs[0])

# Rami menggores garis baru (garis pertama kelompok ke-8) sambil bicara "Hari ke-211": garis memanjang
# pelan selama Rami bergoyang menggores (P04+8 .. P04+38). Bentuknya disalin dari garis tegak yang sudah ada.
hit = O["hitungan_rami"]
baru = O.get("hitungan_baru")
if baru:                                                  # selalu dibangun ulang (aman dijalankan ulang)
    me_lama = baru.data
    bpy.data.objects.remove(baru)
    if me_lama.users == 0:
        bpy.data.meshes.remove(me_lama)
if True:
    acuan = min(pulau(hit.data), key=lambda idx: abs(sum(hit.data.vertices[i].co.y for i in idx) / len(idx) - 1.89))
    vs = [hit.data.vertices[i].co + Vector((0, 0.36, 0)) for i in acuan]   # satu kelompok = 0.42; 0.36 agar tidak menimpa bingkai emas sampul
    pangkal = Vector((max(v.x for v in vs), sum(v.y for v in vs) / len(vs), 0))   # ujung dekat Rami
    nomor = {i: k for k, i in enumerate(acuan)}
    sisi = [[nomor[i] for i in poly.vertices] for poly in hit.data.polygons if poly.vertices[0] in nomor]
    me = bpy.data.meshes.new("hitungan_baru")
    me.from_pydata([v - pangkal for v in vs], [], sisi)
    me.materials.append(hit.data.materials[0])
    baru = O.new("hitungan_baru", me)
    for c in hit.users_collection:
        c.objects.link(baru)
    baru.parent = hit.parent
    baru.matrix_parent_inverse = hit.matrix_parent_inverse.copy()
    baru.location = hit.location + pangkal
baru.animation_data_clear()
kunci(baru, "scale", P04 + 8, Vector((0.001, 1, 1)))
kunci(baru, "scale", P04 + 38, Vector((1, 1, 1)))
tampil([baru], 1, False)
tampil([baru], P04 + 8, True)
tampil([baru], P12, False)
konstan([baru])

debu_lap = [O["lapisan_debu"], O["hitungan_rami"], baru]
for o in debu_lap:
    for fc in fcurves(o):                                   # buang kunci "hilang sekaligus" versi lama
        if fc.data_path.startswith("hide"):
            for k in [k for k in fc.keyframe_points if P11 <= k.co[0] < P12]:
                fc.keyframe_points.remove(k)
    if "Hapus_Terlap" not in o.modifiers:
        o.modifiers.new("Hapus_Terlap", 'NODES').node_group = ng
sc.frame_set(P11)
gumpal = []                                                 # (objek, indeks verteks, pusat dunia)
for o in debu_lap:
    for idx in pulau(o.data):
        pusat = sum((o.data.vertices[i].co for i in idx), Vector()) / len(idx)
        gumpal.append((o, idx, o.matrix_world @ pusat))
waktu_lap = [None] * len(gumpal)
for f in range(P11, P12):
    sc.frame_set(f)
    inv = tangan.matrix_world.inverted()
    for n, (o, idx, p) in enumerate(gumpal):
        if waktu_lap[n] is None:
            q = inv @ p
            if abs(q.x - KAIN_TENGAH.x) < KAIN_SETENGAH and abs(q.y - KAIN_TENGAH.y) < KAIN_SETENGAH and -0.78 < q.z < -0.45:   # kain menempel di sampul
                waktu_lap[n] = f
sisa = waktu_lap.count(None)
for o in debu_lap:
    nilai = [1e6] * len(o.data.vertices)
    for (oo, idx, p), f in zip(gumpal, waktu_lap):
        if oo is o:
            for i in idx:
                nilai[i] = f if f is not None else P11 + 88
    at = o.data.attributes.get("waktu_lap") or o.data.attributes.new("waktu_lap", 'FLOAT', 'POINT')
    at.data.foreach_set("value", nilai)
print("DEBU tersapu %d/%d gumpalan, frame %d-%d" % (len(gumpal) - sisa, len(gumpal),
      min(f for f in waktu_lap if f), max(f for f in waktu_lap if f)))

# Kamera P11: dari belakang pembaca, menunduk ke sampul. Lengan kanan masuk dari kanan bawah tanpa menutupi
# mushaf (kamera lama sejajar bahu kanan, jadi tertutup lengan yang terangkat).
cam11 = next(m.camera for m in sc.timeline_markers if m.name == "P11")
cam11.location = (12.2, -3.0, 27.0)
cam11.rotation_euler = (Vector((17.4, -3.0, 21.0)) - cam11.location).to_track_quat('-Z', 'Y').to_euler()
cam11.data.lens = 30

# Kamera pembuka (P01): melayang pelan dari sisi jendela ke arah rak, siap disambung push-in P02
cam1 = next(m.camera for m in sc.timeline_markers if m.name == "P01")
cam1.animation_data_clear()
# akhir gerakan: rak + tokoh di titik sepertiga kanan-atas
for f, loc, rot in ((P01, (-14.5, -15.2, 25.5), (62, 0, -40)), (P02 - 1, (-7.5, -14.3, 23.2), (75.8, 0, -51.3))):
    kunci(cam1, "location", f, Vector(loc))
    kunci(cam1, "rotation_euler", f, Vector([R(r) for r in rot]))

# Push-in P02: berakhir setinggi mata tokoh. Rami & Abu (pembicara berikutnya) di sepertiga kiri,
# Piko di sepertiga kanan, garis mata di sepertiga atas (dulu terlalu dekat & rendah: tokoh mepet kiri-atas).
cam2 = next(m.camera for m in sc.timeline_markers if m.name == "P02")
cam2.animation_data_clear()
for f, loc, rot in ((P02, (4.0, -11.0, 18.0), (1.771, 0, -1.039)), (P03 - 1, (11.67, -6.49, 22.8), (1.4084, 0, -0.932))):
    kunci(cam2, "location", f, Vector(loc))
    kunci(cam2, "rotation_euler", f, Vector(rot))

# P03: dulu extreme close-up (wajah memenuhi frame, potongan Rami di tepi) untuk adegan menguap yang tenang.
# Sekarang close-up 3/4: seluruh kepala Abu masuk, Rami jadi latar di belakangnya, Piko di luar frame.
cam3 = next(m.camera for m in sc.timeline_markers if m.name == "P03")
cam3.location = (12.83, -5.58, 21.75)
cam3.rotation_euler = (1.5365, 0, -0.8665)
cam3.data.lens = 50

# P04 medium: mundur sedikit supaya Piko tidak terpotong. Rami (pembicara) & Abu di sepertiga kiri bersama
# goresan hitungan yang sedang dibuat, Piko di sepertiga kanan.
cam4 = next(m.camera for m in sc.timeline_markers if m.name == "P04")
cam4.location = (9.78, -5.35, 22.6)
cam4.rotation_euler = (1.4419, 0, -1.2441)
cam4.data.lens = 40

# P04 sisipan POV: saat Rami menggores, kamera dari atas kepalanya searah pandangannya (atas layar = arah
# pandang Rami), barisan hitungan melintang dan garis baru terlihat memanjang. Lalu kembali ke kamera P04.
for nama in ("P04_POV", "P04_lanjut"):
    m = sc.timeline_markers.get(nama)
    if m:
        sc.timeline_markers.remove(m)
pov = O.get("P04b_POV_Rami")
if not pov:
    pov = O.new("P04b_POV_Rami", bpy.data.cameras.new("P04b_POV_Rami"))
    for c in cam4.users_collection:
        c.objects.link(pov)
pov.data.sensor_width = cam4.data.sensor_width
pov.data.clip_start = 0.05
pov.animation_data_clear(); pov.data.animation_data_clear()
mata, sasaran = Vector((17.0, -1.05, 23.8)), Vector((16.2, -1.1, 21.16))
depan = (sasaran - mata).normalized()
kanan = depan.cross(Vector((-1, 0, 0))).normalized()
pov.matrix_world = Matrix((kanan, kanan.cross(depan), -depan)).transposed().to_4x4()
pov.location = mata
kunci(pov.data, "lens", P04 + 5, 50)                     # dorong pelan selama garis digores
kunci(pov.data, "lens", P04 + 46, 56)
sc.timeline_markers.new("P04_POV", frame=P04 + 5).camera = pov
sc.timeline_markers.new("P04_lanjut", frame=P04 + 46).camera = cam4

# P07 wide: kamera sedikit naik (tidak terlalu mendongak), keempat tokoh di tengah, mata di sepertiga atas
cam7 = next(m.camera for m in sc.timeline_markers if m.name == "P07")
cam7.location = (15.0, -9.5, 22.6)
cam7.rotation_euler = (1.4181, 0, -0.1827)
cam7.data.lens = 28

# Dinding depan: kamar dulu terbuka di sisi depan (y = -16), terlihat sebagai bidang gelap di pojok kanan P01
depan = O.get("dinding_depan")
if not depan:
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new("dinding_depan")
    bm.to_mesh(me); bm.free()
    me.materials.append(bpy.data.materials["dinding"])
    depan = O.new("dinding_depan", me)
    O["dinding_kanan"].users_collection[0].objects.link(depan)
depan.location = (0.0, -16.25, 14.0)
depan.scale = (41.0, 0.5, 28.0)

sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SELESAI", OUT)
