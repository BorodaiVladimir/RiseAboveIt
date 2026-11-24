# Проверка блокаута «Канавы» по выгрузке (Export/SM_Ditch_*.fbx + ArenaDitch_Layout.csv), как это увидит UE.
#   blender.exe -b --factory-startup --python Arena_Ditch/check_ditch.py
# Код выхода 1, если хоть одна проверка не прошла. Гонять после любой правки build_ditch.py / ditch_shape.py.
# Сетка 0.5 м: клетка проходима, если пол под ней с уклоном < 44° и в росте игрока (0.45–1.9 м над полом) нет коллизии.
# Соседи — перепад ≤ 0.45 м (шаг UE), клетка с непроходимым соседом выкидывается (запас под капсулу ~0.4 м).
import bpy, os, sys, csv, math
from collections import deque
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ditch_shape as S

EXP = os.path.join(HERE, "Export")
fails = []

def need(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
names = sorted(f for f in os.listdir(EXP) if f.startswith("SM_Ditch_") and f.endswith(".fbx")) if os.path.isdir(EXP) else []
need(len(names) >= 6, f"выгрузка: {len(names)} FBX SM_Ditch_*")
csv_path = os.path.join(EXP, "ArenaDitch_Layout.csv")
need(os.path.isfile(csv_path), "есть ArenaDitch_Layout.csv")
if fails:
    print("CHECK FAIL")
    sys.exit(1)
for f in names:
    bpy.ops.import_scene.fbx(filepath=os.path.join(EXP, f))
rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
P = {r["Label"]: Vector((float(r["X"]) / 100, -float(r["Y"]) / 100, float(r["Z"]) / 100)) for r in rows}

def bvh(objs):
    verts, polys = [], []
    for o in objs:
        mw, base = o.matrix_world, len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)

objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
ucx = [o for o in objs if o.name.startswith("UCX_")]
ground_o = [o for o in objs if o.name.startswith("SM_Ditch_Ground")]
need(len(ground_o) == 1, "есть SM_Ditch_Ground")
need(any(o.name.startswith("UCX_SM_Ditch_Boundary") for o in ucx), "у границы есть UCX")
need(any(o.name.startswith("UCX_SM_Ditch_Props") for o in ucx), "у пропсов есть UCX")
G, C = bvh(ground_o), bvh(ucx)
HULLS = []
for o in ucx:
    ws = [o.matrix_world @ v.co for v in o.data.vertices]
    HULLS.append(((Vector([min(p[i] for p in ws) for i in range(3)]), Vector([max(p[i] for p in ws) for i in range(3)])), bvh([o])))

STEP, BODY_LO, BODY_HI = 0.5, 0.45, 1.9
XS = [-86 + STEP * i for i in range(int(172 / STEP) + 1)]
YS = [-62 + STEP * j for j in range(int(124 / STEP) + 1)]
NX, NY = len(XS), len(YS)
H = [[None] * NY for _ in range(NX)]
OK = [[False] * NY for _ in range(NX)]
maxslope_pool, deep_outside, worst_pool = 0.0, [], None

def floor_at(x, y):
    hit = G.ray_cast(Vector((x, y, 80)), Vector((0, 0, -1)))
    return hit if hit[0] else None

def body_blocked(x, y, g):
    up = C.ray_cast(Vector((x, y, g + 0.05)), Vector((0, 0, 1)), BODY_HI - 0.05)
    dn = C.ray_cast(Vector((x, y, g + BODY_HI)), Vector((0, 0, -1)), BODY_HI - BODY_LO)
    return up[0] is not None or dn[0] is not None or inside_ucx(Vector((x, y, g + 0.9)))

def inside_ucx(p):
    """Точка внутри выпуклой UCX: луч вверх и луч вниз упираются в одну и ту же оболочку (нормали не важны)."""
    for (lo, hi), t in HULLS:
        if lo.x <= p.x <= hi.x and lo.y <= p.y <= hi.y and lo.z <= p.z <= hi.z:
            if t.ray_cast(p, Vector((0, 0, 1)))[0] is not None and t.ray_cast(p, Vector((0, 0, -1)))[0] is not None:
                return True
    return False

for i, x in enumerate(XS):
    for j, y in enumerate(YS):
        hit = floor_at(x, y)
        if not hit:
            continue
        g, n = hit[0].z, hit[1]
        H[i][j] = g
        slope = math.degrees(math.acos(max(-1, min(1, abs(n.z)))))
        in_pool = any(math.hypot(x - px, y - py) < p[2] for p in S.POOLS for px, py in [S.pool_xy(p)])
        if in_pool:
            if slope > maxslope_pool:
                maxslope_pool, worst_pool = slope, (x, y, round(g, 2))
        elif g < -1.0:
            deep_outside.append((round(x, 1), round(y, 1), round(g, 2)))
        OK[i][j] = slope < 44 and not body_blocked(x, y, g)
