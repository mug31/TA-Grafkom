# Ganti potongan tangan melayang (tangan_pembaca) dengan lengan KANAN utuh sampai bahu + rig IK.
# Empty "Tangan" tetap jadi pengendali: posisinya = pergelangan, rotasinya = arah telapak.
# Bahu (objek armature "Lengan_Kanan") dianimasikan di animasi_tokoh.py supaya condong saat meraih jauh.
# Jalankan dulu skrip ini, lalu animasi_tokoh.py:
#   blender -b debu_di_atas_mushaf_lengkap.blend --python lengan_kanan.py -- debu_di_atas_mushaf_lengkap.blend
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
O = bpy.data.objects
R = math.radians
tangan = O["Tangan"]
koleksi = tangan.users_collection[0]

# ---------- bersihkan versi lama (aman dijalankan ulang) ----------
for nama in ("tangan_pembaca", "Lengan_Kanan_Mesh", "Lengan_Kanan", "Lengan_Pole", "Tangan_Arah"):
    o = O.get(nama)
    if o:
        data = o.data
        bpy.data.objects.remove(o)
        if data and data.users == 0:
            (bpy.data.meshes if isinstance(data, bpy.types.Mesh) else bpy.data.armatures).remove(data)

# ---------- ukuran (1 unit = 10 cm, pintu 2,1 m) ----------
PANJANG_ATAS, PANJANG_BAWAH = 3.4, 3.2
BAHU = Vector((0, 0, 0))
SIKU = BAHU + Vector((0.5, -0.15, 0.85)).normalized() * PANJANG_ATAS
PERGELANGAN = SIKU + Vector((0.55, 0.35, 0.75)).normalized() * PANJANG_BAWAH
# rangka telapak: x = arah jari, y = sisi jempol (tangan kanan, telapak menghadap -z), z = punggung tangan
def T(x, y, z):
    return PERGELANGAN + Vector((x, y, z))

# ---------- armature ----------
arm = bpy.data.armatures.new("Lengan_Kanan")
rig = O.new("Lengan_Kanan", arm)
koleksi.objects.link(rig)
arm.display_type = 'STICK'
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
def tulang(nama, kepala, ekor, induk=None, sambung=False):
    b = arm.edit_bones.new(nama)
    b.head, b.tail = kepala, ekor
    b.align_roll(Vector((0, 0, 1)))
    if induk:
        b.parent = arm.edit_bones[induk]
        b.use_connect = sambung
    return b
tulang("lengan_atas", BAHU, SIKU)
tulang("lengan_bawah", SIKU, PERGELANGAN, "lengan_atas", True)
tulang("telapak", PERGELANGAN, T(1.0, 0, 0), "lengan_bawah", True)
JEMPOL_PANGKAL, JEMPOL_ARAH = T(0.2, 0.36, -0.05), Vector((0.62, 0.62, -0.3)).normalized()
tulang("jempol", JEMPOL_PANGKAL, JEMPOL_PANGKAL + JEMPOL_ARAH * 0.75, "telapak")
bpy.ops.object.mode_set(mode='OBJECT')

# ---------- mesh: kumpulan tabung (cincin per titik) ----------
bm = bmesh.new()
dl = bm.verts.layers.deform.verify()
GRUP = ["lengan_atas", "lengan_bawah", "telapak", "jempol"]
MAT_KULIT, MAT_BAJU = 0, 1

