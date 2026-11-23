# Блокаут локации «Канава» для UE (серый черновик под проверку геймплея; арт — позже).
# Запуск: blender.exe -b --factory-startup --python Arena_Ditch/build_ditch.py
# Пишет в Arena_Ditch/Export/ (все меши в начале координат, ставятся в (0,0,0) уровня):
#   SM_Ditch_Ground   — дно, склоны, верх и дальняя земля (в UE коллизия complex as simple)
#   SM_Ditch_Water    — ручей и бочаги (без коллизии, по дну ходят вброд)
#   SM_Ditch_Props    — кочки, коряги, камни (UCX)
#   SM_Ditch_Reeds    — тростник по верху склонов (без коллизии, силуэт «канавы»)
#   SM_Ditch_Pipe     — бетонный водопропуск в торце + решётка (UCX), перед ним площадка босса
#   SM_Ditch_SafeZone — консервная банка на боку у старта (UCX), внутри верстак SM_Safe_Workbench из «Земли»
#   SM_Ditch_Boundary — невидимая стена по верху склонов (UCX, в UE Hidden in Game)
#   ArenaDitch_Layout.csv — PlayerStart, спавны, safe zone, триггер арены босса (см, оси UE)
# Форма — в ditch_shape.py (её же читает check_ditch.py). Масштаб ×35.
import bpy, bmesh, math, random, os, sys, csv
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "Shared"))
sys.path.insert(0, HERE)
import lowpoly as lp
import ditch_shape as S
from ditch_shape import ground_z, yc, half_width, smooth

OUT = os.path.join(HERE, "Export")
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.startswith("SM_Ditch_") or f == "ArenaDitch_Layout.csv":
        os.remove(os.path.join(OUT, f))
lp.clear_scene()
MATS = [lp.palette_material("M_Palette"), lp.palette_material("M_Palette_TwoSided"),
        lp.palette_material("M_Water"), lp.palette_material("M_Glow")]
OPAQUE, TWO_SIDED, WATER, GLOW = range(4)

# ------------------------------------------------------------------ примитивы
def frame(d):
    d = d.normalized()
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(ref).normalized()
    return u, u.cross(d).normalized()

def ico(mb, subdiv):
    t = bmesh.new()
    bmesh.ops.create_icosphere(t, subdivisions=subdiv, radius=1.0)
    m = {v: mb.bm.verts.new(v.co) for v in t.verts}
    faces = [mb.bm.faces.new([m[v] for v in f.verts]) for f in t.faces]
    t.free()
    return list(m.values()), faces

def tube(mb, pts, radii, sides, sw, mat=OPAQUE, caps=True):
    rings = []
    for i, p in enumerate(pts):
        u, v = frame(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        rings.append([mb.bm.verts.new(p + (u * math.cos(2 * math.pi * k / sides) + v * math.sin(2 * math.pi * k / sides)) * radii[i])
                      for k in range(sides)])
    faces = []
    for A, B in zip(rings, rings[1:]):
        faces += [mb.bm.faces.new((A[k], A[(k + 1) % sides], B[(k + 1) % sides], B[k])) for k in range(sides)]
    if caps:
        faces += [mb.bm.faces.new(list(reversed(rings[0]))), mb.bm.faces.new(rings[-1])]
    mb.register([v for r in rings for v in r], faces, sw, "root", mat)
    return [[v.co.copy() for v in r] for r in rings]

def cuboid(mb, pts8, sw, mat=OPAQUE):
    """Брусок по 8 углам в порядке (x0/x1, y0/y1, z0/z1)."""
    vs = [mb.bm.verts.new(p) for p in pts8]
    idx = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))
    mb.register(vs, [mb.bm.faces.new([vs[i] for i in q]) for q in idx], sw, "root", mat)

def aabb(lo, hi):
    return [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]

def finish(mb, name, smooth_angle):
    obj = mb.finish(name, MATS, uv_mode="flat", smooth_angle=smooth_angle)
    print(f"DITCH {name}: {sum(len(p.vertices) - 2 for p in obj.data.polygons)} tris")
    return obj

