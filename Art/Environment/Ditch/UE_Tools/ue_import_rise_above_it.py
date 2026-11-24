# Импорт ассетов Rise Above It! в UE 5 одним запуском (Output Log → Python, или File → Execute Python Script).
# Лежит в корне папки UE_Import и берёт файлы рядом с собой:
#   1) импортирует палитру в /Game/RiseAboveIt/Textures и создаёт общие материалы в /Game/RiseAboveIt/Materials;
#   2) импортирует FBX в /Game/RiseAboveIt/... (скелетные меши + их анимации, статичные меши с UCX-коллизией)
#      без материалов из FBX — слоты материалов назначаются по имени слота (SLOT_MATERIALS);
#   3) ставит коллизию земли и расставляет арену в ОТКРЫТОМ уровне по её CSV (папка арены в Outliner):
#      по умолчанию «Земля» (Arena_Earth/ArenaEarth_Layout.csv); «Канава» — ARENA = "Ditch"
#      или скрипт ue_place_ditch.py (ставит Канаву без переимпорта).
# Повторный запуск переимпортирует ассеты; расстановку можно отключить флагом PLACE_ARENA.
# Переменные окружения (для сборки карт): RAI_ARENA=Earth|Ditch, RAI_SKIP_IMPORT=1 — только расстановка.
# Проверен 12.10.2026 (оружие 20.10.2026, общий скелет игрока 25.10.2026) на UE 5.7.4 в пустом проекте. Если какой-то шаг упадёт, он пишет ошибку в лог и идёт дальше.
import os, csv
import unreal

ROOT = os.path.dirname(os.path.abspath(__file__))
DEST = "/Game/RiseAboveIt"
MAT_DIR = f"{DEST}/Materials"
PLACE_ARENA = True
PLACE_LIGHTING = True          # свет и туман арены (папка <арена>/Lighting) — выключить, если у уровня свой свет
ARENA = os.environ.get("RAI_ARENA", "Earth")         # какую арену ставить в открытый уровень: "Earth" или "Ditch"
SKIP_IMPORT = os.environ.get("RAI_SKIP_IMPORT") == "1"
ARENAS = {   # папка в UE_Import и в /Game/RiseAboveIt, CSV расстановки, земля (complex as simple), свет
    "Earth": dict(folder="Arena_Earth", csv="ArenaEarth_Layout.csv", ground="SM_Earth_Ground", light="morning"),
    "Ditch": dict(folder="Arena_Ditch", csv="ArenaDitch_Layout.csv", ground="SM_Ditch_Ground", light="overcast"),
}

# Игрок и оружие — на ОДНОМ скелете SK_FP_Arms_Skeleton: кости оружия висят под костью weapon рук
# (root → weapon → sp_* у копья, xb_* у арбалета), при импорте меша оружия UE добавляет их в скелет рук.
# Порядок важен: сначала руки (создают скелет), потом оружие на него.
PLAYER_SKELETON = "Player/FP_Arms/SK_FP_Arms"
SKELETAL = [  # (папка в UE_Import, меш, префикс анимаций, чей скелет: None — свой)
    ("Mobs/Tick", "SK_Tick", "A_Tick_", None),
    ("Mobs/Mosquito", "SK_Mosquito", "A_Mosquito_", None),
    ("Mobs/FrogBoss", "SK_FrogBoss", "A_FrogBoss_", None),
    ("Player/FP_Arms", "SK_FP_Arms", "A_FP_", None),
    ("Arena_Earth/JumpLeaf", "SK_JumpLeaf", "A_JumpLeaf_", None),
    ("Weapons/Spear", "SK_Spear", "A_Spear_", PLAYER_SKELETON),
    ("Weapons/Crossbow", "SK_Crossbow", "A_Crossbow_", PLAYER_SKELETON),
    ("NPC/RoachCrafter", "SK_RoachCrafter", "A_RoachCrafter_", None),   # SK_RoachCrafter_Toon встаёт на тот же скелет
]
STATIC_DIRS = ["Arena_Earth", "Arena_Earth/Kit", "Arena_Ditch", "Loot", "Weapons/Projectiles"]

