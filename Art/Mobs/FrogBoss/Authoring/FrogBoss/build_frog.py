# Босс «Земли» — лягушка-сеголетка (issue #8 «First Boss T1»).
# Запуск: blender.exe -b --factory-startup --python build_frog.py [-- toon]
# Масштаб ×257: сеголетка 27 мм от морды до клоаки → 7 м. Сидит ~4 м в высоту (с глазами), ширина ~5.5 м.
# Механики под анимации: язык-гарпун (цепочка из 8 костей, тянется на ~14 м вперёд), прыжок с ударной волной,
# раздувающийся горловой мешок (кваканье — призыв мошкары), глаза втягиваются при моргании и глотании.
# Всё ниже задано в долях длины тела (SVL = 1) и умножается на S при сборке. Смотрит в −Y,
# начало координат — на земле под центром тела. +X — левая сторона лягушки.
import bpy, math, os, sys, random
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "Shared"))
import lowpoly as lp

TOON = "toon" in sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else False
S = 8.0                                   # метров на одну длину тела (крупнее реальной сеголетки — босс)
SIDES = ((1, "l"), (-1, "r"))
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
V = Vector

lp.clear_scene()
mb = lp.MeshBuilder(seed=33)
mat = lp.palette_material("M_Palette_Toon" if TOON else "M_FrogBoss", toon=TOON)   # имя = слот в UE (SLOT_MATERIALS)

# ---------------------------------------------------------------- тело: голова → грудь → таз одной поверхностью
# (y, центр z, полуширина, полувысота, веса костей) — сечения от морды к заду
HEAD_W, CHEST_W, PELV_W = {"head": 1.0}, {"chest": 1.0}, {"pelvis": 1.0}
BODY = [(-0.53, 0.405, 0.03, 0.02, HEAD_W), (-0.50, 0.41, 0.11, 0.055, HEAD_W), (-0.45, 0.42, 0.17, 0.075, HEAD_W),
        (-0.38, 0.43, 0.23, 0.09, HEAD_W), (-0.30, 0.44, 0.28, 0.105, HEAD_W),
        (-0.22, 0.445, 0.31, 0.125, {"head": 0.6, "chest": 0.4}), (-0.12, 0.43, 0.33, 0.16, CHEST_W),
        (0.00, 0.39, 0.34, 0.19, CHEST_W), (0.12, 0.34, 0.33, 0.20, {"chest": 0.5, "pelvis": 0.5}),
        (0.24, 0.28, 0.30, 0.19, PELV_W), (0.35, 0.225, 0.26, 0.165, PELV_W), (0.43, 0.19, 0.22, 0.14, PELV_W),
        (0.49, 0.175, 0.16, 0.105, PELV_W), (0.525, 0.17, 0.08, 0.055, PELV_W), (0.54, 0.17, 0.015, 0.012, PELV_W)]

