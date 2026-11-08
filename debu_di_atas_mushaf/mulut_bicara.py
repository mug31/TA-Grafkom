# Rig mulut bicara: setiap tokoh dapat satu shape key "buka" (0 = tertutup, 1 = terbuka lebar)
# yang dianimasikan per suku kata oleh animasi_tokoh.py.
#   - Mulut garis (Abu, Piko senang/sedih) dan mulut lukisan tekstur (Rami) diberi "rongga":
#     mesh gelap di bawah garis bibir yang membuka ke bawah, menempel di permukaan wajah.
#   - Mulut berisi (Bayu, Piko normal/kaget) langsung diberi shape key "buka".
# Aman dijalankan ulang. Jalankan sebelum animasi_tokoh.py:
#   blender -b debu_di_atas_mushaf_lengkap.blend --python mulut_bicara.py -- debu_di_atas_mushaf_lengkap.blend
import bpy, math, os, sys
from mathutils import Vector

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
O = bpy.data.objects
sc = bpy.context.scene
sc.frame_set(1)                                   # semua tokoh di pose dasar
vl = bpy.context.view_layer
vl.update()
dg = bpy.context.evaluated_depsgraph_get()
BAHAN = bpy.data.materials.get("Mat_Rongga_Mulut") or bpy.data.materials.new("Mat_Rongga_Mulut")
BAHAN.use_nodes = True                            # merah tua gelap, kontras dengan bibir merah Abu
bsdf = BAHAN.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.09, 0.006, 0.012, 1)
bsdf.inputs["Roughness"].default_value = 0.75
BAHAN.diffuse_color = (0.09, 0.006, 0.012, 1)

# ---------- bersihkan versi lama ----------
for o in [o for o in O if o.name.endswith("_Rongga")]:
    me = o.data
    bpy.data.objects.remove(o)
    if me.users == 0:
        bpy.data.meshes.remove(me)

def key_buka(o):
    """Shape key "buka" baru (versi lama dibuang), mulai dari Basis."""
    if not o.data.shape_keys:
        o.shape_key_add(name="Basis")
    kb = o.data.shape_keys.key_blocks
    if "buka" in kb:
        o.shape_key_remove(kb["buka"])
    k = o.shape_key_add(name="buka", from_mix=False)
    k.slider_max = 1.5                            # menguap boleh lebih lebar dari bicara biasa
    return k

def sambung(dari_key, nama, ke_key):
    """Driver: key_blocks[nama] pada ke_key mengikuti nilai key yang sama di dari_key."""
    kb = ke_key.key_blocks[nama]
    kb.driver_remove("value")
    fc = kb.driver_add("value")
    var = fc.driver.variables.new()
    var.name, var.type = "m", 'SINGLE_PROP'
    var.targets[0].id_type = 'KEY'
    var.targets[0].id = dari_key
    var.targets[0].data_path = f'key_blocks["{nama}"].value'
    fc.driver.expression = "m"

def garis_tengah(o, n=16, kunci=None):
    """Garis tengah mesh mulut berbentuk garis (dikelompokkan per x), dalam koordinat dunia."""
    me = o.data
    xs = [v.co.x for v in me.vertices]
    x0, x1 = min(xs), max(xs)
    grup = [[] for _ in range(n)]
    for v in me.vertices:
        grup[min(n - 1, int((v.co.x - x0) / (x1 - x0) * n))].append(v.index)
    grup = [g for g in grup if g]
    data = kunci.data if kunci else me.vertices
    return [o.matrix_world @ (sum((data[i].co for i in g), Vector()) / len(g)) for g in grup]

def permukaan_di(permukaan, p, depan):
    """Titik di permukaan `permukaan` searah `depan` dari p (dunia), None kalau meleset."""
    inv_p = permukaan.matrix_world.inverted()
    ok, loc, _, _ = permukaan.evaluated_get(dg).ray_cast(inv_p @ (p + depan * 0.3),
                                                         (inv_p.to_3x3() @ -depan).normalized(), distance=0.6)
    return permukaan.matrix_world @ loc if ok else None