# имя слота материала в FBX → материал проекта (все на одной палитре, кроме воды и росы)
SLOT_MATERIALS = {
    "M_FrogBoss": "M_Palette",
    "M_Tick": "M_Palette", "M_Mosquito": "M_Palette", "M_FP_Arms": "M_Palette", "M_JumpLeaf": "M_Palette",
    "M_Palette": "M_Palette", "M_Palette_TwoSided": "M_Palette_TwoSided",
    "M_MosquitoWing": "M_Palette_Wing", "M_Water": "M_Water", "M_Dew": "M_Dew",
    "M_Palette_Toon": "M_Palette_Toon", "M_Outline": "M_Outline",   # оружие, лут, снаряды: тун-палитра + контур
    "M_Glow": "M_Glow",                                              # светодиод в safe zone
    "M_RoachCrafter": "M_Palette",                                   # таракан-крафтер, вариант как у мобов
}

log = unreal.log
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary

def step(name, fn, *a):
    try:
        return fn(*a)
    except Exception as e:                       # noqa: BLE001 — один упавший шаг не должен останавливать остальные
        unreal.log_error(f"[RiseAboveIt] {name}: {e}")

def legacy_fbx(enable):
    """С 5.5 FBX по умолчанию идёт через Interchange и игнорирует FbxImportUI — на время импорта включаем старый импортёр."""
    unreal.SystemLibrary.execute_console_command(None, f"Interchange.FeatureFlags.Import.FBX {'False' if enable else 'True'}")

def task(path, dest, options=None):
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", path)
    t.set_editor_property("destination_path", dest)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    if options:
        t.set_editor_property("options", options)
    asset_tools.import_asset_tasks([t])
    return t.get_editor_property("imported_object_paths")

# ---------- палитра и материалы ----------

def import_palette(name="T_Palette"):
    task(os.path.join(ROOT, "Textures", name + ".png"), f"{DEST}/Textures")
    tex = eal.load_asset(f"{DEST}/Textures/{name}")
    tex.set_editor_property("filter", unreal.TextureFilter.TF_NEAREST)          # иначе соседние клетки смешиваются
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    eal.save_loaded_asset(tex)
    return tex

def new_material(name):
    path = f"{MAT_DIR}/{name}"
    if eal.does_asset_exist(path):
        mat = eal.load_asset(path)
        mel.delete_all_material_expressions(mat)
        return mat
    return asset_tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())

def const(mat, value, prop, y):
    c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, y)
    c.set_editor_property("r", value)
    mel.connect_material_property(c, "", prop)

def color(mat, rgb, prop, y):
    c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, y)
    c.set_editor_property("constant", unreal.LinearColor(*rgb, 1.0))
    mel.connect_material_property(c, "", prop)

def palette_material(name, tex, two_sided=False, opacity=None):
    mat = new_material(name)
    s = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, 0)
    s.set_editor_property("texture", tex)
    mel.connect_material_property(s, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    const(mat, 0.8, unreal.MaterialProperty.MP_ROUGHNESS, 250)               # матовый low poly
    mat.set_editor_property("two_sided", two_sided)
    if opacity is not None:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        const(mat, opacity, unreal.MaterialProperty.MP_OPACITY, 350)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)

