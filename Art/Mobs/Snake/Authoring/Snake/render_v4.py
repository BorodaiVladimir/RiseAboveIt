import bpy,sys
from pathlib import Path
from mathutils import Vector as V
H=Path(__file__).resolve().parent;args=sys.argv[sys.argv.index('--')+1:];kind=args[0];view=args[1] if len(args)>1 else 'combat';single=int(args[2]) if len(args)>2 else None
sc=bpy.context.scene;arm=bpy.data.objects['Armature'];sc.render.engine='BLENDER_WORKBENCH';sh=sc.display.shading
sh.light='STUDIO';sh.color_type='TEXTURE';sh.show_shadows=True;sh.show_cavity=True;sh.background_type='WORLD'
sh.show_specular_highlight=False
sc.world=sc.world or bpy.data.worlds.new('W');sc.world.color=(.16,.17,.16);sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1100;sc.render.resolution_y=760;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,-.016));g=bpy.data.materials.new('Floor');g.diffuse_color=(.24,.245,.23,1);bpy.context.object.data.materials.append(g)
grid=bpy.data.materials.new('Grid');grid.diffuse_color=(.15,.16,.145,1)
for x in range(-20,21,2):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,0,-.01));o=bpy.context.object;o.scale=(.012,40,.002);o.data.materials.append(grid)
for y in range(-32,23,2):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,y,-.009));o=bpy.context.object;o.scale=(24,.012,.002);o.data.materials.append(grid)
if kind=='Combat':
 target=bpy.data.materials.new('PlayerTarget');target.diffuse_color=(.9,.39,.12,1)
 bpy.ops.mesh.primitive_torus_add(major_radius=.35,minor_radius=.035,location=(0,-10,.045));bpy.context.object.data.materials.append(target)
cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);sc.collection.objects.link(cam);sc.camera=cam;cd.clip_start=.02;cd.clip_end=200
out=H/'preview_v4'/f'{kind}_{view}';out.mkdir(parents=True,exist_ok=True)
def smooth(f,a,b):
 t=max(0.,min(1.,(f-a)/(b-a)));return t*t*(3-2*t)
end=360 if kind=='Combat' else int(bpy.data.actions['A_Snake_'+kind].frame_range[1])+1
for f in ([single] if single is not None else range(end)):
 travel=V();zoom=1.
 if kind=='Combat':
  travel.y=-2*min(f,60)/30;zoom=smooth(f,60,120)*(1-.65*smooth(f,248,300))
  if f<60:action,af='Move',f
  elif f<120:action,af='Coil_Enter',f-60
  elif f<150:action,af='Coil_Idle',f-120
  elif f<240:action,af='Attack_Combo',f-150
  else:action,af='Death',min(102,f-240)
 else:action,af=kind,f
 arm.animation_data.action=bpy.data.actions['A_Snake_'+action];sc.frame_set(af);arm.location=travel;bpy.context.view_layer.update()
 if view=='head':
  head=arm.matrix_world@arm.pose.bones['head'].head;loc=head+V((2.4,-3.9,1.0));look=head+V((0,-.7,-.1));lens=60
 elif view=='front':loc=V((0,-10.5,2.5))+travel;look=V((0,-2.7,1.4))+travel;lens=62
 elif view=='top':loc=V((0,2,29))+travel;look=V((0,2,0))+travel;lens=38
 else:
  loc=V((17,-19,21)).lerp(V((8,-12,8)),zoom)+travel;look=V((0,5,.6)).lerp(V((0,-1.2,1.7)),zoom)+travel;lens=42
 cam.location=loc;cam.rotation_euler=(look-loc).to_track_quat('-Z','Y').to_euler();cd.lens=lens
 sc.render.filepath=str(out/f'f_{f:04d}.png');bpy.ops.render.render(write_still=True)
print('SNAKE V2 RENDER PASS',kind,view)