def rongga(nama, induk, permukaan, titik, depan, atas, tinggi, celah=0.0, tebal=0.003, ekspresi=None,
           bentuk=None, baris=4):
    """Mesh rongga mulut di bawah garis `titik` (dunia). Basis = terkatup (tinggi 0), "buka" = terbuka.
    Tiap titik diproyeksikan ke `permukaan` sepanjang `depan` supaya menempel di wajah yang melengkung.
    ekspresi = {nama_key: titik garis untuk key itu} -> rongga ikut berubah bentuk lewat driver.
    bentuk = {nama_key: f(t, s) -> titik dunia} -> bentuk bebas (t = kiri-kanan, s = atas-bawah, 0..1)."""
    def tempel(p):
        q = permukaan_di(permukaan, p, depan)
        return q + depan * tebal if q else p
    N = len(titik)
    def grid(garis, buka):
        hasil = []
        for i, c in enumerate(garis):
            t = i / (N - 1)
            dalam = tinggi * math.sin(math.pi * t) ** 0.7 * buka
            for j in range(baris + 1):
                hasil.append(tempel(c - atas * (celah + dalam * j / baris)))
        return hasil
    me = bpy.data.meshes.new(nama)
    inv = induk.matrix_world.inverted()
    tutup = grid(titik, 0.0)
    wajah = [(i * (baris + 1) + j, i * (baris + 1) + j + 1, (i + 1) * (baris + 1) + j + 1, (i + 1) * (baris + 1) + j)
             for i in range(N - 1) for j in range(baris)]
    me.from_pydata([inv @ p for p in tutup], [], wajah)
    me.materials.append(BAHAN)
    o = O.new(nama, me)
    for c in induk.users_collection:
        c.objects.link(o)
    o.parent = induk
    o.matrix_parent_inverse.identity()
    o.matrix_world = induk.matrix_world.copy()
    # arah normal ke depan wajah
    vl.update()
    n0 = o.matrix_world.to_3x3() @ me.polygons[0].normal
    if n0.dot(depan) < 0:
        for p in me.polygons:
            p.flip()
    o.shape_key_add(name="Basis")
    for k, garis in (ekspresi or {}).items():
        kb = o.shape_key_add(name=k, from_mix=False)
        for d, p0, c0, c1 in zip(kb.data, tutup, [c for c in titik for _ in range(baris + 1)],
                                 [c for c in garis for _ in range(baris + 1)]):
            d.co = inv @ (p0 + (c1 - c0))
    for k, f in (bentuk or {}).items():
        kb = o.shape_key_add(name=k, from_mix=False)
        for d, (i, j) in zip(kb.data, [(i, j) for i in range(N) for j in range(baris + 1)]):
            d.co = inv @ tempel(f(i / (N - 1), j / baris))
    kb = key_buka(o)
    for d, p in zip(kb.data, grid(titik, 1.0)):
        d.co = inv @ p
    return o