def expr(mat, cls, x, y, **props):
    e = mel.create_material_expression(mat, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e

def water_material():
    """Лужа: тёмная мутная вода, отражает как настоящая (сверху ~2%, у горизонта — почти зеркало),
    по поверхности бежит мелкая рябь (нормаль из синусов по мировым координатам).
    Specular 1.0 давал 8% отражения даже сверху — лужи выглядели хромированными пластинами."""
    mat = new_material("M_Water")
    P = unreal.MaterialProperty
    color(mat, (0.03, 0.028, 0.018), P.MP_BASE_COLOR, -200)
    const(mat, 0.25, P.MP_SPECULAR, -100)                 # F0 = 0.08 × 0.25 = 0.02 — вода
    const(mat, 0.08, P.MP_ROUGHNESS, 0)
    wp = expr(mat, unreal.MaterialExpressionWorldPosition, -1400, 200)
    t = expr(mat, unreal.MaterialExpressionTime, -1400, 350)
    def wave(mask, freq, speed, y):                       # sin(координата * частота + время * скорость)
        m = expr(mat, unreal.MaterialExpressionComponentMask, -1200, y, r=mask == "r", g=mask == "g", b=False, a=False)
        mel.connect_material_expressions(wp, "", m, "")
        k = expr(mat, unreal.MaterialExpressionMultiply, -1050, y, const_b=freq)
        mel.connect_material_expressions(m, "", k, "A")
        ts = expr(mat, unreal.MaterialExpressionMultiply, -1050, y + 60, const_b=speed)
        mel.connect_material_expressions(t, "", ts, "A")
        a = expr(mat, unreal.MaterialExpressionAdd, -900, y)
        mel.connect_material_expressions(k, "", a, "A")
        mel.connect_material_expressions(ts, "", a, "B")
        sn = expr(mat, unreal.MaterialExpressionSine, -760, y, period=6.283)
        mel.connect_material_expressions(a, "", sn, "")
        amp = expr(mat, unreal.MaterialExpressionMultiply, -620, y, const_b=0.06)
        mel.connect_material_expressions(sn, "", amp, "A")
        return amp
    nx, ny = wave("r", 0.021, 1.3, 200), wave("g", 0.017, -1.1, 380)
    n = expr(mat, unreal.MaterialExpressionAppendVector, -450, 280)
    mel.connect_material_expressions(nx, "", n, "A")
    mel.connect_material_expressions(ny, "", n, "B")
    n3 = expr(mat, unreal.MaterialExpressionAppendVector, -300, 280)
    mel.connect_material_expressions(n, "", n3, "A")
    one = expr(mat, unreal.MaterialExpressionConstant, -450, 420, r=1.0)
    mel.connect_material_expressions(one, "", n3, "B")
    mel.connect_material_property(n3, "", P.MP_NORMAL)
    mel.recompile_material(mat); eal.save_loaded_asset(mat)

def dew_material():
    """Роса: прозрачная вода с преломлением (IOR 1.33), края капли плотнее (Френель)."""
    mat = new_material("M_Dew")
    P = unreal.MaterialProperty
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE)
    color(mat, (0.75, 0.85, 0.85), P.MP_BASE_COLOR, -200)
    const(mat, 1.0, P.MP_SPECULAR, -100)
    const(mat, 0.0, P.MP_ROUGHNESS, 0)
    fr = expr(mat, unreal.MaterialExpressionFresnel, -600, 200, exponent=3.0, base_reflect_fraction=0.05)
    op = expr(mat, unreal.MaterialExpressionLinearInterpolate, -350, 200, const_a=0.12, const_b=0.85)
    mel.connect_material_expressions(fr, "", op, "Alpha")
    mel.connect_material_property(op, "", P.MP_OPACITY)
    ior = expr(mat, unreal.MaterialExpressionConstant, -350, 350, r=1.33)
    mel.connect_material_property(ior, "", P.MP_REFRACTION)
    mel.recompile_material(mat); eal.save_loaded_asset(mat)

def fx_material(name, tex_name, additive=False):
    """Материал частицы: кадр из флипбука 4×4 (Sub UV в Niagara) × цвет частицы, без освещения."""
    if not os.path.isfile(os.path.join(ROOT, "Textures", "FX", tex_name + ".png")):
        return                                   # неполный архив (например, только NPC) — эффектов нет
    task(os.path.join(ROOT, "Textures", "FX", tex_name + ".png"), f"{DEST}/Textures/FX")
    tex = eal.load_asset(f"{DEST}/Textures/FX/{tex_name}")
    mat = new_material(name)
    P = unreal.MaterialProperty
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE if additive else unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("used_with_niagara_sprites", True)
    sub = expr(mat, unreal.MaterialExpressionParticleSubUV, -700, 0, texture=tex)
    pc = expr(mat, unreal.MaterialExpressionParticleColor, -700, 300)
    rgb = expr(mat, unreal.MaterialExpressionMultiply, -400, 0)
    mel.connect_material_expressions(sub, "RGB", rgb, "A")
    mel.connect_material_expressions(pc, "RGB", rgb, "B")
    mel.connect_material_property(rgb, "", P.MP_EMISSIVE_COLOR)
    al = expr(mat, unreal.MaterialExpressionMultiply, -400, 250)
    mel.connect_material_expressions(sub, "A", al, "A")
    mel.connect_material_expressions(pc, "A", al, "B")
    mel.connect_material_property(al, "", P.MP_OPACITY)
    mel.recompile_material(mat); eal.save_loaded_asset(mat)

