# Общий набор для процедурных low-poly мобов Rise Above It!
# Палитра проекта, сборка меша из примитивов с жёстким скином, скелет, привязка, экспорт меша.
# Соглашения: метры, модель смотрит в -Y, каждая вершина 100% на одну кость.
import bpy, bmesh, math, random, os
from mathutils import Vector

SHARED = os.path.dirname(os.path.abspath(__file__))

# Палитра проекта 8x8 (512 px), одна на все ассеты. Индекс -> (имя, цвет sRGB).
# Новые цвета добавлять на место spare_*, существующие индексы не двигать — на них завязаны UV.
PALETTE = [
    # мобы «Земли»
    ("body_red", 0x6b2c1f), ("scutum", 0x1a1310), ("legs", 0x2b1e17), ("belly", 0x8a7458),
    ("hypostome", 0xc2a878), ("palps", 0x4a2a1c), ("joints", 0x5a4030), ("emissive", 0xff3b1f),
    # «Канава», «Подвал», мусор
    ("frog_green", 0x4f6b2a), ("frog_belly", 0xb8b07a), ("mud", 0x3b3424), ("mouse_grey", 0x6e6660),
    ("mouse_pink", 0xc98f86), ("mosquito", 0x4b4a48), ("wing", 0x9aa3a0), ("trash_metal", 0x8c8f93),
    # игрок и оружие
    ("skin", 0xd6a98b), ("skin_dark", 0xa8785f), ("coat", 0xc8c2b2), ("coat_dirty", 0x8c8576),
    ("bandage", 0xc4b89c), ("blood", 0x5c1612), ("wood", 0xc9a66b), ("cap_red", 0xa83a2a),
    ("can_alu", 0xb9bcc0), ("doll_pink", 0xc77b9a), ("doll_blue", 0x4f6fa8), ("thread", 0x6d6a5e),
    ("frog_dark", 0x2f4219), ("mouse_dark", 0x403a36), ("rat_tail", 0xa77f78), ("eye_black", 0x0b0b0c),
    # арена «Земля»
    ("leaf", 0x6a8228), ("leaf_dark", 0x4a6220),
    ("soil", 0x5a4a3a), ("soil_dark", 0x3a3026), ("grass", 0x4f6b2a), ("grass_b", 0x5d7a30),
    ("grass_dry", 0x9a8a5a), ("grass_back", 0x2f4019), ("stone", 0x8a8070), ("stone_b", 0x6e665c),
    ("quartz", 0xb8ad98), ("wood_dry", 0x6b5a48), ("char", 0x1a1614), ("bark", 0x3a3634),
    ("crown", 0x2c3428), ("water", 0x1c1d1a), ("dew", 0xe8f0f0),
    # оружие из мусора
    ("brass", 0xb08a3a), ("copper", 0xb5653a), ("steel", 0xaeb4ba), ("hair", 0x24180f),
    ("glass", 0xbfe0e8), ("plastic_yellow", 0xd9a623), ("spark", 0x7fd8ff), ("tape", 0x8e959c),
    # таракан-крафтер (safe zone): тёплый каштановый хитин и светлая кайма переднеспинки
    ("roach", 0x9a5226), ("roach_light", 0xd8a868),
    # босс-лягушка «Земли»: язык и светлые спинные складки
    ("frog_tongue", 0xd8707a), ("frog_lime", 0x9cb83e),
] + [(f"spare_{i}", 0x505050 + 0x040404 * (i % 8)) for i in range(61, 64)]
SW = {name: i for i, (name, _) in enumerate(PALETTE)}
N = 8

def palette_image():
    """T_Palette.png в Shared/ — создаётся один раз, дальше переиспользуется."""
    path = os.path.join(SHARED, "T_Palette.png")
    img = bpy.data.images.get("T_Palette")
    if img:
        return img
    PX = 512
    S = PX // N
    img = bpy.data.images.new("T_Palette", PX, PX, alpha=False)
    pix = [0.0] * (PX * PX * 4)
    for i, (_, hexc) in enumerate(PALETTE):
        r, g, b = ((hexc >> 16) & 255) / 255, ((hexc >> 8) & 255) / 255, (hexc & 255) / 255
        cx, cy = i % N, (N - 1) - i // N
        for y in range(S):
            k = 0.7 + 0.45 * (y / (S - 1))  # снизу темнее, сверху светлее
            for x in range(S):
                p = ((cy * S + y) * PX + cx * S + x) * 4
                pix[p:p + 4] = [min(r * k, 1), min(g * k, 1), min(b * k, 1), 1.0]
    img.pixels.foreach_set(pix)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img