def body_at(y):
    """Центр z, полуширина и полувысота тела в сечении y."""
    y = min(max(y, BODY[0][0]), BODY[-1][0])
    for (y0, z0, a0, b0, _), (y1, z1, a1, b1, _) in zip(BODY, BODY[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return z0 + (z1 - z0) * t, a0 + (a1 - a0) * t, b0 + (b1 - b0) * t

def top(x, y, lift=0.0):
    """Точка на верхней поверхности тела над (x, y) и примерная нормаль."""
    zc, a, b = body_at(y)
    u = min(abs(x) / a, 0.98)
    z = zc + b * math.sqrt(1 - u * u)
    n = V((x / (a * a), 0, (z - zc) / (b * b))).normalized()
    return V((x, y, z)) + n * lift, n

def body_bone(y):
    return "head" if y < -0.2 else "chest" if y < 0.12 else "pelvis"

mb.loft([((0, y, z), X, Z, a, b) for y, z, a, b, _ in BODY], 16, "frog_green", "chest",
        ring_weights=[w for *_, w in BODY])

# брюхо — светлое, снизу груди и таза
mb.ellipsoid((0, 0.04, 0.215), (0.27, 0.3, 0.075), 12, 6, "frog_belly", "chest")
mb.ellipsoid((0, 0.27, 0.12), (0.2, 0.17, 0.06), 10, 5, "frog_belly", "pelvis")

# ---------------------------------------------------------------- нижняя челюсть, рот, горловой мешок, язык
JAW = [(-0.52, 0.385, 0.03, 0.02), (-0.49, 0.375, 0.105, 0.04), (-0.44, 0.365, 0.165, 0.055),
       (-0.37, 0.357, 0.225, 0.065), (-0.29, 0.352, 0.27, 0.075), (-0.20, 0.352, 0.29, 0.085),
       (-0.12, 0.352, 0.28, 0.09)]
mb.loft([((0, y, z), X, Z, a, b) for y, z, a, b in JAW], 14, "frog_green", "jaw")
mb.ellipsoid((0, -0.3, 0.305), (0.2, 0.17, 0.03), 12, 4, "frog_belly", "jaw")             # светлое подбородье
mb.ellipsoid((0, -0.33, 0.345), (0.22, 0.15, 0.018), 12, 4, "frog_tongue", "head")    # нёбо — видно, когда рот открыт
mb.ellipsoid((0, -0.31, 0.418), (0.2, 0.15, 0.012), 12, 4, "mouse_pink", "jaw")        # дно рта
mb.ellipsoid((0, -0.2, 0.29), (0.2, 0.13, 0.07), 12, 6, "frog_belly", "throat")       # горловой мешок, раздувается
# губа — тёмная линия от угла рта вокруг морды к другому углу
LIP = []
for s, side in SIDES:
    for y in ([-0.15, -0.2, -0.27, -0.34, -0.41, -0.47] if s < 0 else [-0.47, -0.41, -0.34, -0.27, -0.2, -0.15]):
        zc, a, b = body_at(y)
        drop = 0.03 if y > -0.18 else 0.0                                    # угол рта загнут вниз
        LIP.append(V((s * a * 0.99, y, zc - b * 0.45 - drop)))
    if s < 0:
        LIP.append(V((0, -0.522, 0.392)))
mb.tube(LIP, [0.009] * len(LIP), 4, "frog_dark", "head")

# язык: 8 колец на 8 костях подряд — кости расходятся, грани между кольцами тянутся (одна поверхность)
TONGUE_Y = [-0.17, -0.21, -0.25, -0.29, -0.33, -0.37, -0.41, -0.44]
TONGUE_R = [0.035, 0.042, 0.046, 0.048, 0.048, 0.046, 0.044, 0.04]
TONGUE = [V((0, y, 0.413 + 0.012 * i / 7)) for i, y in enumerate(TONGUE_Y)]
mb.loft([(p, X, Z, r, r * 0.45) for p, r in zip(TONGUE, TONGUE_R)], 8, "frog_tongue", "tongue_01",
        ring_weights=[{f"tongue_{i + 1:02d}": 1.0} for i in range(8)])
mb.ellipsoid(TONGUE[-1] + V((0, -0.035, 0.002)), (0.06, 0.05, 0.026), 10, 6, "frog_tongue", "tongue_08")  # липкая подушечка

# ---------------------------------------------------------------- глаза, веки, барабанные перепонки, ноздри
EYE_R = 0.085
EYES = {}
for s, side in SIDES:
    c = V((s * 0.165, -0.335, 0.515))
    EYES[side] = c
    mb.ellipsoid(c, (EYE_R, EYE_R, EYE_R), 12, 8, "brass", f"eye_{side}")                      # золотая радужка
    d = V((s * 0.84, -0.5, 0.2)).normalized()                                              # взгляд вбок-вперёд
    u = d.cross(Z).normalized()
    v = u.cross(d).normalized()
    mb.loft([(c + d * (EYE_R - 0.012), u, v, 0.036, 0.017), (c + d * (EYE_R + 0.002), u, v, 0.031, 0.014)],
            10, "eye_black", f"eye_{side}")                                                  # зрачок горизонтальный
    mb.ellipsoid(c + d * (EYE_R - 0.012) + v * 0.03 - u * s * 0.02, (0.009, 0.009, 0.009), 6, 4, "dew", f"eye_{side}")
    # Upper and lower rigid eyelid shells close over a fixed-radius eyeball.
    for lower in (False, True):
        lid_bone = f"lid_{'lower_' if lower else ''}{side}"
        open_axis = V((0, 0.8, -0.6 if lower else 0.6)).normalized()
        lu = open_axis.cross(X).normalized()
        lv = open_axis.cross(lu).normalized()
        cap = math.radians(92)
        radius = 0.092 if lower else 0.091
        rings = []
        for k in range(9):
            theta = 0.015 + (cap - 0.015) * k / 8
            rings.append((c + open_axis * (radius * math.cos(theta)), lu, lv,
                          radius * math.sin(theta), radius * math.sin(theta)))
        mb.loft(rings, 20, "frog_green", lid_bone, caps=(True, False))
        rim = []
        for k in range(21):
            phi = 2 * math.pi * k / 20
            rim.append(c + radius * (open_axis * math.cos(cap)
                       + (lu * math.cos(phi) + lv * math.sin(phi)) * math.sin(cap)))
        mb.tube(rim, [0.0018] * len(rim), 4, "frog_dark", lid_bone)
    # барабанная перепонка за глазом
    t0, tn = top(s * 0.27, -0.205)
    tu = tn.cross(Y).normalized()
    tv = tn.cross(tu).normalized()
    mb.loft([(t0 - tn * 0.014, tu, tv, 0.045, 0.042), (t0 - tn * 0.001, tu, tv, 0.041, 0.038)], 10, "mud", "head")
    p, _ = top(s * 0.04, -0.49, -0.004)
    mb.ellipsoid(p, (0.011, 0.008, 0.007), 6, 4, "eye_black", "head")                     # ноздря
# шрам через левое веко — у босса за спиной не одна драка
c = EYES["l"]
for k in range(3):
    a = c + V((-0.03 + 0.03 * k, 0.05 - 0.018 * k, 0.088 - 0.008 * k))
    mb.tube([a + V((-0.02, -0.03, 0.0)), a, a + V((0.025, 0.035, -0.004))], [0.0, 0.007, 0.0], 3, "frog_belly", "head")

# ---------------------------------------------------------------- спина: складки, пятна, бугорки
for s, side in SIDES:
    # складка лежит на груди и тазе: заднюю половину отдаём тазу, чтобы при прогибе не отрывалась
    for ys, rs, bone in (((-0.24, -0.14, -0.02, 0.1), (0.0, 0.018, 0.021, 0.021), "chest"),
                         ((0.1, 0.22, 0.32, 0.4), (0.021, 0.019, 0.014, 0.0), "pelvis")):
        pts = [top(s * body_at(y)[1] * 0.62, y, -0.004)[0] for y in ys]
        mb.tube(pts, list(rs), 4, "frog_lime", bone)
rnd = random.Random(5)
SPOTS = [(-0.05, 0.0, 0.07), (0.1, 0.1, 0.06), (-0.12, 0.22, 0.05), (0.13, -0.1, 0.05), (0.0, 0.33, 0.045),
         (-0.17, 0.05, 0.04), (0.19, 0.27, 0.035), (0.04, -0.17, 0.04), (-0.08, 0.38, 0.03)]
for x, y, r in SPOTS:
    zc, a, _ = body_at(y)
    p, n = top(x, y, -r * 0.16)
    mb.ellipsoid(p, (r * 1.15, r * 1.35, r * 0.2), 10, 3, "frog_dark", body_bone(y))
WARTS = 0
while WARTS < 34:
    y = rnd.uniform(-0.15, 0.44)
    zc, a, _ = body_at(y)
    x = rnd.uniform(-0.85, 0.85) * a
    r = rnd.uniform(0.011, 0.02)
    p, n = top(x, y, -r * 0.35)
    mb.ellipsoid(p, (r, r, r * 0.7), 6, 4, "frog_dark" if rnd.random() < 0.5 else "frog_lime", body_bone(y))
    WARTS += 1

# ---------------------------------------------------------------- лапы
def limb_tube(pts, radii, sw, bone, sides=8):
    mb.tube(pts, radii, sides, sw, bone)

def toe(base, d, length, r, pad, sw, bone, curl=0.0):
    tip = base + d * length + V((0, 0, curl))
    mid = base.lerp(tip, 0.55) + V((0, 0, 0.012))
    mb.tube([base, mid, tip], [r, r * 0.8, r * 0.55], 5, sw, bone)
    mb.ellipsoid(tip + d * pad * 0.4, (pad, pad, pad * 0.6), 6, 4, "frog_belly", bone)   # подушечка на пальце
    return tip

def fan(n, a0, a1):
    """n направлений в горизонтали от угла a0 до a1 (0 — вперёд, −Y; плюс — к +X)."""
    return [V((math.sin(math.radians(a)), -math.cos(math.radians(a)), 0)) for a in
            (a0 + (a1 - a0) * k / (n - 1) for k in range(n))]

LIMBS = {}
for s, side in SIDES:
    # передняя: плечо → локоть → запястье → кисть на земле, 4 пальца веером внутрь-вперёд
    sh, el, wr = V((s * 0.2, -0.1, 0.3)), V((s * 0.32, -0.12, 0.14)), V((s * 0.28, -0.27, 0.035))
    hand_tip = wr + V((-s * 0.03, -0.1, -0.02))
    limb_tube([sh, sh.lerp(el, 0.5), el], [0.06, 0.06, 0.048], "frog_green", f"arm_{side}_upper")
    mb.ellipsoid(el, (0.05, 0.05, 0.05), 8, 6, "frog_green", f"arm_{side}_lower")
    limb_tube([el, el.lerp(wr, 0.5) + V((s * 0.01, 0, 0)), wr], [0.048, 0.044, 0.032], "frog_green", f"arm_{side}_lower")
    for k in range(3):                                                    # полоски на предплечье
        p = el.lerp(wr, 0.25 + 0.25 * k)
        mb.tube([p + V((0, 0.01, 0.0)), p + V((0, -0.01, 0.0))], [0.05 - 0.006 * k, 0.05 - 0.006 * k], 8, "frog_dark",
                f"arm_{side}_lower")
    mb.ellipsoid(wr + V((-s * 0.01, -0.03, -0.012)), (0.04, 0.045, 0.018), 8, 4, "frog_belly", f"arm_{side}_hand")
    for d, L in zip(fan(4, s * 35, -s * 45), (0.07, 0.09, 0.095, 0.075)):
        toe(wr + V((-s * 0.01, -0.03, -0.015)) + d * 0.02, d, L, 0.014, 0.014, "frog_green", f"arm_{side}_hand",
            curl=-0.008)
    LIMBS[f"arm_{side}"] = (sh, el, wr, hand_tip)

    # задняя сложена «зигзагом»: бедро вперёд-наружу, голень назад, предплюсна вперёд по земле, стопа с перепонкой
    hip, kn, an = V((s * 0.17, 0.33, 0.21)), V((s * 0.42, 0.05, 0.17)), V((s * 0.34, 0.47, 0.075))
    ball = V((s * 0.45, 0.13, 0.035))
    ftip = ball + V((s * 0.06, -0.26, -0.015))
    limb_tube([hip, hip.lerp(kn, 0.45) + V((0, 0, 0.03)), kn], [0.105, 0.11, 0.075], "frog_green", f"leg_{side}_upper", 10)
    for k in range(3):                                                    # тёмные поперечные полосы на бедре
        p = hip.lerp(kn, 0.35 + 0.2 * k) + V((0, 0, 0.03 * (1 - abs(0.5 - (0.35 + 0.2 * k)) * 2)))
        dd = (kn - hip).normalized() * 0.018
        r = 0.112 - 0.012 * k
        mb.tube([p - dd, p + dd], [r, r], 10, "frog_dark", f"leg_{side}_upper")
    mb.ellipsoid(kn, (0.075, 0.075, 0.075), 8, 6, "frog_green", f"leg_{side}_lower")
    limb_tube([kn, kn.lerp(an, 0.4) + V((0, 0, 0.02)), an], [0.072, 0.07, 0.045], "frog_green", f"leg_{side}_lower")
    for k in range(2):
        p = kn.lerp(an, 0.35 + 0.25 * k) + V((0, 0, 0.014))
        dd = (an - kn).normalized() * 0.016
        r = 0.073 - 0.01 * k
        mb.tube([p - dd, p + dd], [r, r], 8, "frog_dark", f"leg_{side}_lower")
    mb.ellipsoid(an, (0.045, 0.045, 0.045), 8, 6, "frog_green", f"leg_{side}_tarsus")
    limb_tube([an, an.lerp(ball, 0.5), ball], [0.045, 0.04, 0.032], "frog_green", f"leg_{side}_tarsus")
    # стопа: перепонка — тонкий веер, 5 длинных пальцев
    fd = (ftip - ball).normalized()
    side_dir = fd.cross(Z).normalized()
    mb.ellipsoid(ball.lerp(ftip, 0.42) + V((0, 0, 0.004)), (0.1, 0.13, 0.008), 10, 4, "frog_dark", f"leg_{side}_foot",
                 lambda co, fd=fd: co if co.dot(fd) > -0.02 else co * 0.6)
    base_ang = math.degrees(math.atan2(fd.x, -fd.y))
    for k, (d, L) in enumerate(zip(fan(5, base_ang - 34, base_ang + 30), (0.13, 0.19, 0.26, 0.22, 0.15))):
        toe(ball + d * 0.02, d, L, 0.02 - 0.001 * k, 0.017, "frog_green", f"leg_{side}_foot", curl=-0.01)
    LIMBS[f"leg_{side}"] = (hip, kn, an, ball, ftip)

obj = mb.finish("SK_FrogBoss", [mat], scale=S)

# ---------------------------------------------------------------- скелет (в долях тела, build_armature умножает на S)
B = [("root", (0, 0, 0), (0, -0.05, 0), None, False),
     ("pelvis", (0, 0.3, 0.25), (0, 0.06, 0.34), "root", False),
     ("chest", (0, 0.06, 0.34), (0, -0.18, 0.43), "pelvis", True),
     ("head", (0, -0.18, 0.43), (0, -0.5, 0.44), "chest", True),
     ("jaw", (0, -0.15, 0.405), (0, -0.5, 0.375), "head", False),
     ("throat", (0, -0.2, 0.335), (0, -0.2, 0.22), "jaw", False)]
for i, p in enumerate(TONGUE):
    nxt = TONGUE[i + 1] if i + 1 < len(TONGUE) else p + V((0, -0.06, 0))
    B.append((f"tongue_{i + 1:02d}", tuple(p), tuple(nxt), "jaw" if i == 0 else f"tongue_{i:02d}", i > 0))
for s, side in SIDES:
    c = EYES[side]
    B.append((f"eye_{side}", tuple(c - V((0, 0, 0.05))), tuple(c + V((0, 0, 0.05))), "head", False))
    B.append((f"lid_{side}", tuple(c), tuple(c + V((0, 0, 0.06))), "head", False))
    B.append((f"lid_lower_{side}", tuple(c), tuple(c - V((0, 0, 0.06))), "head", False))
    sh, el, wr, ht = LIMBS[f"arm_{side}"]
    B += [(f"arm_{side}_upper", sh, el, "chest", False), (f"arm_{side}_lower", el, wr, f"arm_{side}_upper", True),
          (f"arm_{side}_hand", wr, ht, f"arm_{side}_lower", True)]
    hip, kn, an, ball, ftip = LIMBS[f"leg_{side}"]
    B += [(f"leg_{side}_upper", hip, kn, "pelvis", False), (f"leg_{side}_lower", kn, an, f"leg_{side}_upper", True),
          (f"leg_{side}_tarsus", an, ball, f"leg_{side}_lower", True), (f"leg_{side}_foot", ball, ftip, f"leg_{side}_tarsus", True)]
arm = lp.build_armature("SKEL_FrogBoss", B, roll_up_prefixes=("leg_", "arm_", "tongue_"), scale=S)
lp.bind_rigid(mb, arm)
if TOON:
    lp.toonify(obj)
    lp.add_outline(obj, 0.035)

lp.report(obj, arm)
suffix = "_Toon" if TOON else ""
lp.export_mesh(arm, obj, os.path.join(HERE, f"SK_FrogBoss{suffix}.fbx"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"FrogBoss{suffix}.blend"))
print("FROG: done")