def make_materials():
    tex = import_palette()
    palette_material("M_Palette", tex)
    palette_material("M_Palette_TwoSided", tex, two_sided=True)             # трава
    palette_material("M_Palette_Wing", tex, two_sided=True, opacity=0.45)   # крылья комара
    water_material()
    dew_material()
    fx_material("M_FX_Dust", "T_FX_Dust")                    # пыль: срыв сборки, приземление, смерть
    fx_material("M_FX_Spark", "T_FX_Spark", additive=True)   # искры: электрокастет, удар по хитину
    fx_material("M_FX_Ripple", "T_FX_Ripple")                # рябь: лист-батут, лужи
    # тун: свет уже запечён в полосы T_Palette_Toon, поэтому Unlit — как в превью Blender
    toon = new_material("M_Palette_Toon")
    toon.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    s = mel.create_material_expression(toon, unreal.MaterialExpressionTextureSample, -400, 0)
    s.set_editor_property("texture", import_palette("T_Palette_Toon"))
    mel.connect_material_property(s, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(toon); eal.save_loaded_asset(toon)
    # контур — вывернутая оболочка с перевёрнутыми нормалями: материал обязательно ОДНОСТОРОННИЙ
    outline = new_material("M_Outline")
    outline.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    color(outline, (0.0, 0.0, 0.0), unreal.MaterialProperty.MP_EMISSIVE_COLOR, 0)
    mel.recompile_material(outline); eal.save_loaded_asset(outline)
    glow = new_material("M_Glow")                                     # светится цветом палитры
    glow.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    s = mel.create_material_expression(glow, unreal.MaterialExpressionTextureSample, -500, 0)
    s.set_editor_property("texture", tex)
    k = mel.create_material_expression(glow, unreal.MaterialExpressionMultiply, -250, 0)
    k.set_editor_property("const_b", 6.0)
    mel.connect_material_expressions(s, "RGB", k, "A")
    mel.connect_material_property(k, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(glow); eal.save_loaded_asset(glow)
    log("[RiseAboveIt] palette + materials: ok")

def assign_materials(asset):
    """Ставит материалы проекта в слоты по имени слота из FBX."""
    is_static = isinstance(asset, unreal.StaticMesh)
    slots = list(asset.get_editor_property("static_materials" if is_static else "materials"))
    for s in slots:
        target = SLOT_MATERIALS.get(str(s.get_editor_property("material_slot_name")))
        if target:
            s.set_editor_property("material_interface", eal.load_asset(f"{MAT_DIR}/{target}"))
        else:
            unreal.log_warning(f"[RiseAboveIt] {asset.get_name()}: слот {s.get_editor_property('material_slot_name')} без материала")
    asset.set_editor_property("static_materials" if is_static else "materials", slots)
    eal.save_loaded_asset(asset)

# ---------- FBX ----------

def base_ui(mesh_type):
    ui = unreal.FbxImportUI()
    ui.set_editor_property("automated_import_should_detect_type", False)  # иначе тип берётся из файла, и анимация (в FBX есть меш) становится мешем
    ui.set_editor_property("mesh_type_to_import", mesh_type)
    ui.set_editor_property("original_import_type", mesh_type)
    ui.set_editor_property("import_materials", False)                     # материалы — свои, см. make_materials
    ui.set_editor_property("import_textures", False)
    # FBX из Blender в метрах (UnitScaleFactor 100), старый импортёр читает числа как сантиметры — всё в 100 раз меньше.
    # Convert Scene Unit не годится: у меша ×100 уходит в масштаб кости root, а треки анимаций остаются в метрах,
    # и анимированный меш схлопывается. Поэтому одинаковый Import Uniform Scale 100 для меша, анимаций и статики.
    for data in ("static_mesh_import_data", "skeletal_mesh_import_data", "anim_sequence_import_data"):
        d = ui.get_editor_property(data)
        d.set_editor_property("convert_scene", True)
        d.set_editor_property("convert_scene_unit", False)
        d.set_editor_property("import_uniform_scale", 100.0)
    return ui

def import_skeletal(folder, mesh, prefix, owner=None):
    src = os.path.join(ROOT, folder)
    dest = f"{DEST}/{folder}"
    ui = base_ui(unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", True)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("create_physics_asset", True)
    if owner:                                    # на чужой скелет: недостающие кости UE добавит в него сам
        ui.set_editor_property("skeleton", eal.load_asset(f"{DEST}/{owner}").get_editor_property("skeleton"))
    task(os.path.join(src, mesh + ".fbx"), dest, ui)
    sk = eal.load_asset(f"{dest}/{mesh}")
    assign_materials(sk)
    skeleton = sk.get_editor_property("skeleton")
    extra = []                                   # меши на том же скелете (улучшения кулаков) — SK_* кроме основного
    for f in sorted(os.listdir(src)):
        if f.startswith("SK_") and f.endswith(".fbx") and f != mesh + ".fbx":
            ui = base_ui(unreal.FBXImportType.FBXIT_SKELETAL_MESH)
            ui.set_editor_property("import_mesh", True)
            ui.set_editor_property("import_as_skeletal", True)
            ui.set_editor_property("import_animations", False)
            ui.set_editor_property("create_physics_asset", False)
            ui.set_editor_property("skeleton", skeleton)
            task(os.path.join(src, f), dest, ui)
            assign_materials(eal.load_asset(f"{dest}/{f[:-4]}"))
            extra.append(f[:-4])
    anims = []
    for f in sorted(os.listdir(src)):
        if f.startswith(prefix) and f.endswith(".fbx"):
            ui = base_ui(unreal.FBXImportType.FBXIT_ANIMATION)
            ui.set_editor_property("import_mesh", False)
            ui.set_editor_property("import_as_skeletal", True)
            ui.set_editor_property("import_animations", True)
            ui.set_editor_property("skeleton", skeleton)
            anims += task(os.path.join(src, f), dest, ui)
    log(f"[RiseAboveIt] {mesh}: ok, скелет {skeleton.get_path_name()}, анимаций {len(anims)}"
        + (f", меши на том же скелете: {', '.join(extra)}" if extra else ""))

def import_static(folder):
    src = os.path.join(ROOT, folder)
    dest = f"{DEST}/{folder}"
    n = 0
    for f in sorted(os.listdir(src)):
        if not (f.startswith("SM_") and f.endswith(".fbx")):
            continue
        ui = base_ui(unreal.FBXImportType.FBXIT_STATIC_MESH)
        ui.set_editor_property("import_mesh", True)
        ui.set_editor_property("import_as_skeletal", False)
        ui.set_editor_property("import_animations", False)
        smd = ui.get_editor_property("static_mesh_import_data")
        smd.set_editor_property("combine_meshes", True)
        smd.set_editor_property("auto_generate_collision", False)       # коллизия — UCX из FBX
        task(os.path.join(src, f), dest, ui)
        assign_materials(eal.load_asset(f"{dest}/{f[:-4]}"))
        n += 1
    log(f"[RiseAboveIt] {folder}: static ok, мешей {n}")

def setup_ground_collision(folder, ground):
    sm = eal.load_asset(f"{DEST}/{folder}/{ground}")
    bs = sm.get_editor_property("body_setup")
    bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    eal.save_loaded_asset(sm)

# ---------- расстановка ----------

def static_asset(folder, name):
    """Меш из папки арены; общие (верстак SM_Safe_Workbench) — из Arena_Earth."""
    for f in (folder, "Arena_Earth"):
        if eal.does_asset_exist(f"{DEST}/{f}/{name}"):
            return eal.load_asset(f"{DEST}/{f}/{name}")
    raise RuntimeError(f"нет меша {name}")

def place_row(actors, r, leaf_idle, folder="Arena_Earth"):
    loc = unreal.Vector(float(r["X"]), float(r["Y"]), float(r["Z"]))
    rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=float(r["Yaw"]))
    kind = r["Kind"]
    if kind == "StaticMesh":
        actor = actors.spawn_actor_from_object(static_asset(folder, r["Asset"]), loc, rot)
        if r["Asset"].endswith("_Boundary"):
            actor.set_actor_hidden_in_game(True)
    elif kind == "SkeletalMesh":
        actor = actors.spawn_actor_from_object(eal.load_asset(f"{DEST}/Arena_Earth/JumpLeaf/{r['Asset']}"), loc, rot)
        if leaf_idle:
            actor.get_editor_property("skeletal_mesh_component").override_animation_data(leaf_idle, True, True, 0.0, 1.0)
    elif kind == "PlayerStart":
        actor = actors.spawn_actor_from_class(unreal.PlayerStart, loc, rot)
    elif kind == "PointLight":
        actor = actors.spawn_actor_from_class(unreal.PointLight, loc, rot)
        lc = actor.point_light_component
        lc.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
        lc.set_editor_property("intensity", 40.0)                     # одна лампочка в коробке
        lc.set_editor_property("light_color", unreal.Color(r=255, g=196, b=120, a=255))
        lc.set_editor_property("attenuation_radius", 1200.0)
    elif kind == "TriggerBox":
        actor = actors.spawn_actor_from_class(unreal.TriggerBox, loc, rot)
        size = [float(v) for v in r["Note"].split(": ")[1].split(" ")[0].split("x")]
        actor.collision_component.set_editor_property("box_extent", unreal.Vector(size[0] / 2, size[1] / 2, size[2] / 2))
    else:
        actor = actors.spawn_actor_from_class(unreal.TargetPoint, loc, rot)
    actor.set_actor_label(r["Label"])
    actor.set_folder_path(folder)
    return True

def place_lighting(actors, folder="Arena_Earth", preset="morning"):
    """morning («Земля»): утро в тумане — низкое тёплое солнце из-за дерева, плотный светлый туман, холодный небосвод.
    overcast («Канава»): пасмурно — солнце высоко и слабое; густой серо-зелёный болотный туман по дну."""
    def put(cls, label, loc=(0, 0, 0), rot=(0, 0, 0)):
        a = actors.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
        a.set_actor_label(label)
        a.set_folder_path(f"{folder}/Lighting")
        return a
    if preset == "overcast":
        sun = put(unreal.DirectionalLight, "Sun", (0, 0, 1000), (0, -55, 60))
        sc = sun.light_component
        sc.set_editor_property("intensity", 3.0)
        sc.set_editor_property("light_color", unreal.Color(r=215, g=225, b=210, a=255))
        sc.set_editor_property("atmosphere_sun_light", True)
        put(unreal.SkyAtmosphere, "SkyAtmosphere")
        sky = put(unreal.SkyLight, "SkyLight", (0, 0, 500))
        kc = sky.light_component
        kc.set_editor_property("real_time_capture", True)
        kc.set_editor_property("intensity", 1.0)
        kc.set_editor_property("light_color", unreal.Color(r=200, g=215, b=195, a=255))
        fog = put(unreal.ExponentialHeightFog, "Fog")
        fc = fog.component
        fc.set_editor_property("fog_density", 0.05)
        fc.set_editor_property("fog_height_falloff", 0.2)          # туман стелется по дну канавы
        fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.42, 0.52, 0.34, 1))
        fc.set_editor_property("enable_volumetric_fog", True)
        fc.set_editor_property("volumetric_fog_extinction_scale", 2.0)
        return
    sun = put(unreal.DirectionalLight, "Sun", (0, 0, 1000), (0, -15, 30))
    sc = sun.light_component
    sc.set_editor_property("intensity", 8.0)
    sc.set_editor_property("light_color", unreal.Color(r=255, g=225, b=185, a=255))
    sc.set_editor_property("atmosphere_sun_light", True)
    put(unreal.SkyAtmosphere, "SkyAtmosphere")
    sky = put(unreal.SkyLight, "SkyLight", (0, 0, 500))
    kc = sky.light_component
    kc.set_editor_property("real_time_capture", True)
    kc.set_editor_property("intensity", 0.6)
    kc.set_editor_property("light_color", unreal.Color(r=205, g=220, b=255, a=255))
    fog = put(unreal.ExponentialHeightFog, "Fog")
    fc = fog.component
    fc.set_editor_property("fog_density", 0.02)
    fc.set_editor_property("fog_height_falloff", 0.05)
    fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.9, 0.8, 0.65, 1))
    fc.set_editor_property("enable_volumetric_fog", True)
    fc.set_editor_property("volumetric_fog_scattering_distribution", 0.6)   # свет вперёд — лучи из-за травы
    fc.set_editor_property("volumetric_fog_extinction_scale", 1.5)