def ucx(owner, idx, points):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in points]
    bmesh.ops.convex_hull(bm, input=vs)
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    me = bpy.data.meshes.new(f"UCX_{owner}_{idx:02d}")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(me.name, me)
    bpy.context.scene.collection.objects.link(o)
    return o

def export(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + ".fbx"), use_selection=True, object_types={"MESH"},
                             apply_scale_options="FBX_SCALE_ALL", add_leaf_bones=False, bake_anim=False,
                             mesh_smooth_type="FACE", path_mode="COPY", embed_textures=True)

def put(owner, mb_obj, cols):
    export([mb_obj] + [ucx(owner, i, p) for i, p in enumerate(cols)], owner)

# ------------------------------------------------------------------ земля: сетка 1.25 м по канаве + крупная дальняя
GX0, GX1, GY = -100.0, 95.0, 70.0
CELL = 1.25
mb = lp.MeshBuilder(seed=1)
NI, NJ = int((GX1 - GX0) / CELL), int(2 * GY / CELL)
grid = [[mb.bm.verts.new((GX0 + CELL * i, -GY + CELL * j, 0)) for j in range(NJ + 1)] for i in range(NI + 1)]
for row in grid:
    for v in row:
        v.co.z = ground_z(v.co.x, v.co.y)
by_sw = {"mud": [], "soil_dark": [], "frog_dark": [], "grass_back": []}
for i in range(NI):
    for j in range(NJ):
        a, b, c, d = grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]
        cen = (a.co + c.co) / 2
        e = S.outside(cen.x, cen.y)
        sw = "grass_back" if cen.z > S.TOP_Z - 0.3 else "frog_dark" if e > 0.5 else "soil_dark" if cen.z < S.WATER_Z else "mud"
        tris = [(a, b, c), (a, c, d)] if (i + j) % 2 else [(a, b, d), (b, c, d)]
        by_sw[sw] += [mb.bm.faces.new(t) for t in tris]
FAR, FC = 600.0, 60.0
M = int(2 * FAR / FC)
far = [[mb.bm.verts.new((-FAR + FC * i, -FAR + FC * j, S.TOP_Z)) for j in range(M + 1)] for i in range(M + 1)]
for i in range(M):
    for j in range(M):
        x0, y0 = -FAR + FC * i, -FAR + FC * j
        if x0 + FC > GX0 and x0 < GX1 and y0 + FC > -GY and y0 < GY:
            continue                                                  # под мелкой сеткой — дыра (с перекрытием по краю)
        by_sw["grass_back"].append(mb.bm.faces.new((far[i][j], far[i + 1][j], far[i + 1][j + 1], far[i][j + 1])))
