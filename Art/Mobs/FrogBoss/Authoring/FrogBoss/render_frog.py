# Превью босса-лягушки (Workbench): blender.exe -b FrogBoss.blend --python render_frog.py -- <out_dir> [action кадр|all] [вид]
# Рядом капсула игрока 1.8 м — для масштаба. Без action — набор ракурсов в покое.
import bpy, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(args[0])
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
arm = bpy.data.objects["Armature"]
VIDEO = len(args) > 2 and args[2] == "all"
VIEW = args[3] if len(args) > 3 else "34"
if len(args) > 2:
    arm.animation_data.action = bpy.data.actions[args[1]]
    if VIDEO:
        sc.frame_start, sc.frame_end = 0, int(arm.animation_data.action.frame_range[1]) - 1
    else:
        sc.frame_set(int(args[2]))
toon = any(m.name == "M_Outline" for m in bpy.data.materials)
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.color_type = "TEXTURE"
if toon:
    sh.light, sh.show_backface_culling = "FLAT", True
else:
    sh.light, sh.show_shadows, sh.show_cavity = "STUDIO", True, True
sc.world = sc.world or bpy.data.worlds.new("W")
sc.world.color = (0.16, 0.17, 0.2)
sc.render.resolution_x, sc.render.resolution_y = 1000, 800

bpy.ops.mesh.primitive_plane_add(size=600)
g = bpy.data.materials.new("M_G"); g.diffuse_color = (0.42, 0.36, 0.26, 1); bpy.context.object.data.materials.append(g)
bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.8, location=(4.5, -5.0, 0.9))
player = bpy.context.object
pm = bpy.data.materials.new("M_P"); pm.diffuse_color = (0.6, 0.65, 0.75, 1); player.data.materials.append(pm)

cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_end = 500
K = 8 / 7                                          # ракурсы подобраны под лягушку 7 м, сейчас 8 м
def aim(loc, target, lens):
    cam.location = Vector(loc) * K
    cam.rotation_euler = (Vector(target) * K - cam.location).to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
def shoot(name, loc, target, lens, extras=False):
    player.hide_render = not extras
    aim(loc, target, lens)
    sc.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)

VIEWS = {   # для анимаций: ракурс и цель
    "34": ((11, -12, 6), (0, 0, 2.0), 35),
    "side": ((19, -2, 4), (0, -2.5, 2.2), 30),
    "front": ((2, -22, 4.5), (0, -6, 2.2), 30),
    "tongue": ((22, -8, 6), (0, -6, 2.7), 35),
    "jump": ((12, -15, 9), (0, 0, 4.0), 35),
    "jump_side": ((22, 1, 6), (0, 3, 4.0), 34),
    "proc_up": ((24, -22, 12), (0, 0, 5.5), 35),
    "proc_forward": ((24, -22, 12), (0, -5, 5.5), 35),
    "proc_side": ((24, -22, 12), (4, 0, 5.5), 35),
    "player": ((1.6, -10.5, 1.65 / K), (0, -2, 3.0), 20),
    "far": ((22, -28, 8), (0, -6, 2.5), 26),            # язык и прыжок целиком
}
if VIEW.startswith('proc_'):
    point = (0,-10,.04) if VIEW=='proc_forward' else (8,0,.04) if VIEW=='proc_side' else (0,0,.04)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.2,minor_radius=.045,location=point)
    marker=bpy.context.object;marker.name='Preview_LandingTarget'
    material=bpy.data.materials.new('Preview_Target');material.diffuse_color=(1,.45,.08,1);marker.data.materials.append(material)
if VIDEO:
    sc.render.resolution_x, sc.render.resolution_y = (1280,960) if VIEW.startswith("proc_") else (960,720)
    player.location.x = 300
    aim(*VIEWS[VIEW])
    sc.render.filepath = os.path.join(out, args[1] + "_" + VIEW, "f_####")
    bpy.ops.render.render(animation=True)
elif len(args) > 2:
    player.location.x = 300
    loc, tgt, lens = VIEWS[VIEW]
    shoot(f"{args[1]}_{int(args[2]):03d}_{VIEW}", loc, tgt, lens)
else:
    shoot("01_front", (0, -17, 3.5), (0, 0, 2.2), 35)
    shoot("02_three_quarter", (11, -12, 6), (0, 0, 2.0), 35)
    shoot("03_side", (17, 0, 3), (0, 0, 2.0), 35)
    shoot("04_back", (-8, 13, 7), (0, 0, 2.0), 35)
    shoot("05_face", (4, -9, 4.5), (0, -2.5, 3.3), 55)
    shoot("06_scale", (12, -16, 3), (1.5, -2, 2.0), 30, True)
    shoot("07_top", (0.01, 0, 22), (0, 0, 0), 35)
    shoot("08_player_eye", (2.6, -10.5, 1.65 / K), (0, -2, 3.0), 18, False)   # из глаз игрока (FOV 90)
