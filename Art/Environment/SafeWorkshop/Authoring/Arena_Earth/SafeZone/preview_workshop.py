import bpy,sys,math,csv
from pathlib import Path
from mathutils import Matrix,Vector as V
H=Path(__file__).parent;ROOT=H.parents[1];sc=bpy.context.scene
sys.path.insert(0,str(H));from workshop_layout import SPECS
# Start from the local prop scene, then place all parts relative to the existing table.
for ob in list(bpy.data.objects):
 if ob.name.startswith('UCX_'):bpy.data.objects.remove(ob,do_unlink=True)
for label,kind,asset,position,yaw,note in SPECS:
 if kind=='StaticMesh':
  obj=bpy.data.objects[asset];obj.location=position;obj.rotation_euler.z=math.radians(-yaw)

def append(path,names,actions=False):
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):
  dst.objects=[n for n in src.objects if n in names]
  if actions:dst.actions=[n for n in src.actions if n.startswith('A_RoachCrafter_')]
 for o in dst.objects:
  if o and not o.users_collection:sc.collection.objects.link(o)
 return dst.objects
rows=list(csv.DictReader((ROOT/'Arena_Earth/Export/ArenaEarth_Layout.csv').open(encoding='utf8')))
b=next(r for r in rows if r['Label']=='SafeZone_Workbench')
bench=V((float(b['X'])/100,-float(b['Y'])/100,float(b['Z'])/100));angle=-math.radians(float(b['Yaw']))
for o in append(ROOT/'Arena_Earth/Arena_Earth.blend',['SM_Earth_SafeZone','SM_Safe_Workbench']):
 if o.name=='SM_Earth_SafeZone':o.matrix_world=Matrix.Rotation(-angle,4,'Z') @ Matrix.Translation(-bench)
append(ROOT/'RoachCrafter/RoachCrafter_Toon.blend',['Armature','SK_RoachCrafter'],True)
arm=bpy.data.objects['Armature'];arm.location=(0,-2,0);arm.rotation_euler.z=math.pi
arm.animation_data.action=bpy.data.actions['A_RoachCrafter_Work'];sc.frame_set(12)
# Rest the current part between the crafter's hands; this is a visual prop only.
old=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'Loot/Export/SM_Loot_Gear.fbx'))
for o in set(bpy.data.objects)-old:
 if o.type=='MESH':o.location=(0,-1.15,1.095);o.scale=(.8,.8,.8)
# Cycles does not honor viewport backface culling on the inverted outline hull.
# Keep the approved outline, but make its camera-facing back faces transparent.
for mat in bpy.data.materials:
 if mat.name.startswith('M_Outline'):
  mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
  out=nt.nodes.new('ShaderNodeOutputMaterial');mix=nt.nodes.new('ShaderNodeMixShader')
  geo=nt.nodes.new('ShaderNodeNewGeometry');black=nt.nodes.new('ShaderNodeEmission')
  black.inputs['Color'].default_value=(.008,.005,.007,1)
  transparent=nt.nodes.new('ShaderNodeBsdfTransparent')
  mix.inputs[0].default_value=1.0  # Preview only: Cycles does not cull the hull like UE/Workbench.
  nt.links.new(black.outputs[0],mix.inputs[1]);nt.links.new(transparent.outputs[0],mix.inputs[2])
  nt.links.new(mix.outputs[0],out.inputs['Surface'])
# Plane beyond the doorway, no game geometry changes.
bpy.ops.mesh.primitive_plane_add(size=50,location=(0,0,-.27))
ground=bpy.context.object;ground.name='Preview_OutsideGround'
m=bpy.data.materials.new('Preview_Soil');m.diffuse_color=(.15,.11,.07,1);ground.data.materials.append(m)
sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True
sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Workshop_World');sc.world.use_nodes=True
bg=sc.world.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(.27,.34,.43,1);bg.inputs['Strength'].default_value=.18
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=1.0

def aim(o,target):o.rotation_euler=(V(target)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,color,size,target):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
 o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;aim(o,target)
area('Workshop_Warm',(-.7,.4,3.0),180,(1,.75,.46),2.2,(0,-1.7,.8))
area('Door_SoftFill',(3,2,2.8),100,(.64,.78,1),3.,(-1,-1.8,1.2))
d=bpy.data.lights.new('LED_Warm','POINT');d.energy=60;d.color=(1,.65,.3);d.shadow_soft_size=.25
o=bpy.data.objects.new('LED_Warm',d);sc.collection.objects.link(o);o.location=(-1.4,1.1,2.7)
cd=bpy.data.cameras.new('Workshop_Camera');cam=bpy.data.objects.new('Workshop_Camera',cd);sc.collection.objects.link(cam);sc.camera=cam
out=H/'preview';out.mkdir(exist_ok=True)
shots=[('01_player',(0.5,2.65,1.7),(-.55,-1.6,1.30),30),('02_workbench',(2.65,.35,2.0),(-.35,-1.55,1.1),28),('03_entry',(6.15,4.2,1.75),(-.5,-1.35,1.30),24)]
bpy.ops.wm.save_as_mainfile(filepath=str(H/'SafeZone_Workshop.blend'))
for name,loc,target,lens in shots:
 cam.location=loc;aim(cam,target);cd.lens=lens
 sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
