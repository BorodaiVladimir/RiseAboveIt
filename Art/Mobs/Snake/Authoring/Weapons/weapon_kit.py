# Детали оружия из мусора для Rise Above It! — поверх Shared/lowpoly.MeshBuilder.
# Масштаб ×257 (игрок 1.8 м = божья коровка 7 мм): всё оружие собрано из того, что в реальности
# меньше миллиметра — щепка от зубочистки, обломок лезвия бритвы, волос, шестерёнка часов,
# медная жилка из провода, стеклянная микробусина, SMD-конденсатор с платы.
import bmesh, math, random
from mathutils import Vector, Matrix

def basis(axis, up=(0, 0, 1)):
    """Ортонормированный базис (u, v, w) с w вдоль axis."""
    w = Vector(axis).normalized()
    up = Vector(up)
    if abs(w.dot(up.normalized())) > 0.95:
        up = Vector((1, 0, 0)) if abs(w.x) < 0.9 else Vector((0, 1, 0))
    u = up.cross(w).normalized()
    return u, w.cross(u).normalized(), w

def splinter(mb, pts, radii, sw, bone, flat=0.65, sides=7, jitter=0.18, seed=1, twist=25.0):
    """Щепка: сплюснутая неровная палка по ломаной pts, сечения с разбросом — волокнистая, не цилиндр."""
    rnd = random.Random(seed)
    pts = [Vector(p) for p in pts]
    rings = []
    for i, p in enumerate(pts):
        d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        u, v, _ = basis(d)
        a = math.radians(twist * i / max(len(pts) - 1, 1))
        u, v = u * math.cos(a) + v * math.sin(a), v * math.cos(a) - u * math.sin(a)
        r = radii[i]
        rings.append((p, u, v, r * (1 + rnd.uniform(-jitter, jitter)), r * flat * (1 + rnd.uniform(-jitter, jitter))))
    faces = mb.loft(rings, sides, sw, bone)
    verts = {v for f in faces for v in f.verts}
    for v in verts:                                  # продольные волокна: случайные бороздки
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * radii[0] * 0.06
    return faces

def spike(mb, base, tip, r, sw, bone, sides=5):
    return mb.tube([base, Vector(base).lerp(Vector(tip), 0.5), tip], [r, r * 0.6, 0.0], sides, sw, bone)

def plate(mb, outline, origin, u, v, half_thick, sw, bone, edge=None, edge_sw=None):
    """Плоская пластина по контуру (2D-точки в осях u, v) толщиной 2*half_thick.
    edge — индексы рёбер контура (i -> i+1), которые красятся edge_sw (заточенная кромка)."""
    bm = mb.bm
    o, u, v = Vector(origin), Vector(u).normalized(), Vector(v).normalized()
    n = u.cross(v).normalized()
    top = [bm.verts.new(o + u * x + v * y + n * half_thick) for x, y in outline]
    bot = [bm.verts.new(o + u * x + v * y - n * half_thick) for x, y in outline]
    k = len(outline)
    faces = [bm.faces.new(top), bm.faces.new(list(reversed(bot)))]
    sides = []
    for i in range(k):
        sides.append(bm.faces.new((bot[i], bot[(i + 1) % k], top[(i + 1) % k], top[i])))
    res = mb.register(top + bot, faces + sides, sw, bone)
    if edge:
        for i in edge:
            sides[i][mb.L_SW] = mb_sw(edge_sw)
    return res

def mb_sw(name):
    import lowpoly
    return lowpoly.SW[name]

def coil(mb, start, axis, ra, rb, length, turns, wire_r, sw, bone, up=(0, 0, 1), sides=4, steps_per_turn=10,
         phase=0.0, wobble=0.0, seed=3):
    """Обмотка (нитка, проволока, бинт) вокруг оси: эллипс ra×rb, шаг = length / turns."""
    rnd = random.Random(seed)
    u, v, w = basis(axis, up)
    s = Vector(start)
    n = max(2, int(turns * steps_per_turn))
    pts = []
    for i in range(n + 1):
        t = i / n
        a = phase + 2 * math.pi * turns * t
        k = 1 + rnd.uniform(-wobble, wobble)
        pts.append(s + w * (length * t) + u * (ra * k * math.cos(a)) + v * (rb * k * math.sin(a)))
    return mb.tube(pts, [wire_r] * len(pts), sides, sw, bone)

def ring(mb, center, axis, ra, rb, wire_r, sw, bone, up=(0, 0, 1), seg=12, sides=4):
    u, v, w = basis(axis, up)
    c = Vector(center)
    bm = mb.bm
    loops = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        p = c + u * (ra * math.cos(a)) + v * (rb * math.sin(a))
        radial = (u * (math.cos(a) / max(ra, 1e-6)) + v * (math.sin(a) / max(rb, 1e-6))).normalized()
        loops.append([bm.verts.new(p + radial * (wire_r * math.cos(b)) + w * (wire_r * math.sin(b)))
                      for b in (2 * math.pi * j / sides for j in range(sides))])
    faces = []
    for i in range(seg):
        A, B = loops[i], loops[(i + 1) % seg]
        faces += [bm.faces.new((A[j], A[(j + 1) % sides], B[(j + 1) % sides], B[j])) for j in range(sides)]
    return mb.register([v for L in loops for v in L], faces, sw, bone)