# щель между мелкой сеткой и дырой крупной — заполняем полосами на высоте верха
def strip(x0, y0, x1, y1):
    vs = [mb.bm.verts.new((x, y, S.TOP_Z)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    by_sw["grass_back"].append(mb.bm.faces.new(vs))
hx0, hx1 = -FAR + FC * math.floor((GX0 + FAR) / FC), -FAR + FC * math.ceil((GX1 + FAR) / FC)
hy = -FAR + FC * math.ceil((GY + FAR) / FC)
strip(hx0, -hy, GX0, hy); strip(GX1, -hy, hx1, hy)
strip(GX0, GY, GX1, hy); strip(GX0, -hy, GX1, -GY)
for v in [v for v in mb.bm.verts if not v.link_faces]:
    mb.bm.verts.remove(v)
for sw, faces in by_sw.items():
    mb.register(list({v for f in faces for v in f.verts}), faces, sw, "root")
ground = finish(mb, "SM_Ditch_Ground", 35)
export([ground], "SM_Ditch_Ground")

# ------------------------------------------------------------------ вода: клетки 1 м там, где дно ниже воды
mb = lp.MeshBuilder(seed=2)
faces, verts = [], {}
def wv(i, j):
    if (i, j) not in verts:
        verts[(i, j)] = mb.bm.verts.new((i * 1.0, j * 1.0, S.WATER_Z))
    return verts[(i, j)]
for i in range(int(S.X0) - 1, int(S.X1) + 2):
    for j in range(-40, 41):
        if min(ground_z(i + a, j + b) for a in (0, 0.5, 1) for b in (0, 0.5, 1)) < S.WATER_Z + 0.02 and \
                max(ground_z(i + a, j + b) for a in (0, 1) for b in (0, 1)) < S.WATER_Z + 0.35:
            faces.append(mb.bm.faces.new((wv(i, j), wv(i + 1, j), wv(i + 1, j + 1), wv(i, j + 1))))
mb.register(list(verts.values()), faces, "water", "root", WATER)
water = finish(mb, "SM_Ditch_Water", None)
export([water], "SM_Ditch_Water")

# ------------------------------------------------------------------ пропсы: кочки, коряги, камни
rng = random.Random(41)
mb = lp.MeshBuilder(seed=3)
cols = []
def at(x, d):
    return Vector((x, yc(x) + d, 0))

def hummock(c, r, h):
    vs, fs = ico(mb, 2)
    gz = ground_z(c.x, c.y)
    for v in vs:
        p = v.co.copy()
        k = 1 + 0.15 * math.sin(p.x * 3 + c.x) * math.sin(p.y * 3 + c.y)
        v.co = Vector((c.x + p.x * r * k, c.y + p.y * r * k * 0.9, gz - 0.4 + (p.z + 0.35) * h * 0.75))
    mb.register(vs, fs, rng.choice(["frog_dark", "grass_back", "frog_green"]), "root")
    cols.append([v.co.copy() for v in vs])

def log(c, yaw, L, r):
    d = Vector((math.cos(yaw), math.sin(yaw), 0))
    pts = []
    for k in range(4):
        p = c + d * (L * (k / 3 - 0.5))
        p = Vector((p.x, p.y, ground_z(p.x, p.y) + r * 0.45 + 0.15 * math.sin(k * 1.7)))
        pts.append(p)
    rings = tube(mb, pts, [r * 1.05, r, r * 0.95, r * 0.85], 8, rng.choice(["bark", "wood_dry"]))
    cols.extend(ra + rb for ra, rb in zip(rings, rings[1:]))
    # обломанный сук
    b0 = pts[1] + Vector((0, 0, r * 0.6))
    b1 = b0 + Vector((-d.y, d.x, 0)) * (r * 2.5) + Vector((0, 0, r * 1.8))
    tube(mb, [b0, b1], [r * 0.35, r * 0.2], 6, "bark")

def stone(c, s, sw):
    vs, fs = ico(mb, 2)
    gz = ground_z(c.x, c.y)
    Rz = Matrix.Rotation(rng.uniform(0, 6.3), 3, "Z")
    for v in vs:
        p = v.co * (1 + 0.15 * math.sin(v.co.x * 4 + c.x))
        v.co = Rz @ Vector((p.x * s * 1.1, p.y * s * 0.85, p.z * s * 0.6)) + Vector((c.x, c.y, gz + s * 0.15))
    mb.register(vs, fs, sw, "root")
    cols.append([v.co.copy() for v in vs])

# зона боя x −50…25: укрытия по обе стороны, середина свободна под проход
for x, d, r, h in [(-48, 8, 2.4, 1.4), (-41, -9, 3.0, 1.8), (-34, 3, 2.0, 1.2), (-22, -8, 2.6, 1.5), (-16, 9, 3.2, 1.7),
                   (-6, -3, 2.2, 1.3), (8, -9, 2.8, 1.6), (14, 10, 2.4, 1.4), (20, 2, 2.0, 1.1), (33, 12, 2.6, 1.5)]:
    hummock(at(x, d), r, h)
for x, d, yaw, L, r in [(-38, 2, 0.5, 12, 1.0), (-12, -2, -0.35, 14, 1.2), (5, 3, 1.9, 10, 0.9), (14, -10.5, 0.15, 12, 1.1)]:
    log(at(x, d), yaw, L, r)
for x, d, s, sw in [(-55, -8, 1.8, "stone"), (-27, 10, 2.2, "stone_b"), (-3, 8, 1.4, "stone"), (11, -4, 1.6, "stone_b"),
                    (30, 7, 1.3, "stone"), (52, -12, 2.0, "stone_b")]:
    stone(at(x, d), s, sw)
props = finish(mb, "SM_Ditch_Props", 50)
put("SM_Ditch_Props", props, cols)

# ------------------------------------------------------------------ тростник по верху склонов
rng = random.Random(52)
mb = lp.MeshBuilder(seed=4)
n_reeds = 0
for k in range(260):
    side = 1 if k % 2 else -1
    if k % 13 == 0:                                                   # за торцами
        x = rng.choice([S.X0 - S.BANK_RUN - rng.uniform(0, 8), S.X1 + S.BANK_RUN + rng.uniform(0, 8)])
        y = yc(x) + rng.uniform(-25, 25)
    else:
        x = rng.uniform(S.X0 - 10, S.X1 + 14)
        y = yc(x) + side * (half_width(x) + S.BANK_RUN * rng.uniform(0.55, 1.0) + rng.uniform(0, 12) ** 1.3)
    gz = ground_z(x, y)
    h, r = rng.uniform(22, 40), rng.uniform(0.35, 0.7)                 # стебель 1–2 см → 0.35–0.7 м, 0.6–1.1 м → 22–40 м
    lean = Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12) - side * 0.08, 1)).normalized()
    pts = [Vector((x, y, gz - 0.5)) + lean * h * t + Vector((0, 0, 0)) for t in (0, 0.35, 0.7, 1.0)]
    for i in range(1, 4):
        pts[i] += Vector((lean.x, lean.y, 0)) * h * 0.05 * i * i
    tube(mb, pts, [r, r * 0.85, r * 0.6, r * 0.15], 5, rng.choice(["grass", "grass_b", "grass_dry", "frog_green"]))
    if rng.random() < 0.3:                                            # початок рогоза
        top = pts[-1] - (pts[-1] - pts[-2]).normalized() * 3
        tube(mb, [top - (pts[-1] - pts[-2]).normalized() * 6, top], [r * 1.9, r * 1.9], 6, "mud")
    n_reeds += 1