def tabung(titik, n=12, atas=Vector((0, 0, 1)), tutup_awal=True, tutup_akhir=True, mat=MAT_KULIT):
    """titik: list (posisi, jari2_lebar, jari2_tebal, {grup: bobot}). Ujung ditutup membulat."""
    cincin = []
    for i, (p, rl, rt, w) in enumerate(titik):
        a = titik[max(i - 1, 0)][0]; b = titik[min(i + 1, len(titik) - 1)][0]
        t = (b - a).normalized()
        u = (atas - t * atas.dot(t)).normalized()
        s = t.cross(u)
        c = []
        for k in range(n):
            ang = 2 * math.pi * k / n
            v = bm.verts.new(p + u * math.cos(ang) * rt + s * math.sin(ang) * rl)
            for g, bobot in w.items():
                v[dl][GRUP.index(g)] = bobot
            c.append(v)
        cincin.append((c, p, t, w, rl, rt))
    for (c1, *_), (c2, *_) in zip(cincin, cincin[1:]):
        for k in range(n):
            bm.faces.new((c1[k], c1[(k + 1) % n], c2[(k + 1) % n], c2[k])).material_index = mat
    def tutup(c, p, t, w, rl, rt, arah):
        ujung = bm.verts.new(p + t * arah * min(rl, rt) * 0.7)
        for g, bobot in w.items():
            ujung[dl][GRUP.index(g)] = bobot
        for k in range(n):
            f = bm.faces.new((c[k], c[(k + 1) % n], ujung))
            f.material_index = mat
    if tutup_awal:
        tutup(*cincin[0], -1)
    if tutup_akhir:
        tutup(*cincin[-1], 1)

def bobot_lengan(s):
    """s = jarak dari bahu sepanjang lengan. Siku dicampur; putaran pergelangan disebar di lengan bawah."""
    ls = PANJANG_ATAS
    if s < ls - 0.45:
        return {"lengan_atas": 1.0}
    if s < ls + 0.45:
        k = (s - (ls - 0.45)) / 0.9
        return {"lengan_atas": 1 - k, "lengan_bawah": k}
    k = min(max((s - (ls + 1.0)) / (PANJANG_BAWAH - 0.8), 0.0), 1.0)
    return {"lengan_bawah": 1 - k, "telapak": k} if k > 0 else {"lengan_bawah": 1.0}

def titik_lengan(s):
    if s <= PANJANG_ATAS:
        return BAHU.lerp(SIKU, s / PANJANG_ATAS)
    return SIKU.lerp(PERGELANGAN, (s - PANJANG_ATAS) / PANJANG_BAWAH)

# kulit lengan (terlihat dari ujung lengan baju sampai pergelangan), masuk sedikit ke telapak
kulit = []
for s, r in ((0.3, 0.5), (1.7, 0.45), (PANJANG_ATAS, 0.37), (4.6, 0.36), (5.6, 0.33), (6.2, 0.3), (6.6, 0.28)):
    kulit.append((titik_lengan(s), r, r * 0.92, bobot_lengan(s)))
kulit.append((T(0.25, 0, 0.0), 0.33, 0.18, {"telapak": 1.0}))
tabung(kulit, atas=Vector((0, 0, 1)))

# lengan baju panjang (baju koko putih) dari bahu sampai dekat pergelangan, ujungnya terbuka
baju = [(BAHU - (SIKU - BAHU).normalized() * 0.45, 0.4, 0.4, {"lengan_atas": 1.0})]
for s, r in ((0.0, 0.68), (1.0, 0.64), (2.2, 0.58), (PANJANG_ATAS, 0.54), (4.4, 0.52), (5.2, 0.5), (5.65, 0.49)):
    baju.append((titik_lengan(s), r, r, bobot_lengan(s)))
baju.append((titik_lengan(5.58), 0.4, 0.4, bobot_lengan(5.58)))     # bibir ujung lengan baju (tebal kain)
baju.append((titik_lengan(5.1), 0.38, 0.38, bobot_lengan(5.1)))
tabung(baju, n=14, atas=Vector((0, -1, 0)), tutup_akhir=False, mat=MAT_BAJU)

# telapak (pipih), lalu empat jari menekuk santai, lalu jempol
TELAPAK = {"telapak": 1.0}
tabung([(T(0.05, 0.02, 0.0), 0.34, 0.17, TELAPAK), (T(0.45, 0.03, 0.02), 0.45, 0.19, TELAPAK),
        (T(0.95, 0.0, 0.0), 0.44, 0.15, TELAPAK)], n=12)