def place_arena(name="Earth"):
    cfg = ARENAS[name]
    folder = cfg["folder"]
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level = actors.get_all_level_actors()
    in_folder = lambda a, f: str(a.get_folder_path()) == f or str(a.get_folder_path()).startswith(f + "/")
    other = [c["folder"] for n, c in ARENAS.items() if n != name and any(in_folder(a, c["folder"]) for a in level)]
    if other:   # в уровне стоит другая арена — не трогаем её (иначе перезапуск импорта на карте Канавы стёр бы Канаву)
        unreal.log_warning(f"[RiseAboveIt] в уровне уже стоит {', '.join(other)} — арену {name} не ставлю. "
                           f"Открой пустой уровень или уровень этой арены и запусти снова")
        return
    for a in level:                           # повторный запуск — свою арену расставляем заново
        if in_folder(a, folder):
            actors.destroy_actor(a)
    if PLACE_LIGHTING:
        step("lighting", place_lighting, actors, folder, cfg["light"])
    with open(os.path.join(ROOT, folder, cfg["csv"]), encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    leaf_idle = None
    if any(r["Kind"] == "SkeletalMesh" for r in rows):
        leaf_idle = eal.load_asset(f"{DEST}/Arena_Earth/JumpLeaf/A_JumpLeaf_Idle")
        if not isinstance(leaf_idle, unreal.AnimSequence):
            unreal.log_warning(f"[RiseAboveIt] A_JumpLeaf_Idle не анимация ({leaf_idle}) — листья без Idle")
            leaf_idle = None
    placed = sum(1 for r in rows if step(f"place {r['Label']}", place_row, actors, r, leaf_idle, folder))
    log(f"[RiseAboveIt] arena {name} placed: {placed}/{len(rows)}")

# архив может быть неполным (например, только таракан-крафтер) — чего нет рядом со скриптом, то пропускаем
has = lambda *p: os.path.exists(os.path.join(ROOT, *p))
if not SKIP_IMPORT:
    step("materials", make_materials)
    legacy_fbx(True)
    try:
        for folder, mesh, prefix, owner in SKELETAL:
            if has(folder, mesh + ".fbx"):
                step(f"import {mesh}", import_skeletal, folder, mesh, prefix, owner)
        for folder in STATIC_DIRS:
            if has(folder):
                step(f"import {folder}", import_static, folder)
    finally:
        legacy_fbx(False)
    for _cfg in ARENAS.values():
        if has(_cfg["folder"], _cfg["ground"] + ".fbx"):
            step(f"ground collision {_cfg['ground']}", setup_ground_collision, _cfg["folder"], _cfg["ground"])
_cfg = ARENAS.get(ARENA)
if _cfg is None:
    unreal.log_error(f"[RiseAboveIt] ARENA = {ARENA!r}: нет такой арены, есть {', '.join(ARENAS)}")
elif PLACE_ARENA and has(_cfg["folder"], _cfg["csv"]):
    step("place arena", place_arena, ARENA)
elif PLACE_ARENA and (ARENA != "Earth" or SKIP_IMPORT):     # арену просили явно, а файлов нет — сказать об этом
    unreal.log_warning(f"[RiseAboveIt] нет {_cfg['folder']}/{_cfg['csv']} рядом со скриптом — арена {ARENA} не поставлена")
# save=True у задачи импорта сохраняет только сам импортированный ассет — скелеты и Physics Asset остаются
# несохранёнными, и после перезапуска редактора анимации теряют скелет
step("save", eal.save_directory, DEST, True, True)
log(f"[RiseAboveIt] done (уровень с ареной {ARENA} не сохраняется — сохранить вручную)")