reeds = finish(mb, "SM_Ditch_Reeds", 40)
export([reeds], "SM_Ditch_Reeds")
print(f"DITCH reeds={n_reeds}")

# ------------------------------------------------------------------ водопропуск: бетонная труба в торце + решётка
mb = lp.MeshBuilder(seed=5)
cols = []
PY = yc(S.PIPE_X)
PZ = S.PIPE_R_IN - 0.8                     # низ трубы на 0.8 м под илом
SIDES = 20
L0, L1 = S.PIPE_X, S.X1 + S.BANK_RUN + 4
def ring(r, x):
    return [Vector((x, PY + math.cos(2 * math.pi * k / SIDES) * r, PZ + math.sin(2 * math.pi * k / SIDES) * r)) for k in range(SIDES)]
R = [ring(S.PIPE_R_OUT, L1), ring(S.PIPE_R_OUT, L0), ring(S.PIPE_R_IN, L0), ring(S.PIPE_R_IN, L1)]
V = [[mb.bm.verts.new(p) for p in r] for r in R]
fs = [mb.bm.faces.new((A[k], A[(k + 1) % SIDES], B[(k + 1) % SIDES], B[k])) for A, B in zip(V, V[1:]) for k in range(SIDES)]
mb.register([v for r in V for v in r], fs, "stone", "root")
# UCX: стенка трубы кусками (каждый выпуклый)
for k in range(SIDES):
    k2 = (k + 1) % SIDES
    cols.append([R[0][k], R[0][k2], R[1][k], R[1][k2], R[2][k], R[2][k2], R[3][k], R[3][k2]])
