# Siluet hitam Pembaca di ambang pintu (panel 10), memakai karakter buatan sendiri dari modul 8
# (../mod8_mixamo.blend: model modul 4, rig modul 7, animasi jalan Mixamo).
# Pembaca berdiri di depan cahaya_pintu sehingga terlihat sebagai siluet saat pintu terbuka,
# lalu melangkah satu siklus jalan masuk kamar dan berhenti. Hanya tampil di panel 10.
# Aman dijalankan ulang:
#   blender -b debu_di_atas_mushaf_lengkap.blend --python siluet_pembaca.py -- debu_di_atas_mushaf_lengkap.blend
import bpy, math, os, sys
from mathutils import Vector

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.dirname(OUT)
SUMBER = os.path.join(DIR, "..", "mod8_mixamo.blend")
sc = bpy.context.scene
O = bpy.data.objects
P = {m.name: m.frame for m in sc.timeline_markers}
P10, P11 = P["P10"], P["P11"]

X = -12.3                    # tengah bukaan pintu (sisi dalam kusen x -17..-9), menjauhi daun pintu yang terbuka miring
Y_BERDIRI = 9.5              # di lorong, di balik kusen (y 5), masih di depan cahaya_pintu (y 12)
BELOK = 80.0                 # setelah lewat pintu berbelok ke arah mushaf, berhenti tepat sebelum rehal
LURUS = 6.2                  # jarak lurus dulu sampai badan keluar dari bukaan pintu (dinding y 5..5,5)
JARI = 3.0                   # jari-jari belokan
MULAI_JALAN = P10 + 92       # setelah pintu terbuka penuh (P10+70) dan para debu terkejut
SIKLUS = 32                  # frame per siklus jalan Mixamo (2 langkah)
LANGKAH = 16.0               # jarak tempuh per siklus (unit = 10 cm)