def gear(mb, center, axis, r_out, teeth, half_thick, sw, bone, up=(0, 0, 1), rim=0.22, hub=0.18, spokes=4,
         tooth_depth=0.12, hole=0.05):
    """Колесо часов: зубчатый обод, спицы, ступица с отверстием под ось. Размеры — доли r_out."""
    bm = mb.bm
    u, v, w = basis(axis, up)
    c = Vector(center)
    def P(r, a, h):
        return c + u * (r * math.cos(a)) + v * (r * math.sin(a)) + w * h
    r_root = r_out * (1 - tooth_depth)
    r_in = r_out * (1 - tooth_depth - rim)
    outline = []                                     # зубья: 4 точки на зуб (впадина, подъём, вершина, спуск)
    for i in range(teeth):
        a0 = 2 * math.pi * i / teeth
        da = 2 * math.pi / teeth
        outline += [(r_root, a0), (r_out, a0 + da * 0.3), (r_out, a0 + da * 0.55), (r_root, a0 + da * 0.85)]
    m = len(outline)
    inner = [(r_in, 2 * math.pi * i / m) for i in range(m)]
    T = [bm.verts.new(P(r, a, half_thick)) for r, a in outline]
    B = [bm.verts.new(P(r, a, -half_thick)) for r, a in outline]
    Ti = [bm.verts.new(P(r, a, half_thick)) for r, a in inner]
    Bi = [bm.verts.new(P(r, a, -half_thick)) for r, a in inner]
    faces = []
    for i in range(m):
        j = (i + 1) % m
        faces.append(bm.faces.new((T[i], T[j], Ti[j], Ti[i])))
        faces.append(bm.faces.new((B[j], B[i], Bi[i], Bi[j])))
        faces.append(bm.faces.new((B[i], B[j], T[j], T[i])))
        faces.append(bm.faces.new((Ti[i], Ti[j], Bi[j], Bi[i])))
    mb.register(T + B + Ti + Bi, faces, sw, bone)
    # ступица — шестигранная втулка с отверстием (кольцо)
    hr, hh = r_out * hub, r_out * hole
    k = 8
    o = [bm.verts.new(P(hr, 2 * math.pi * i / k, half_thick * 1.6)) for i in range(k)]
    ob = [bm.verts.new(P(hr, 2 * math.pi * i / k, -half_thick * 1.6)) for i in range(k)]
    ii = [bm.verts.new(P(hh, 2 * math.pi * i / k, half_thick * 1.6)) for i in range(k)]
    ib = [bm.verts.new(P(hh, 2 * math.pi * i / k, -half_thick * 1.6)) for i in range(k)]
    hf = []
    for i in range(k):
        j = (i + 1) % k
        hf += [bm.faces.new((o[i], o[j], ii[j], ii[i])), bm.faces.new((ob[j], ob[i], ib[i], ib[j])),
               bm.faces.new((ob[i], ob[j], o[j], o[i])), bm.faces.new((ii[i], ii[j], ib[j], ib[i]))]
    mb.register(o + ob + ii + ib, hf, sw, bone)
    # спицы — чуть изогнутые, как у колёс часового механизма
    for s in range(spokes):
        a = 2 * math.pi * (s + 0.5) / spokes
        p0, p1 = P(hr * 0.9, a, 0), P(r_in * 1.02, a + 0.25, 0)
        mid = P((hr + r_in) / 2, a + 0.16, 0)
        mb.tube([p0, mid, p1], [r_out * 0.05] * 3, 4, sw, bone)

def shell(mb, y_back, y_front, radius, half_arc, thick, sw, bone, z=0.0, seg_y=6, seg_a=8, jag=0.04, seed=5,
          inner_sw=None):
    """Осколок стенки трубки (корпус ручки/карандаша) вдоль −Y: дуга желобом вверх, рваные концы.
    half_arc — половина угла дуги (рад) от низа; внутренняя сторона красится inner_sw."""
    rnd = random.Random(seed)
    bm = mb.bm
    ends = [(y_back + rnd.uniform(-jag, jag), y_front + rnd.uniform(-jag, jag)) for _ in range(seg_a + 1)]
    grid_o, grid_i = [], []
    for i in range(seg_y + 1):
        ro, ri = [], []
        for j in range(seg_a + 1):
            a = -half_arc + 2 * half_arc * j / seg_a            # 0 — низ дуги
            yb, yf = ends[j]
            y = yb + (yf - yb) * i / seg_y
            d = Vector((math.sin(a), 0, -math.cos(a)))
            c = Vector((0, y, z + radius))
            ro.append(bm.verts.new(c + d * radius))
            ri.append(bm.verts.new(c + d * (radius - thick)))
        grid_o.append(ro)
        grid_i.append(ri)
    faces, inner = [], []
    for i in range(seg_y):
        for j in range(seg_a):
            faces.append(bm.faces.new((grid_o[i][j], grid_o[i][j + 1], grid_o[i + 1][j + 1], grid_o[i + 1][j])))
            inner.append(bm.faces.new((grid_i[i][j + 1], grid_i[i][j], grid_i[i + 1][j], grid_i[i + 1][j + 1])))
        for j in (0, seg_a):                                   # кромки дуги
            faces.append(bm.faces.new((grid_o[i][j], grid_o[i + 1][j], grid_i[i + 1][j], grid_i[i][j])))
    for i in (0, seg_y):                                       # рваные торцы
        for j in range(seg_a):
            faces.append(bm.faces.new((grid_o[i][j], grid_i[i][j], grid_i[i][j + 1], grid_o[i][j + 1])))
    verts = [v for g in (grid_o, grid_i) for r in g for v in r]
    mb.register(verts, faces + inner, sw, bone)
    if inner_sw:
        for f in inner:
            f[mb.L_SW] = mb_sw(inner_sw)
    return faces + inner

def bead(mb, center, r, sw, bone):
    """Стеклянная микробусина — гранёный шарик (икосфера) с отверстием-втулкой."""
    return mb.ellipsoid(center, (r, r, r), 10, 7, sw, bone)
