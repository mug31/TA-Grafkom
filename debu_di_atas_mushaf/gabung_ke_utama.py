# Ganti Piko & Rami versi generator di file utama dengan model buatan teman (piko.blend, rami.blend).
# Model baru dipasang sebagai anak Empty karakter lama, jadi posisi, arah hadap, dan kamera panel tetap.
# Mesh lama dipindah ke collection "Cadangan_Tokoh_Lama" (disembunyikan, bisa dikembalikan).
# Jalankan: blender -b ../debu_di_atas_mushaf_lengkap.blend --python gabung_ke_utama.py -- debu_di_atas_mushaf_lengkap.blend
import bpy, math, os, sys
from mathutils import Vector

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.dirname(OUT)
sc = bpy.context.scene
vl = bpy.context.view_layer

cadangan = bpy.data.collections.new("Cadangan_Tokoh_Lama")
sc.collection.children.link(cadangan)

def tinggi_lama(root):
    zs = [(o.matrix_world @ Vector(c)).z for o in root.children_recursive if o.type == 'MESH' for c in o.bound_box]
    return max(zs) - min(zs)

def simpan_lama(root):
    for o in list(root.children_recursive):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        cadangan.objects.link(o)

def layer_col(nama, lc=None):
    lc = lc or vl.layer_collection
    if lc.name == nama:
        return lc
    for ch in lc.children:
        r = layer_col(nama, ch)
        if r:
            return r

def pasang(ctrl, root, objs, rot=(0, 0, 0)):
    """Skala ctrl agar setinggi tokoh lama, lalu taruh alasnya tepat di titik root (permukaan mushaf)."""
    tinggi = tinggi_lama(root)
    ctrl.parent = None
    ctrl.location = (0, 0, 0); ctrl.rotation_euler = rot; ctrl.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for o in objs for c in o.bound_box]
    s = tinggi / (max(zs) - min(zs))
    ctrl.parent = root
    ctrl.matrix_parent_inverse.identity()
    ctrl.scale = (s, s, s)
    ctrl.location = (0, 0, -min(zs) * s)
    return tinggi, s

# ---------------- Piko ----------------
piko_root = bpy.data.objects["Piko"]
with bpy.data.libraries.load(os.path.join(DIR, "piko.blend"), link=False) as (src, dst):
    dst.collections = ["Piko_Utama"]
piko_col = dst.collections[0]
bpy.data.collections["Piko"].children.link(piko_col)
simpan_lama(piko_root)
ctrl = bpy.data.objects["Piko_Master_Ctrl"]
for c in piko_col.children:                       # hanya ekspresi Normal yang tampil
    lc = layer_col(c.name)
    lc.hide_viewport = c.name != "Piko_1_Wajah_Normal"
    c.hide_render = c.name != "Piko_1_Wajah_Normal"
tampil = [o for o in piko_col.all_objects if o.type == 'MESH'
          and not any(n in o.name for n in ("_Senang_", "_Kaget_", "_Sedih_"))]
print("PIKO tinggi %.2f skala %.3f" % pasang(ctrl, piko_root, tampil))

# ---------------- Rami ----------------
rami_root = bpy.data.objects["Rami"]
with bpy.data.libraries.load(os.path.join(DIR, "rami.blend"), link=False) as (src, dst):
    dst.objects = ["world", "geometry_0"]
rami_col = bpy.data.collections.new("Rami_Utama")
bpy.data.collections["Rami"].children.link(rami_col)
rctrl, rbadan = dst.objects
rctrl.name, rbadan.name = "Rami_Ctrl", "Rami_Badan"
bpy.data.materials["Material_0"].name = "Mat_Rami_Tekstur"
for o in (rctrl, rbadan):
    rami_col.objects.link(o)
simpan_lama(rami_root)
print("RAMI tinggi %.2f skala %.3f" % pasang(rctrl, rami_root, [rbadan]))

# ---------------- Bayu ----------------
# Karakter_Bayu.blend (root repo) dimodelkan rebahan: wajah ke +Z, kepala ke +Y -> diputar 90 derajat di X.
bayu_root = bpy.data.objects["Bayu"]
for o in bayu_root.children_recursive:                # nama lama (Bayu_mulut, ...) dibebaskan untuk versi baru
    o.name = o.name + "_lama"
BUANG = {"Kamera_Bayu", "Lampu_Isi", "Lampu_Rim", "Lampu_Utama", "Bayangan"}
with bpy.data.libraries.load(os.path.join(os.path.dirname(DIR), "Karakter_Bayu.blend"), link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n not in BUANG]
bayu_col = bpy.data.collections.new("Bayu_Utama")
bpy.data.collections["Bayu"].children.link(bayu_col)
bctrl = bpy.data.objects.new("Bayu_Ctrl", None)
bayu_col.objects.link(bctrl)
for o in dst.objects:
    if not o.name.startswith("Bayu_"):
        o.name = "Bayu_" + o.name
    bayu_col.objects.link(o)
    o.parent = bctrl