# ---------------------------------------------------------------- тун-палитра
# T_Palette_Toon.png — те же индексы, но каждый квадрат — три резкие полосы снизу вверх:
# тень (сдвиг в холодное), основной тон (насыщеннее), блик (сдвиг в тёплое). Какая полоса
# достанется поверхности, решает развёртка toonify() по нормали — свет «запечён», переход резкий.
TOON_BANDS = (0.32, 0.86)            # границы полос по высоте квадрата
TOON_OVERRIDES = {                   # цвета оружия посочнее, чем в общей палитре
    "wood": 0xdca455, "bandage": 0xeee0bf, "thread": 0x9a937c, "trash_metal": 0x9aa6b4,
    "doll_blue": 0x3f7fe0, "grass_dry": 0xd2b664, "hypostome": 0xe0b673, "dew": 0xf4fbff,
    "brass": 0xe8a92c, "copper": 0xe0682e, "steel": 0xb4c3d4, "hair": 0x3d2414,
    "glass": 0xaef2ff, "plastic_yellow": 0xffc414, "spark": 0x63ecff, "coat": 0xd6d0c0,
    "skin": 0xe8a985, "tape": 0xa7b2bd,
}

def _toon_rgb(hexc):
    import colorsys
    r, g, b = ((hexc >> 16) & 255) / 255, ((hexc >> 8) & 255) / 255, (hexc & 255) / 255
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    def shift(h, target, k):
        d = (target - h + 0.5) % 1.0 - 0.5
        return (h + d * k) % 1.0
    base = colorsys.hsv_to_rgb(h, min(1.0, s * 1.25), v)
    shadow = colorsys.hsv_to_rgb(shift(h, 0.72, 0.12), min(1.0, s * 1.15 + 0.1), v * 0.55)
    light = colorsys.hsv_to_rgb(shift(h, 0.14, 0.1), s * 0.85, min(1.0, v * 1.13 + 0.05))
    return shadow, base, light

def palette_image_toon():
    path = os.path.join(SHARED, "T_Palette_Toon.png")
    img = bpy.data.images.get("T_Palette_Toon")
    if img:
        return img
    PX = 512
    S = PX // N
    img = bpy.data.images.new("T_Palette_Toon", PX, PX, alpha=False)
    pix = [0.0] * (PX * PX * 4)
    for i, (name, hexc) in enumerate(PALETTE):
        bands = _toon_rgb(TOON_OVERRIDES.get(name, hexc))
        cx, cy = i % N, (N - 1) - i // N
        for y in range(S):
            t = y / (S - 1)
            c = bands[0] if t < TOON_BANDS[0] else bands[1] if t < TOON_BANDS[1] else bands[2]
            for x in range(S):
                p = ((cy * S + y) * PX + cx * S + x) * 4
                pix[p:p + 4] = [c[0], c[1], c[2], 1.0]
    img.pixels.foreach_set(pix)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img

def toonify(obj, light=(-0.3, -0.45, 1.0), soft=0.0):
    """Переразвернуть меш на тун-палитру: квадрат цвета берётся из текущей UV, полоса — по нормали
    угла к направлению света (нормали с учётом острых рёбер). soft — сдвиг в сторону света (−1..1)."""
    me = obj.data
    L = Vector(light).normalized()
    uv = me.uv_layers.active.data
    normals = me.corner_normals
    for poly in me.polygons:
        cu = sum(uv[li].uv.x for li in poly.loop_indices) / poly.loop_total
        cv = sum(uv[li].uv.y for li in poly.loop_indices) / poly.loop_total
        cx, cy = min(int(cu * N), N - 1), min(int(cv * N), N - 1)
        i = (N - 1 - cy) * N + cx
        u0, v0, size = swatch_rect(i, margin=0.08)
        for li in poly.loop_indices:
            d = normals[li].vector.dot(L) + soft
            v = min(max(0.5 + 0.5 * d, 0.02), 0.98)
            uv[li].uv = (u0 + 0.5 * size, v0 + v * size)
    for m in me.materials:
        if m and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE":
                    n.image = palette_image_toon()

