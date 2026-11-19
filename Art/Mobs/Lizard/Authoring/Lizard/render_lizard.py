import bpy,sys,json
from pathlib import Path
from mathutils import Vector as V
H=Path(__file__).resolve().parent;args=sys.argv[sys.argv.index('--')+1:];kind=args[0] if args else 'Combat';view=args[1] if len(args)>1 else 'angle';single=int(args[2]) if len(args)>2 else None
meta=json.loads((H/'build_report.json').read_text());sc=bpy.context.scene;arm=bpy.data.objects['Armature']
sc.render.engine='BLENDER_WORKBENCH';sh=sc.display.shading;sh.light='STUDIO';sh.color_type='TEXTURE';sh.show_shadows=False;sh.show_cavity=True;sh.show_specular_highlight=False;sh.background_type='WORLD'
sh.cavity_type='BOTH';sh.cavity_valley_factor=1.4;sh.cavity_ridge_factor=1.;sh.curvature_ridge_factor=1.;sh.curvature_valley_factor=1.
sc.world=sc.world or bpy.data.worlds.new('World');sc.world.color=(.18,.19,.17);sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1100;sc.render.resolution_y=760;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.02));mat=bpy.data.materials.new('Ground');mat.diffuse_color=(.26,.27,.24,1);bpy.context.object.data.materials.append(mat)
grid=bpy.data.materials.new('Grid');grid.diffuse_color=(.17,.18,.15,1)
data=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',data);sc.collection.objects.link(cam);sc.camera=cam;data.lens=46
out=H/'preview'/f'{kind}_{view}';out.mkdir(parents=True,exist_ok=True)
timeline=[('Idle',30),('Move',72),('Attack_Bite',72),('Hit',36),('Death',96)]
end=sum(e for _,e in timeline) if kind=='Combat' else meta['clips'][kind]['frames']+1
for f in ([single] if single is not None else range(end)):
 action=kind;af=f;travel=0.
 if kind=='Combat':
  elapsed=0
  for n,e in timeline:
   if f<elapsed+e:action=n;af=f-elapsed;break
   elapsed+=e
  travel=-meta['reference_speed_m_s']*max(0,min(72,f-30))/30
 elif kind=='Move':travel=-meta['reference_speed_m_s']*f/30
 arm.animation_data.action=bpy.data.actions['A_Lizard_'+action];sc.frame_set(af);arm.location=(0,travel,0);bpy.context.view_layer.update()
 look=V((0,1.8+travel,.85));loc=V((13,-17+travel,11))
 if view=='side':loc=V((17,1.8+travel,4.7))
 if view=='top':loc=V((0,1.8+travel,24))
 if view=='front':loc=V((7,-15+travel,6))
 cam.location=loc;cam.rotation_euler=(look-loc).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/f'f_{f:04d}.png');bpy.ops.render.render(write_still=True)
print('LIZARD RENDER PASS',kind,view)
