# Форма «Канавы» — общая для генератора (build_ditch.py) и проверки (check_ditch.py). Чистый Python, без bpy.
# Масштаб ×35: игрок 1.8 м = лягушка ~5 см. Метры, ось канавы — X (от safe zone к трубе), вверх +Z.
import math

X0, X1 = -78.0, 70.0          # торцы дна: у -X — банка (safe zone), у +X — дренажная труба
TOP_Z = 12.0                  # канава 35 см → 12 м
BANK_RUN = 7.0                # склон 12 м на 7 м (~60°, в UE не зайти: предел пола 44.76°)
WATER_Z = -0.3
STREAM_HW, STREAM_DEPTH = 2.6, 0.7

PIPE_X, PIPE_R_IN, PIPE_R_OUT = 62.0, 5.0, 5.6   # водопропуск Ø 30 см → 10.5 м, устье на x = 62
PIPE_GRATE = PIPE_X + 7.5     # решётка внутри трубы — дальше не пройти
BOSS_X, BOSS_R = 44.0, 15.0   # площадка босса-мыши перед устьем
START_X = -60.0
CAN_X0, CAN_X1, CAN_R, CAN_SINK = -74.5, -65.75, 3.5, 1.5   # банка Ø 20 см × 25 см на боку, открытым концом к +X

# бочаги: (x, смещение от оси, радиус, глубина) — по бокам ручья, проход мимо свободен
POOLS = [(-30.0, -4.5, 5.0, 1.8), (2.0, 7.0, 5.5, 2.0), (27.0, -5.5, 5.0, 1.8)]


def smooth(e0, e1, x):
    k = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return k * k * (3 - 2 * k)


def yc(x):
    """Ось канавы по Y — плавно петляет."""
    return 3.5 * math.sin(x * 0.05 + 0.6) + 1.5 * math.sin(x * 0.11)


def half_width(x):
    """Полуширина дна: 10.5–15.5 м, у площадки босса ≥ 17 м."""
    return 13.0 + 2.5 * math.sin(x * 0.08 + 1.3) + 5.0 * smooth(18, 36, x)


def stream_y(x):
    return yc(x) + 4.0 * math.sin(x * 0.09 + 0.4) * (1 - smooth(30, 40, x)) * smooth(-62, -50, x)


def pool_xy(p):
    x, d, _, _ = p
    return x, yc(x) + d


def outside(x, y):
    """Насколько точка за краем дна, м (< 0 — на дне)."""
    return max(abs(y - yc(x)) - half_width(x), X0 - x, x - X1)


def ground_z(x, y):
    e = outside(x, y)
    if e > 0:
        return TOP_Z * smooth(0, BANK_RUN, e)
    z = 0.18 * math.sin(x * 0.31 + y * 0.17) + 0.12 * math.sin(x * 0.13 - y * 0.41 + 1.7)
    z *= smooth(0, 3, -e)                                    # у склона ровно
    for px, py in ((START_X, yc(START_X)), (BOSS_X, yc(BOSS_X))):  # старт и площадка босса ровные
        z *= smooth(8, 14, math.hypot(x - px, y - py))
    z *= smooth(0, 3, x - CAN_X1 - 1) if x > CAN_X0 - 4 else 0.0   # под банкой и перед ней ровно
    # углубления не складываются, а берётся самое глубокое — уклон не круче, чем у каждого по отдельности
    ds = abs(y - stream_y(x))
    dig = 0.0
    if x < PIPE_X + 1:                                       # ручей уходит в трубу
        dig = STREAM_DEPTH * smooth(0, 1, (STREAM_HW + 1.8 - ds) / 1.8) * smooth(CAN_X1 + 2, CAN_X1 + 8, x)
        z *= 1 - 0.7 * smooth(0, 1, (STREAM_HW + 1.8 - ds) / 1.8)   # по руслу шум слабее — вода не мелеет
    for p in POOLS:
        px, py = pool_xy(p)
        r, depth = p[2], p[3]
        dig = max(dig, depth * smooth(0, 1, (r - math.hypot(x - px, y - py)) / r))
    return z - dig