# оголовок — бетонная плита вокруг устья
for y0, y1, z0, z1 in ((PY - 9, PY - S.PIPE_R_OUT + 0.4, -1, PZ + 4), (PY + S.PIPE_R_OUT - 0.4, PY + 9, -1, PZ + 4),
                       (PY - 9, PY + 9, PZ + S.PIPE_R_OUT - 0.4, PZ + S.PIPE_R_OUT + 1.6)):
    pts = aabb((L0 + 0.3, y0, z0), (L0 + 1.3, y1, z1))
    cuboid(mb, pts, "stone_b")
    cols.append(pts)
# ржавая решётка: вертикальные прутья + две перекладины, одна коллизия-плита
for k in range(-4, 5):
    y = PY + k * 1.05
    h = math.sqrt(max(S.PIPE_R_IN ** 2 - (y - PY) ** 2, 0.0))
    tube(mb, [Vector((S.PIPE_GRATE, y, PZ - h)), Vector((S.PIPE_GRATE, y, PZ + h))], [0.12, 0.12], 5, "trash_metal")
for z in (PZ - 1.5, PZ + 1.5):
    h = math.sqrt(S.PIPE_R_IN ** 2 - (z - PZ) ** 2)
    tube(mb, [Vector((S.PIPE_GRATE, PY - h, z)), Vector((S.PIPE_GRATE, PY + h, z))], [0.12, 0.12], 5, "trash_metal")
cols.append(aabb((S.PIPE_GRATE - 0.3, PY - S.PIPE_R_IN, PZ - S.PIPE_R_IN), (S.PIPE_GRATE + 0.3, PY + S.PIPE_R_IN, PZ + S.PIPE_R_IN)))
# темнота за решёткой — заглушка, чтобы не было видно склона изнутри
vs = [mb.bm.verts.new(p) for p in ring(S.PIPE_R_IN - 0.05, S.PIPE_GRATE + 2.5)]
mb.register(vs, [mb.bm.faces.new(list(reversed(vs)))], "eye_black", "root")
pipe = finish(mb, "SM_Ditch_Pipe", 30)
put("SM_Ditch_Pipe", pipe, cols)

# ------------------------------------------------------------------ safe zone: консервная банка на боку
mb = lp.MeshBuilder(seed=6)
cols = []
CY = yc((S.CAN_X0 + S.CAN_X1) / 2)
CZ = S.CAN_R - S.CAN_SINK
T = 0.15
CS = 24
def cring(r, x):
    return [Vector((x, CY + math.cos(2 * math.pi * k / CS) * r, CZ + math.sin(2 * math.pi * k / CS) * r)) for k in range(CS)]
# обечайка с рёбрами жёсткости (чередование радиуса)
xs = [S.CAN_X0 + (S.CAN_X1 - S.CAN_X0) * t for t in [i / 10 for i in range(11)]]
outer = [cring(S.CAN_R + (0.12 if i % 2 else 0.0), x) for i, x in enumerate(xs)]
inner = [cring(S.CAN_R - T, x) for x in xs]
OV = [[mb.bm.verts.new(p) for p in r] for r in outer]
IV = [[mb.bm.verts.new(p) for p in r] for r in inner]
fs = [mb.bm.faces.new((A[k], A[(k + 1) % CS], B[(k + 1) % CS], B[k])) for A, B in zip(OV, OV[1:]) for k in range(CS)]
fs += [mb.bm.faces.new((B[k], B[(k + 1) % CS], A[(k + 1) % CS], A[k])) for A, B in zip(IV, IV[1:]) for k in range(CS)]
fs += [mb.bm.faces.new((OV[-1][k], OV[-1][(k + 1) % CS], IV[-1][(k + 1) % CS], IV[-1][k])) for k in range(CS)]   # кромка
mb.register([v for r in OV + IV for v in r], fs, "can_alu", "root")
# дно банки (закрытый конец)
cap = [mb.bm.verts.new(p) for p in cring(S.CAN_R, S.CAN_X0 - 0.01)]
mb.register(cap, [mb.bm.faces.new(list(reversed(cap)))], "trash_metal", "root")
for k in range(CS):
    k2 = (k + 1) % CS
    cols.append([outer[0][k], outer[0][k2], outer[-1][k], outer[-1][k2], inner[0][k], inner[0][k2], inner[-1][k], inner[-1][k2]])