simpan_lama(bayu_root)
print("BAYU tinggi %.2f skala %.3f" % pasang(bctrl, bayu_root, list(dst.objects), rot=(math.radians(90), 0, 0)))

# ---------- rig mulut Bayu: shape key senang/kaget/sedih + lidah ikut lewat driver ----------
# Koordinat lokal model teman: x kanan, y atas, z keluar dari wajah. Titik 0-4 bibir atas (kiri->kanan),
# 5-7 bibir bawah (kanan->kiri). Basis = senyum tipis netral; "senang" = bentuk asli dari teman.
mulut = bpy.data.objects["Bayu_Mulut_Senyum"]
mulut.name = mulut.data.name = "Bayu_mulut"
asli = [v.co.copy() for v in mulut.data.vertices]
def bentuk(xy):
    return [Vector((x, y, asli[i].z)) for i, (x, y) in enumerate(xy)]
NETRAL = bentuk([(-0.5, -0.55), (-0.3, -0.62), (0, -0.64), (0.3, -0.62), (0.5, -0.55),
                 (0.33, -0.7), (0, -0.74), (-0.33, -0.7)])
KAGET = bentuk([(0.27 * math.cos(math.radians(a)), -0.7 + 0.33 * math.sin(math.radians(a)))
                for a in (180, 135, 90, 45, 0, -45, -90, -135)])
SEDIH = bentuk([(-0.55, -0.85), (-0.3, -0.72), (0, -0.68), (0.3, -0.72), (0.55, -0.85),
                (0.33, -0.86), (0, -0.8), (-0.33, -0.86)])
for v, co in zip(mulut.data.vertices, NETRAL):
    v.co = co
mulut.shape_key_add(name="Basis")
for nama, pos in (("senang", asli), ("kaget", KAGET), ("sedih", SEDIH)):
    kb = mulut.shape_key_add(name=nama, from_mix=False)
    for d, co in zip(kb.data, pos):
        d.co = co
    kb.value = 0.0
mulut.data.shape_keys.key_blocks["senang"].value = 1.0    # tampilan awal = senyum lebar seperti desain teman

lidah = bpy.data.objects["Bayu_Lidah"]
pusat = Vector((0, -0.77, 0.595)) - lidah.location            # pusat lidah dalam koordinat lokal mesh
asli_l = [v.co.copy() for v in lidah.data.vertices]
for v in lidah.data.vertices:                                 # Basis: lidah mengecil hilang ke dalam mulut
    v.co = pusat + (v.co - pusat) * 0.02
lidah.shape_key_add(name="Basis")
for nama, skala, geser in (("senang", (1, 1, 1), (0, 0, 0)), ("kaget", (0.4, 0.55, 1), (0, -0.12, 0))):
    kb = lidah.shape_key_add(name=nama, from_mix=False)
    for d, co in zip(kb.data, asli_l):
        r = co - pusat
        d.co = pusat + Vector(geser) + Vector((r.x * skala[0], r.y * skala[1], r.z * skala[2]))
    kb.value = 0.0
    fc = kb.driver_add("value")                               # lidah mengikuti slider mulut
    var = fc.driver.variables.new()
    var.name, var.type = "m", 'SINGLE_PROP'
    var.targets[0].id_type = 'KEY'
    var.targets[0].id = mulut.data.shape_keys
    var.targets[0].data_path = f'key_blocks["{nama}"].value'
    fc.driver.expression = "m"

# ---------- kamera close-up Bayu (P08): mundur sepanjang arah pandang sampai Bayu ±70% lebar frame ----------
from bpy_extras.object_utils import world_to_camera_view
cam8 = bpy.data.objects["P08_CU_Bayu"]
mundur = cam8.matrix_world.to_3x3() @ Vector((0, 0, 1))
for _ in range(60):
    bpy.context.view_layer.update()
    xs = [world_to_camera_view(sc, cam8, o.matrix_world @ Vector(c)).x
          for o in bpy.data.objects["Bayu_Ctrl"].children if o.type in ('MESH', 'CURVE') for c in o.bound_box]
    if max(xs) - min(xs) <= 0.7:
        break
    cam8.location += mundur * 0.1
print("P08 kamera di", tuple(round(x, 2) for x in cam8.location), "lebar Bayu %.0f%%" % ((max(xs) - min(xs)) * 100))

layer_col("Cadangan_Tokoh_Lama").exclude = True
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SELESAI", OUT)