for y, panjang, r in ((0.31, 0.82, 0.105), (0.1, 0.92, 0.11), (-0.11, 0.86, 0.105), (-0.31, 0.68, 0.09)):
    p = T(0.9, y, 0.0)
    arah = Vector((1, 0, 0))
    jari = [(p, r, r * 0.9, TELAPAK)]
    for ruas, tekuk in ((0.42, 14), (0.32, 18), (0.26, 18)):
        arah = Matrix.Rotation(R(tekuk), 3, 'Y') @ arah        # menekuk ke bawah (ke arah telapak)
        p = p + arah * panjang * ruas
        r *= 0.93
        jari.append((p, r, r * 0.9, TELAPAK))
    tabung(jari, n=8)
JEMPOL = {"jempol": 1.0}
p = JEMPOL_PANGKAL
jempol = [(p - JEMPOL_ARAH * 0.15, 0.16, 0.14, {"telapak": 0.6, "jempol": 0.4})]
for panjang, r in ((0.0, 0.15), (0.38, 0.13), (0.68, 0.115)):
    jempol.append((p + JEMPOL_ARAH * panjang, r, r * 0.9, JEMPOL))
tabung(jempol, n=8)

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("Lengan_Kanan_Mesh")
bm.to_mesh(me)
bm.free()
me.materials.append(bpy.data.materials["kulit"])
me.materials.append(bpy.data.materials["lengan_baju"])
me.shade_smooth()
badan = O.new("Lengan_Kanan_Mesh", me)
koleksi.objects.link(badan)
for g in GRUP:
    badan.vertex_groups.new(name=g)
badan.parent = rig
md = badan.modifiers.new("Armature", 'ARMATURE')
md.object = rig
md.use_deform_preserve_volume = True                 # putaran telapak 180 derajat tidak "mengempis"
sub = badan.modifiers.new("Subdivision", 'SUBSURF')
sub.levels, sub.render_levels = 1, 2

# ---------- kendali: IK ke Empty "Tangan", siku mengarah ke bawah-luar ----------
arah = O.new("Tangan_Arah", None)                    # sumbu Y tulang telapak = sumbu X Empty Tangan
koleksi.objects.link(arah)
arah.parent = tangan
arah.rotation_euler = (0, 0, R(-90))
arah.empty_display_size = 0.3
pole = O.new("Lengan_Pole", None)
koleksi.objects.link(pole)
pole.parent = rig
pole.location = (-1.5, -3.5, -2.5)
pole.empty_display_size = 0.3

pb = rig.pose.bones
ik = pb["lengan_bawah"].constraints.new('IK')
ik.target, ik.pole_target, ik.chain_count = tangan, pole, 2
rot = pb["telapak"].constraints.new('COPY_ROTATION')
rot.target = arah

# pole_angle: pilih yang membuat siku paling dekat ke arah pole
rig.location = (13.6, -5.4, 16.8)
tangan.location, tangan.rotation_euler = Vector((16.2, -3.0, 21.75)), (0, 0, 0)
terbaik = None
for derajat in range(-180, 180, 5):
    ik.pole_angle = R(derajat)
    bpy.context.view_layer.update()
    siku = rig.matrix_world @ pb["lengan_bawah"].head
    nilai = (siku - rig.matrix_world.translation).normalized().dot((pole.matrix_world.translation - rig.matrix_world.translation).normalized())
    if terbaik is None or nilai > terbaik[0]:
        terbaik = (nilai, derajat)
ik.pole_angle = R(terbaik[1])
print("pole_angle", terbaik[1])

# kain lap pindah ke bawah telapak (telapak lebih panjang dari versi lama)
O["kain"].location = (0.45, 0, 0)
bpy.context.view_layer.update()
print("ujung tangan meleset dari target: %.3f" % ((rig.matrix_world @ pb["lengan_bawah"].tail) - tangan.matrix_world.translation).length)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SELESAI", OUT)