cols.append(cring(S.CAN_R, S.CAN_X0 - 0.01) + cring(S.CAN_R, S.CAN_X0 + 0.2))
# отогнутая крышка на «петле» сверху открытого конца
lid_c = Vector((S.CAN_X1 + 2.2, CY, CZ + S.CAN_R + 1.9))
lid = [mb.bm.verts.new(lid_c + Matrix.Rotation(-0.9, 3, "Y") @ Vector((0, math.cos(a) * S.CAN_R, math.sin(a) * S.CAN_R)))
       for a in (2 * math.pi * k / CS for k in range(CS))]
mb.register(lid, [mb.bm.faces.new(lid)], "can_alu", "root", TWO_SIDED)
# этикетка — полоса на боку
lab = [cring(S.CAN_R + 0.14, x) for x in (S.CAN_X0 + 2.5, S.CAN_X1 - 2.0)]
LV = [[mb.bm.verts.new(p) for p in r[2:13]] for r in lab]
mb.register([v for r in LV for v in r], [mb.bm.faces.new((LV[0][k], LV[0][k + 1], LV[1][k + 1], LV[1][k])) for k in range(10)], "cap_red", "root")
# лампочка-светодиод под «потолком» банки
led = Vector((S.CAN_X0 + 3.0, CY, CZ + S.CAN_R - T))
tube(mb, [led, led - Vector((0, 0, 0.7))], [0.3, 0.0001], 8, "emissive", GLOW)
safe = finish(mb, "SM_Ditch_SafeZone", 30)
put("SM_Ditch_SafeZone", safe, cols)

# ------------------------------------------------------------------ невидимая граница по верху склонов
mb = lp.MeshBuilder(seed=7)
EDGE = S.BANK_RUN + 1.0
xa, xb = S.X0 - EDGE, S.X1 + EDGE
left = [Vector((x, yc(x) - half_width(min(max(x, S.X0), S.X1)) - EDGE, 0)) for x in [xa + (xb - xa) * t / 30 for t in range(31)]]
right = [Vector((x, yc(x) + half_width(min(max(x, S.X0), S.X1)) + EDGE, 0)) for x in [xa + (xb - xa) * t / 30 for t in range(31)]]
loop = left + list(reversed(right))
Z0, Z1 = S.TOP_Z - 3, S.TOP_Z + 40
lo = [mb.bm.verts.new(p + Vector((0, 0, Z0))) for p in loop]
hi = [mb.bm.verts.new(p + Vector((0, 0, Z1))) for p in loop]
n = len(loop)
mb.register(lo + hi, [mb.bm.faces.new((lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k])) for k in range(n)], "grass_back", "root", TWO_SIDED)
wall = finish(mb, "SM_Ditch_Boundary", None)
wcols = []
for k in range(n):
    a, b = loop[k], loop[(k + 1) % n]
    mid = (a + b) / 2
    inside = Vector((min(max(mid.x, S.X0), S.X1), yc(min(max(mid.x, S.X0), S.X1)), 0))
    t = (b - a).normalized()
    nrm = Vector((t.y, -t.x, 0))
    if nrm.dot(mid - inside) < 0:
        nrm = -nrm
    pts = [a - nrm * 0.2, b - nrm * 0.2, a + nrm * 2, b + nrm * 2]
    wcols.append([p + Vector((0, 0, Z0)) for p in pts] + [p + Vector((0, 0, Z1)) for p in pts])
export([wall] + [ucx("SM_Ditch_Boundary", k, p) for k, p in enumerate(wcols)], "SM_Ditch_Boundary")

# ------------------------------------------------------------------ расстановка для UE: см, Y Blender → −Y UE, yaw UE = −yaw Blender
def ue(p):
    return round(p.x * 100, 1), round(-p.y * 100, 1), round(p.z * 100, 1)