def add_outline(obj, thickness, name="M_Outline"):
    """Контур «вывернутой оболочкой»: Solidify наружу с вывернутыми нормалями и чёрным материалом.
    Видно только при отсечении задних граней (в UE — односторонний материал, в Workbench — backface culling)."""
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (0.02, 0.015, 0.02, 1)
        mat.use_backface_culling = True
    obj.data.materials.append(mat)
    mod = obj.modifiers.new("Outline", "SOLIDIFY")
    mod.thickness, mod.offset = thickness, 1.0
    mod.use_flip_normals, mod.use_rim = True, False
    mod.use_even_offset = False                      # на остриях «ровная толщина» выстреливает иглами
    mod.use_quality_normals = True
    mod.material_offset = len(obj.data.materials) - 1
    return mod

def palette_material(name, alpha=1.0, toon=False):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None) or nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = palette_image_toon() if toon else palette_image()
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.55
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
    return mat

def swatch_rect(i, margin=0.15):
    cx, cy = i % N, (N - 1) - i // N
    m = margin / N
    return cx / N + m, cy / N + m, 1 / N - 2 * m

def frame(d):
    d = d.normalized()
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(ref).normalized()
    return u, u.cross(d).normalized()

class MeshBuilder:
    """Собирает меш из частей; каждая часть — свой цвет палитры, своя кость, свой слот материала."""

    def __init__(self, seed=7):
        random.seed(seed)
        self.bm = bmesh.new()
        self.L_SW = self.bm.faces.layers.int.new("swatch")
        self.L_PART = self.bm.faces.layers.int.new("part")
        self.L_MAT = self.bm.faces.layers.int.new("mat")
        self.L_BONE = self.bm.verts.layers.int.new("bone")
        self.L_BLEND = self.bm.verts.layers.int.new("blend")   # 0 — жёсткий скин, k — веса из self.blends[k-1]
        self.bones, self.parts, self.blends = [], [], []

    def register(self, verts, faces, sw, bone, mat=0):
        pid = len(self.parts)
        self.parts.append(verts)
        if bone not in self.bones:
            self.bones.append(bone)
        bi = self.bones.index(bone)
        for v in verts:
            v[self.L_BONE] = bi
        for f in faces:
            f[self.L_SW], f[self.L_PART], f[self.L_MAT] = SW[sw], pid, mat
        return faces

    def _linked(self, verts):
        fs = set()
        for v in verts:
            fs.update(v.link_faces)
        return list(fs)

    def ellipsoid(self, center, radii, segs, rings, sw, bone, deform=None, noise=0.0, pole_axis="Z", mat=0):
        verts = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=rings, radius=1.0)["verts"]
        for v in verts:
            x, y, z = v.co
            if pole_axis == "Y":
                y, z = z, y
            elif pole_axis == "X":
                x, z = z, x
            co = Vector((x * radii[0], y * radii[1], z * radii[2]))
            if deform:
                co = deform(co)
            if noise:
                co += co.normalized() * random.uniform(-noise, noise)
            v.co = co + Vector(center)
        return self.register(verts, self._linked(verts), sw, bone, mat)

    def tube(self, pts, radii, sides, sw, bone, mat=0):
        bm = self.bm
        pts = [Vector(p) for p in pts]
        rings, faces = [], []
        for i, p in enumerate(pts):
            u, v = frame(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
            r = radii[i]
            if r < 1e-5:
                rings.append([bm.verts.new(p)])
                continue
            rings.append([bm.verts.new(p + (u * math.cos(a) + v * math.sin(a)) * r)
                          for a in (2 * math.pi * k / sides for k in range(sides))])
        for a, b in zip(rings, rings[1:]):
            if len(b) == 1:
                faces += [bm.faces.new((a[k], a[(k + 1) % len(a)], b[0])) for k in range(len(a))]
            elif len(a) == 1:
                faces += [bm.faces.new((a[0], b[(k + 1) % len(b)], b[k])) for k in range(len(b))]
            else:
                faces += [bm.faces.new((a[k], a[(k + 1) % len(a)], b[(k + 1) % len(b)], b[k]))
                          for k in range(len(a))]
        if len(rings[0]) > 1:
            faces.append(bm.faces.new(list(reversed(rings[0]))))
        if len(rings[-1]) > 1:
            faces.append(bm.faces.new(rings[-1]))
        return self.register([v for r in rings for v in r], faces, sw, bone, mat)

    def ico(self, center, r, sw, bone, mat=0):
        verts = bmesh.ops.create_icosphere(self.bm, subdivisions=1, radius=r)["verts"]
        for v in verts:
            v.co += Vector(center)
        return self.register(verts, self._linked(verts), sw, bone, mat)

    def box(self, start, f, t, length, w0, h0, w1=None, h1=None, sw="joints", bone="root", mat=0, bevel=0.0):
        """Бокс от точки start вдоль оси f на length; t — ось ширины, третья ось — f×t.
        w/h — полуширина/полутолщина у начала (0) и конца (1). bevel — срез рёбер (восьмиугольное сечение)."""
        f = Vector(f).normalized()
        t = (Vector(t) - f * Vector(t).dot(f)).normalized()
        n = f.cross(t)
        w1 = w0 if w1 is None else w1
        h1 = h0 if h1 is None else h1
        start = Vector(start)
        def ring(c, w, h):
            if bevel <= 0:
                pts = [(w, h), (-w, h), (-w, -h), (w, -h)]
            else:
                b = bevel
                pts = [(w, h - b), (w - b, h), (-w + b, h), (-w, h - b),
                       (-w, -h + b), (-w + b, -h), (w - b, -h), (w, -h + b)]
            return [self.bm.verts.new(c + t * x + n * y) for x, y in pts]
        a = ring(start, w0, h0)
        b = ring(start + f * length, w1, h1)
        k = len(a)
        faces = [self.bm.faces.new((a[i], a[(i + 1) % k], b[(i + 1) % k], b[i])) for i in range(k)]
        faces.append(self.bm.faces.new(list(reversed(a))))
        faces.append(self.bm.faces.new(b))
        return self.register(a + b, faces, sw, bone, mat)

    def loft(self, rings, k, sw, bone, mat=0, caps=(True, True), ring_weights=None):
        """Плавная труба по эллиптическим сечениям: rings = [(центр, ось_u, ось_v, полуось_a, полуось_b)].
        Оси у сечений могут быть разными — так рука переходит из круглой в плоскую.
        ring_weights — для каждого сечения {кость: вес} или None (тогда целиком на bone):
        так одна непрерывная поверхность гнётся в суставе без шва."""
        loops = []
        for c, u, v, a, b in rings:
            c, u, v = Vector(c), Vector(u).normalized(), Vector(v).normalized()
            loops.append([self.bm.verts.new(c + u * (a * math.cos(2 * math.pi * i / k))
                                             + v * (b * math.sin(2 * math.pi * i / k))) for i in range(k)])
        faces = []
        for A, B in zip(loops, loops[1:]):
            faces += [self.bm.faces.new((A[i], A[(i + 1) % k], B[(i + 1) % k], B[i])) for i in range(k)]
        if caps[0]:
            faces.append(self.bm.faces.new(list(reversed(loops[0]))))
        if caps[1]:
            faces.append(self.bm.faces.new(loops[-1]))
        res = self.register([v for L in loops for v in L], faces, sw, bone, mat)
        for L, w in zip(loops, ring_weights or []):
            if w:
                for b in w:
                    if b not in self.bones:
                        self.bones.append(b)
                self.blends.append(dict(w))
                for v in L:
                    v[self.L_BLEND] = len(self.blends)
        return res

    def flat(self, outline_rows, sw, bone, mat=0):
        """Плоская полоса (крыло): список рядов вершин одинаковой длины, соединяются квадами."""
        rows = [[self.bm.verts.new(Vector(p)) for p in row] for row in outline_rows]
        faces = []
        for a, b in zip(rows, rows[1:]):
            for k in range(len(a) - 1):
                faces.append(self.bm.faces.new((a[k], a[k + 1], b[k + 1], b[k])))
        return self.register([v for r in rows for v in r], faces, sw, bone, mat)

    def finish(self, name, materials, recalc_normals=True, scale=1.0, uv_mode="part", smooth_angle=None):
        """uv_mode: "part" — у каждой части свой градиент палитры (тёмный низ, светлый верх);
        "flat" — ровный цвет без градиента. smooth_angle (град) — гладкое затенение с острыми рёбрами
        круче этого угла; None — плоское (гранёное)."""
        bm = self.bm
        if scale != 1.0:
            for v in bm.verts:
                v.co *= scale
        if recalc_normals:
            bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[self.L_MAT] == 0])
        uv = bm.loops.layers.uv.new("UVMap")
        bbox = []
        for verts in self.parts:
            xs = [v.co.x for v in verts]; ys = [v.co.y for v in verts]; zs = [v.co.z for v in verts]
            bbox.append((min(xs), max(xs), min(ys), max(ys), min(zs), max(zs),
                         (max(xs) - min(xs)) >= (max(ys) - min(ys))))
        for f in bm.faces:
            x0, x1, y0, y1, z0, z1, hx = bbox[f[self.L_PART]]
            u0, v0, size = swatch_rect(f[self.L_SW])
            for loop in f.loops:
                c = loop.vert.co
                uu = ((c.x - x0) / max(x1 - x0, 1e-4)) if hx else ((c.y - y0) / max(y1 - y0, 1e-4))
                vv = (c.z - z0) / max(z1 - z0, 1e-4)
                if uv_mode == "flat":                 # крошечный участок в середине квадрата — ровный цвет
                    uu, vv = 0.45 + uu * 0.1, 0.45 + vv * 0.1
                loop[uv].uv = (u0 + uu * size, v0 + vv * size)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        mats = [f[self.L_MAT] for f in bm.faces]
        self.vert_bone = [v[self.L_BONE] for v in bm.verts]
        self.vert_blend = [v[self.L_BLEND] for v in bm.verts]
        bm.free()
        for p, m in zip(mesh.polygons, mats):
            p.use_smooth = smooth_angle is not None
            p.material_index = m
        if smooth_angle is not None:
            mesh.set_sharp_from_angle(angle=math.radians(smooth_angle))
        for m in materials:
            mesh.materials.append(m)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        self.obj = obj
        return obj