# ---------- ABU: garis senyum merah + rongga di bawahnya, ikut ekspresi senang/kaget/sedih ----------
abu_m = O["Abu_mulut"]
depan = (abu_m.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
atas = (abu_m.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
kb = abu_m.data.shape_keys.key_blocks

# "kaget" lama melintir seperti pita (cincin tabung digeser tanpa diputar). Dibangun ulang:
# tabung bibir (14 cincin x 4 titik, lokal: x lebar, z atas, y ke belakang) disapu mengikuti
# lingkaran "O"; penampang tiap cincin diputar mengikuti arah lengkungan supaya tidak terpuntir.
me = abu_m.data
CINCIN = len(me.vertices) // 4
basis = [v.co.copy() for v in kb["Basis"].data]
pusat_c = [sum(basis[4 * k:4 * k + 4], Vector()) / 4 for k in range(CINCIN)]
def bingkai(titik, k):
    """(normal, belakang) penampang cincin ke-k: normal tegak lurus garis di bidang wajah x-z."""
    a, b = titik[max(k - 1, 0)], titik[min(k + 1, len(titik) - 1)]
    t = Vector((b.x - a.x, 0, b.z - a.z)).normalized()
    return Vector((-t.z, 0, t.x)), Vector((0, 1, 0))
tebal_wajah = []                                   # jarak pusat cincin di depan permukaan wajah
for c in pusat_c:
    q = permukaan_di(O["Abu_badan"], abu_m.matrix_world @ c, depan)
    tebal_wajah.append(((abu_m.matrix_world @ c) - q).dot(depan) if q else 0.0)
maju = sum(tebal_wajah) / len(tebal_wajah)
RX, RZ = 0.055, 0.07                               # jari-jari "O" (pusat tabung), lokal Abu_mulut
CX, CZ = 0.0, sum(c.z for c in pusat_c) / CINCIN - 0.035
CELAH = math.radians(14)                           # ujung tabung bertemu di atas tanpa saling tembus
o_baru = []
for k in range(CINCIN):
    sudut = math.pi / 2 + CELAH / 2 + (2 * math.pi - CELAH) * k / (CINCIN - 1)
    p = Vector((CX + RX * math.cos(sudut), 0, CZ + RZ * math.sin(sudut)))   # kiri -> bawah -> kanan
    q = permukaan_di(O["Abu_badan"], abu_m.matrix_world @ p, depan)
    if q:                                          # ikuti lengkung wajah, jarak ke wajah sama seperti senyum
        p = abu_m.matrix_world.inverted() @ (q + depan * maju)
    o_baru.append(p)
kaget = kb["kaget"]
for k in range(CINCIN):
    n0, y0 = bingkai(pusat_c, k)
    n1, y1 = bingkai(o_baru, k)
    for i in range(4 * k, 4 * k + 4):
        off = basis[i] - pusat_c[k]
        kaget.data[i].co = o_baru[k] + n1 * off.dot(n0) + y1 * off.dot(y0)

def isi_o(t, s):
    """Bagian dalam "O" untuk rongga: t kiri-kanan, s atas-bawah."""
    rx, rz = RX - 0.012, RZ - 0.012
    x = CX + (2 * t - 1) * rx
    h = rz * math.sqrt(max(0.0, 1 - ((x - CX) / rx) ** 2))
    return abu_m.matrix_world @ Vector((x, 0, CZ + h - 2 * h * s))

ek = {k: garis_tengah(abu_m, kunci=kb[k]) for k in ("senang", "sedih")}
r = rongga("Abu_mulut_Rongga", abu_m, O["Abu_badan"], garis_tengah(abu_m, kunci=kb["Basis"]), depan, atas,
           tinggi=0.095, celah=0.006, ekspresi=ek, bentuk={"kaget": isi_o})
for k in ("senang", "kaget", "sedih"):
    sambung(abu_m.data.shape_keys, k, r.data.shape_keys)

# ---------- RAMI: mulut bergelombang dilukis di tekstur; garisnya dilacak dari render close-up ----------
# (koordinat lokal Rami_Badan, kiri -> kanan, sepanjang garis cokelat tua di tekstur)
RAMI_GARIS = [(-0.1158, -0.3028, -0.0775), (-0.0964, -0.3105, -0.0766), (-0.0773, -0.3127, -0.0726),
              (-0.0582, -0.3148, -0.0685), (-0.0391, -0.3197, -0.0661), (-0.0202, -0.3209, -0.0622),
              (-0.0012, -0.3186, -0.0529), (0.0178, -0.3206, -0.0622), (0.0368, -0.3186, -0.0662),
              (0.0559, -0.3145, -0.0666), (0.0749, -0.3150, -0.0761), (0.0941, -0.3126, -0.0802),
              (0.1136, -0.3031, -0.0736)]
rb = O["Rami_Badan"]
depan = (rb.matrix_world.to_3x3() @ Vector((0, -0.83, 0.55))).normalized()
atas = (rb.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
rongga("Rami_mulut_Rongga", rb, rb, [rb.matrix_world @ Vector(p) for p in RAMI_GARIS], depan, atas,
       tinggi=0.075, celah=0.006, tebal=0.006)

# ---------- PIKO: 4 set wajah ----------
badan = O["Piko_Badan"]
depan = (badan.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
atas = (badan.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
for n in ("Piko_Senang_Mulut", "Piko_Sedih_Mulut"):        # garis senyum / cemberut hitam
    m = O[n]
    rongga(n + "_Rongga", m, badan, garis_tengah(m, n=14), depan, atas, tinggi=0.11, celah=0.012)
for set_ in ("Normal", "Kaget"):                           # mulut "o": memanjang ke bawah
    bibir, isi = O[f"Piko_{set_}_Mulut_1_BibirHitam"], O[f"Piko_{set_}_Mulut_2_RonggaMarun"]
    titik = [bibir.matrix_world @ v.co for v in bibir.data.vertices]
    pusat = sum(titik, Vector()) / len(titik)
    tinggi = max(p.dot(atas) for p in titik) - min(p.dot(atas) for p in titik)
    for o in (bibir, isi):
        inv = o.matrix_world.inverted()
        kb = key_buka(o)
        for d, v in zip(kb.data, o.data.vertices):
            p = o.matrix_world @ v.co
            h = (p - pusat).dot(atas)
            d.co = inv @ (p + atas * (h * 0.6 - tinggi * 0.25))   # tinggi x1.6, rahang turun

# ---------- BAYU: bibir bawah (titik 5-7) turun, lidah ikut ----------
bm = O["Bayu_mulut"]
kb = key_buka(bm)
TURUN = {1: -0.03, 2: -0.04, 3: -0.03, 5: 0.26, 6: 0.32, 7: 0.26}  # koordinat lokal: y = atas
for i, d in enumerate(kb.data):
    d.co.y -= TURUN.get(i, 0.0)
lidah = O["Bayu_Lidah"]
lk = lidah.data.shape_keys.key_blocks
if "buka" in lk:
    lidah.shape_key_remove(lk["buka"])
k = lidah.shape_key_add(name="buka", from_mix=False)
asli = [d.co.copy() for d in lk["senang"].data]               # "senang" = ukuran lidah asli
pusat = sum(asli, Vector()) / len(asli)
for d, co in zip(k.data, asli):
    d.co = pusat + Vector((0, -0.12, 0)) + (co - pusat) * 0.7
sambung(bm.data.shape_keys, "buka", lidah.data.shape_keys)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SELESAI", OUT)