def look_yaw(frm, to):
    d = Vector(to) - Vector(frm)
    return round(math.degrees(math.atan2(-d.y, d.x)), 1)

rows = []
def row(label, kind, p, yaw=0.0, asset="", note=""):
    x, y, z = ue(p)
    rows.append(dict(Label=label, Kind=kind, Asset=asset, X=x, Y=y, Z=z, Yaw=yaw, Note=note))

for name in ["SM_Ditch_Ground", "SM_Ditch_Water", "SM_Ditch_Props", "SM_Ditch_Reeds", "SM_Ditch_Pipe", "SM_Ditch_SafeZone",
             "SM_Ditch_Boundary"]:
    rows.append(dict(Label=name, Kind="StaticMesh", Asset=name, X=0, Y=0, Z=0, Yaw=0,
                     Note="Hidden in Game, коллизия BlockAll" if name == "SM_Ditch_Boundary" else ""))
boss_c = Vector((S.BOSS_X, yc(S.BOSS_X), 0))
ps = Vector((S.START_X, yc(S.START_X), ground_z(S.START_X, yc(S.START_X)) + 0.95))
row("PlayerStart", "PlayerStart", ps, look_yaw(ps, boss_c), note="у банки (safe zone), смотрит вдоль канавы на трубу")
bench = Vector((S.CAN_X0 + 4.0, CY, ground_z(S.CAN_X0 + 4.0, CY)))
row("SafeZone_Workbench", "StaticMesh", bench, 90.0, "SM_Safe_Workbench", "верстак из Arena_Earth; оружие класть на верх пуговицы, 96 см от низа")
row("SafeZone_Light", "PointLight", led - Vector((0, 0, 1.0)), note="светодиод под «потолком» банки: тёплый, радиус ~12 м")
L = S.CAN_X1 - S.CAN_X0
row("SafeZone_Trigger", "TriggerBox", Vector(((S.CAN_X0 + S.CAN_X1) / 2 + 0.5, CY, 2.0)), 0.0,
    note=f"зона безопасности: {(L + 1) * 100:.0f}x{(2 * S.CAN_R) * 100:.0f}x400 см (внутренность банки, X вдоль канавы)")
for k, (x, d) in enumerate(((-44, -10.5), (-31, 12),(-8, -11), (10, 12.5), (24, -12))):
    p = Vector((x, yc(x) + d, 0))
    p.z = ground_z(p.x, p.y) + 0.3
    row(f"Spawn_Ground_{k + 1:02d}", "TargetPoint", p, look_yaw(p, (x, yc(x), 0)),
        note="наземные (ящерицы, змеи, жабы-танки) — у подножия склона")
water_pts = [Vector(S.pool_xy(p)) for p in S.POOLS] + [Vector((-14.0, S.stream_y(-14.0)))]
for k, c in enumerate(water_pts):
    p = Vector((c.x, c.y, S.WATER_Z))
    row(f"Spawn_Water_{k + 1:02d}", "TargetPoint", p, look_yaw(p, (c.x, yc(c.x), 0)),
        note="водяные (лягушки, жабы) — из бочагов и ручья, на воде")
bp = Vector((S.PIPE_X + 3.0, PY, ground_z(S.PIPE_X + 3.0, PY) + 0.3))
row("Spawn_Boss", "TargetPoint", bp, look_yaw(bp, boss_c), note="босс-мышь выходит из трубы на площадку")
row("BossArena_Trigger", "TriggerBox", Vector((boss_c.x, boss_c.y, 4.0)), 0.0,
    note=f"арена босса: {2 * S.BOSS_R * 100:.0f}x{2 * S.BOSS_R * 100:.0f}x800 см (круг r {S.BOSS_R:.0f} м перед устьем трубы)")
with open(os.path.join(OUT, "ArenaDitch_Layout.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["Label", "Kind", "Asset", "X", "Y", "Z", "Yaw", "Note"])
    w.writeheader()
    w.writerows(rows)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Arena_Ditch.blend"))
print(f"DITCH done: {len(rows)} строк расстановки")
