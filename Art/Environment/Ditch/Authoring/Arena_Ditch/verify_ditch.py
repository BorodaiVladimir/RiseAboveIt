# Кадры блокаута «Канавы» только из выгрузки (Export/*.fbx + ArenaDitch_Layout.csv), как это соберёт UE.
#   blender.exe -b --factory-startup --python Arena_Ditch/verify_ditch.py -- [out_dir]
# Маркеры: зелёный конус — PlayerStart, красные — наземные спавны, синие — водяные, фиолетовый — босс.
import bpy, os, sys, csv, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ditch_shape as S

EXP = os.path.join(HERE, "Export")
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 1 else os.path.join(HERE, "verify")
os.makedirs(OUT, exist_ok=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
scene = bpy.context.scene
for f in sorted(os.listdir(EXP)):
    if f.startswith("SM_Ditch_") and f.endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=os.path.join(EXP, f))
for o in scene.objects:
    if o.name.startswith("UCX_") or o.name.startswith("SM_Ditch_Boundary"):
        o.hide_render = True

def marker(name, loc, yaw_ue, rgb):
    bpy.ops.mesh.primitive_cone_add(radius1=0.7, depth=1.8, location=loc + Vector((0, 0, 0.9)))
    c = bpy.context.object
    c.name = name
    c.rotation_euler = (0, math.radians(90), -math.radians(yaw_ue))
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    c.data.materials.append(m)
    c["marker"] = True

rows = list(csv.DictReader(open(os.path.join(EXP, "ArenaDitch_Layout.csv"), encoding="utf-8")))
for r in rows:
    loc = Vector((float(r["X"]) / 100, -float(r["Y"]) / 100, float(r["Z"]) / 100))
    if r["Kind"] == "StaticMesh" and r["Asset"] == "SM_Safe_Workbench":
        before = set(scene.objects)
        bpy.ops.import_scene.fbx(filepath=os.path.join(HERE, "..", "Arena_Earth", "Export", "SM_Safe_Workbench.fbx"))
        for o in set(scene.objects) - before:
            o.location, o.rotation_euler = loc, (0, 0, -math.radians(float(r["Yaw"])))
            o.hide_render = o.name.startswith("UCX_")
    elif r["Kind"] in ("PlayerStart", "TargetPoint"):
        lab = r["Label"]
        rgb = (0.1, 0.9, 0.2) if lab == "PlayerStart" else (0.6, 0.1, 0.9) if "Boss" in lab else \
            (0.1, 0.4, 1.0) if "Water" in lab else (1.0, 0.15, 0.1)
        marker(lab, loc, float(r["Yaw"]), rgb)

scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light, sh.color_type = "STUDIO", "TEXTURE"
sh.show_shadows, sh.show_cavity = True, True
scene.display.shading.background_type = "VIEWPORT" if hasattr(scene.display.shading, "background_type") else None
scene.world = scene.world or bpy.data.worlds.new("W")
scene.world.color = (0.55, 0.62, 0.5)
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
# маркеры — своим цветом (материал), остальное — палитрой
for o in scene.objects:
    if o.get("marker"):
        o.color = o.data.materials[0].diffuse_color

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.clip_end = 3000

def shot(name, eye, target, lens=24, ortho=None):
    cam.location = Vector(eye)
    d = Vector(target) - Vector(eye)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam.data.type, cam.data.ortho_scale = "ORTHO", ortho
    else:
        cam.data.type, cam.data.lens = "PERSP", lens
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("VERIFY shot", name)

yc = S.yc
shot("top", (-4, yc(-4), 300), (-4, yc(-4) + 0.01, 0), ortho=175)
shot("start", (S.START_X, yc(S.START_X), 1.7), (0, yc(0), 1.0), lens=18)
shot("battle", (-55, yc(-55) - 14, 9), (-10, yc(-10), 0), lens=20)
shot("boss", (22, yc(22) + 6, 3.0), (S.PIPE_X, yc(S.PIPE_X), 3), lens=20)
shot("safezone", (S.CAN_X1 + 9, yc(S.CAN_X1) + 4, 2.2), ((S.CAN_X0 + S.CAN_X1) / 2, yc(-70), 1.5), lens=20)
shot("from_top_edge", (10, yc(10) - 30, 16), (10, yc(10), 0), lens=16)