# запас под капсулу
OK2 = [[OK[i][j] and all(0 <= i + a < NX and 0 <= j + b < NY and OK[i + a][j + b]
                         for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))) for j in range(NY)] for i in range(NX)]

def cell(p):
    return int(round((p.x - XS[0]) / STEP)), int(round((p.y - YS[0]) / STEP))

start = cell(P["PlayerStart"])
need(OK2[start[0]][start[1]], f"PlayerStart стоит на проходимой клетке {tuple(round(c, 2) for c in P['PlayerStart'])}")
seen = [[False] * NY for _ in range(NX)]
q = deque([start]); seen[start[0]][start[1]] = True
while q:
    i, j = q.popleft()
    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        u, v = i + a, j + b
        if 0 <= u < NX and 0 <= v < NY and not seen[u][v] and OK2[u][v] and abs(H[u][v] - H[i][j]) <= 0.45:
            seen[u][v] = True
            q.append((u, v))
reach = [(XS[i], YS[j], H[i][j]) for i in range(NX) for j in range(NY) if seen[i][j]]
print(f"CHECK reachable cells {len(reach)} ({len(reach) * STEP * STEP:.0f} м²)")

def reached_near(p, r):
    return any(math.hypot(x - p.x, y - p.y) <= r for x, y, _ in reach)

need(reached_near(P["Spawn_Boss"], 2.0), "от старта доходим до точки босса (≤ 2 м)")
need(reached_near(Vector((S.BOSS_X, S.yc(S.BOSS_X), 0)), 1.0), "от старта доходим до центра площадки босса")
need(reached_near(P["SafeZone_Workbench"], 2.6), "от старта доходим до верстака в банке (≤ 2.6 м)")
need(max(g for _, _, g in reach) < 2.5, f"на склоны не забраться: выше всего {max(g for _, _, g in reach):.2f} м")
PY = S.yc(S.PIPE_X)
in_pipe = [x for x, y, _ in reach if abs(y - PY) < S.PIPE_R_IN and x > S.PIPE_X]
need(not in_pipe or max(in_pipe) < S.PIPE_GRATE, f"за решётку в трубе не пройти: дальше всего x = {max(in_pipe or [0]):.1f}")
need(bool(in_pipe), "в устье трубы заходим (там спавн босса)")
need(maxslope_pool < 35, f"из бочагов выйти: уклон ≤ {maxslope_pool:.1f}° (< 35°)")
need(not deep_outside, f"ям глубже 1 м вне бочагов нет ({deep_outside[:5]})")

for lab, p in P.items():
    if not lab.startswith("Spawn_"):
        continue
    hit = floor_at(p.x, p.y)
    g = hit[0].z if hit else -99
    if lab.startswith("Spawn_Water"):
        need(abs(p.z - S.WATER_Z) < 0.11 and g < S.WATER_Z - 0.1, f"{lab} на воде (z {p.z:.2f}, дно {g:.2f})")
    else:
        need(0 <= p.z - g <= 1.5, f"{lab} над полом на {p.z - g:.2f} м")
    near = C.find_nearest(Vector((p.x, p.y, g + 0.9)))
    d = near[3] if near[0] else 99
    need(d > 0.6, f"{lab} не в коллизии: до UCX {d:.2f} м")
    need(reached_near(p, 2.5), f"{lab}: от него можно дойти до игрока")

if os.environ.get("DITCH_DEBUG"):
    print("DBG worst pool cell", worst_pool, [o.name for o in ucx if "Pipe" in o.name][-6:])
    print("DBG pipe", sorted({(x, round(y - PY, 1), round(g, 2)) for x, y, g in reach if abs(y - PY) < S.PIPE_R_IN and x > S.PIPE_GRATE - 1})[:40])
    for p in S.POOLS:
        px, py = S.pool_xy(p)
        worst = max(((math.degrees(math.acos(abs(floor_at(px + dx, py + dy)[1].z))), dx, dy) for dx in [k * 0.5 for k in range(-14, 15)] for dy in [k * 0.5 for k in range(-14, 15)] if math.hypot(dx, dy) < p[2]))
        print("DBG pool", p, worst)

print("CHECK PASS" if not fails else f"CHECK FAIL ({len(fails)})")
sys.exit(1 if fails else 0)