# ---------- bersihkan versi lama ----------
lama = bpy.data.collections.get("Siluet Pembaca")
if lama:
    for o in list(lama.all_objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(lama)
for a in [a for a in bpy.data.actions if a.name.startswith("Siluet_")]:
    bpy.data.actions.remove(a)

kol = bpy.data.collections.new("Siluet Pembaca")
sc.collection.children.link(kol)

# ---------- ambil karakter dari modul 8 ----------
# rig + mesh versi Mixamo (di mod8_mixamo.blend juga ada versi rig lama tanpa animasi, tidak dipakai)
NAMA = ["Armature_mixamo", "badan.001", "baju.001", "celana.001", "Cube.001", "rambut.001", "sepatu.001",
        "Sphere.003", "Sphere.004"]
with bpy.data.libraries.load(SUMBER, link=False) as (src, dst):
    dst.objects = NAMA
arm = dst.objects[0]
bagian = [o for o in dst.objects[1:] if o.parent == arm]
offset = arm.parent
for o in [arm] + bagian:
    kol.objects.link(o)
arm.name = "Siluet_Rig"
for o in bagian:
    o.name = "Siluet_" + o.name.split(".")[0]
arm.parent = None
if offset and offset.users_collection == ():
    bpy.data.objects.remove(offset)

akar = O.new("Siluet_Pembaca", None)                            # pembawa posisi & arah
kol.objects.link(akar)
akar.empty_display_size = 3
arm.parent = akar
arm.matrix_parent_inverse.identity()
arm.location = (0, 0, 0)
arm.rotation_mode = 'XYZ'
arm.rotation_euler = (0, 0, 0)                                  # jalan Mixamo maju ke -y lokal = ke arah kamera

# ---------- aksi jalan: buang perpindahan maju (dipindah ke akar), sisanya diulang ----------
aksi = arm.animation_data.action.copy()
aksi.name = "Siluet_Jalan"
arm.animation_data.action = None
def fcurves(a):
    try:
        return list(a.fcurves)
    except Exception:
        return [fc for l in a.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
def buang(a, fc):
    try:
        a.fcurves.remove(fc)
    except Exception:
        for l in a.layers:
            for s in l.strips:
                for cb in s.channelbags:
                    if fc in list(cb.fcurves):
                        cb.fcurves.remove(fc)
                        return
for fc in fcurves(aksi):
    if fc.data_path == "location" and fc.array_index == 1:
        buang(aksi, fc)
for fc in fcurves(aksi):
    fc.modifiers.new('CYCLES')

# frame "melintas" (kedua kaki sejajar) dipakai sebagai pose berdiri dan pose akhir
arm.animation_data.action = aksi
try:
    arm.animation_data.action_slot = aksi.slots[0]
except Exception:
    pass
def kaki(f):
    sc.frame_set(f)
    pb = arm.pose.bones
    return abs((arm.matrix_world @ pb["telapak.L"].head - arm.matrix_world @ pb["telapak.R"].head).y)
a0 = int(aksi.frame_range[0])
melintas = min(range(a0, a0 + SIKLUS), key=kaki)
arm.animation_data.action = None

# NLA: diam di pose melintas, jalan tepat satu siklus, berhenti lagi di pose melintas
trek = arm.animation_data.nla_tracks.new()
trek.name = "Siluet_Jalan"
strip = trek.strips.new("jalan", MULAI_JALAN, aksi)
strip.action_frame_start = melintas
strip.action_frame_end = melintas + SIKLUS
strip.frame_end = MULAI_JALAN + SIKLUS
strip.extrapolation = 'HOLD'
strip.blend_in = strip.blend_out = 0

# ---------- posisi: kaki tepat di lantai ----------
akar.location = (X, Y_BERDIRI, 0)
sc.frame_set(MULAI_JALAN)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
bawah = min((o.evaluated_get(dg).matrix_world @ Vector(c)).z for o in bagian for c in o.evaluated_get(dg).bound_box)
akar.location.z -= bawah
# Lintasan: lurus keluar dari bukaan pintu dulu (melewati dinding y 5), baru berbelok melengkung
# ke kanan kamera. Kalau langsung miring sejak di lorong, badan menembus dinding sebelah kusen.
awal = Vector((X, Y_BERDIRI, akar.location.z))
def lintasan(s):
    """posisi & arah hadap (derajat) setelah menempuh jarak s"""
    p, th, ds = awal.copy(), 0.0, 0.02
    t = 0.0
    while t < s - 1e-9:
        d = min(ds, s - t)
        if t >= LURUS:
            th = min(BELOK, math.degrees((t - LURUS) / JARI)) if t < LURUS + math.radians(BELOK) * JARI else BELOK
        r = math.radians(th)
        p += Vector((math.sin(r), -math.cos(r), 0)) * d
        t += d
    return p, th
akar.location = awal
akar.keyframe_insert("location", frame=P10)
akar.rotation_euler = (0, 0, 0)
akar.keyframe_insert("rotation_euler", index=2, frame=P10)
for i in range(SIKLUS + 1):
    p, th = lintasan(LANGKAH * i / SIKLUS)
    akar.location = p
    akar.rotation_euler = (0, 0, math.radians(th))
    akar.keyframe_insert("location", frame=MULAI_JALAN + i)
    akar.keyframe_insert("rotation_euler", index=2, frame=MULAI_JALAN + i)
for fc in fcurves(akar.animation_data.action):
    for k in fc.keyframe_points:
        k.interpolation = 'LINEAR'

# ---------- hitam pekat ----------
mat = bpy.data.materials.get("Mat_Siluet") or bpy.data.materials.new("Mat_Siluet")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
bsdf.inputs["Roughness"].default_value = 1.0
for nama in ("Specular IOR Level", "Specular"):
    if nama in bsdf.inputs:
        bsdf.inputs[nama].default_value = 0.0
mat.diffuse_color = (0, 0, 0, 1)
for o in bagian:
    o.data = o.data.copy()
    o.data.materials.clear()
    o.data.materials.append(mat)

# ---------- lorong terang di balik pintu, supaya siluet hitam terbaca jelas ----------
# Bidang bercahaya hangat di belakang cahaya_pintu (y 12); hanya terlihat lewat pintu yang terbuka.
me = bpy.data.meshes.new("Siluet_Latar")
me.from_pydata([(-21, 12.8, 0), (-5, 12.8, 0), (-5, 12.8, 25), (-21, 12.8, 25)], [], [(0, 1, 2, 3)])
latar_mat = bpy.data.materials.get("Mat_Siluet_Latar") or bpy.data.materials.new("Mat_Siluet_Latar")
latar_mat.use_nodes = True
nt = latar_mat.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.78, 0.5, 1)
em.inputs["Strength"].default_value = 3.0
nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
me.materials.append(latar_mat)
latar = O.new("Siluet_Latar", me)
kol.objects.link(latar)
latar.visible_shadow = False

# ---------- hanya tampil di panel 10 ----------
for o in [arm] + bagian:
    for f, muncul in ((1, False), (P10, True), (P11, False)):
        o.hide_viewport = o.hide_render = not muncul
        o.keyframe_insert("hide_viewport", frame=f)
        o.keyframe_insert("hide_render", frame=f)
    for fc in fcurves(o.animation_data.action):
        if fc.data_path.startswith("hide"):
            for k in fc.keyframe_points:
                k.interpolation = 'CONSTANT'

sc.frame_set(1)
print("SILUET melintas di frame aksi", melintas, "| jalan", MULAI_JALAN, "-", MULAI_JALAN + SIKLUS,
      "| tinggi %.1f unit" % max(o.dimensions.z for o in bagian))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SELESAI", OUT)