def build_armature(name, bone_specs, roll_up_prefixes=(), scale=1.0):
    """bone_specs: [(имя, head, tail, parent|None, connect)]. Объект называется Armature (UE его отбрасывает)."""
    data = bpy.data.armatures.new(name)
    arm = bpy.data.objects.new("Armature", data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones
    for bname, head, tail, parent, connect in bone_specs:
        b = eb.new(bname)
        b.head, b.tail, b.roll = Vector(head) * scale, Vector(tail) * scale, 0
        if parent:
            b.parent = eb[parent]
            b.use_connect = connect
    for b in eb:
        if b.name.startswith(roll_up_prefixes):
            b.align_roll(Vector((0, 0, 1)))
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm

def bind_rigid(builder, arm):
    obj = builder.obj
    for name in builder.bones:
        obj.vertex_groups.new(name=name)
    for vi, bi in enumerate(builder.vert_bone):
        blend = builder.vert_blend[vi]
        if blend:
            for bname, w in builder.blends[blend - 1].items():
                obj.vertex_groups[bname].add([vi], w, "REPLACE")
        else:
            obj.vertex_groups[builder.bones[bi]].add([vi], 1.0, "REPLACE")
    obj.parent = arm
    obj.modifiers.new("Armature", "ARMATURE").object = arm

def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

def export_mesh(arm, obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
        apply_scale_options="FBX_SCALE_ALL", add_leaf_bones=False,
        use_armature_deform_only=True, bake_anim=False, mesh_smooth_type="FACE",
        path_mode="COPY", embed_textures=True,
    )

def report(obj, arm):
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    d = obj.dimensions
    print(f"MOB {obj.name}: tris={tris} bones={len(arm.data.bones)} size={d.x:.2f}x{d.y:.2f}x{d.z:.2f} m")
