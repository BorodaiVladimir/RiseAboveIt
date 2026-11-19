import bpy,sys,math
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;ROOT=H.parent.parent
args=sys.argv[sys.argv.index('--')+1:];version=args[0];view=args[1];single=int(args[2]) if len(args)>2 else None
sc=bpy.context.scene;arm=bpy.data.objects['Armature']
with bpy.data.libraries.load(str(ROOT/'Weapons/Sewer/Fists/Fists_Sewer.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('SK_FP_Fists_Sewer_')]
layers=[]
for o in dst.objects:
 sc.collection.objects.link(o);o.parent=arm;layers.append(o)
 for mod in o.modifiers:
  if mod.type=='ARMATURE':mod.object=arm
for o in list(bpy.data.objects):
 if o.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
sc.render.engine='BLENDER_WORKBENCH';sh=sc.display.shading;sh.light='FLAT';sh.color_type='TEXTURE';sh.show_backface_culling=True;sh.show_shadows=False;sh.show_cavity=False
sc.world=sc.world or bpy.data.worlds.new('World');sc.world.color=(.12,.14,.17);sh.background_type='WORLD';sc.view_settings.view_transform='Standard'
sc.render.resolution_x=550;sc.render.resolution_y=380;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
mark=bpy.data.materials.new('OneMetreReference');mark.diffuse_color=(.43,.48,.50,1)
for x in [-.35,.35]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,-1.02,-.15));o=bpy.context.object;o.scale=(.006,.006,.38);o.data.materials.append(mark)
for z in [-.53,.23]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-1.02,z));o=bpy.context.object;o.scale=(.35,.006,.006);o.data.materials.append(mark)
camdata=bpy.data.cameras.new('CompareCamera');cam=bpy.data.objects.new('CompareCamera',camdata);sc.collection.objects.link(cam);sc.camera=cam;camdata.clip_start=.005
if view=='fp':loc=Vector((0,0,0));look=Vector((0,-1,-.12));camdata.lens=18
else:loc=Vector((1.65,-.50,.23));look=Vector((0,-.50,-.13));camdata.lens=44
cam.location=loc;cam.rotation_euler=(look-loc).to_track_quat('-Z','Y').to_euler()
out=H/'preview'/f'{version}_{view}';out.mkdir(parents=True,exist_ok=True)
for f in ([single] if single is not None else range(82)):
 if f<15:name,af='Idle',0
 elif f<34:name,af='Jab_L',f-15
 elif f<44:name,af='Idle',0
 elif f<67:name,af='Cross_R',f-44
 else:name,af='Idle',0
 action=('Before_'+name if version=='before' and name!='Idle' else 'A_FP_Fists_'+name)
 arm.animation_data.action=bpy.data.actions[action];sc.frame_set(af);bpy.context.view_layer.update();sc.render.filepath=str(out/f'f_{f:04d}.png');bpy.ops.render.render(write_still=True)
print('COMPARE RENDER PASS',version,view)
