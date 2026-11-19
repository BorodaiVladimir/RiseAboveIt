import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector as V
H=Path(__file__).parent;arm=bpy.data.objects['Armature'];obj=bpy.data.objects['SK_FrogBoss'];sc=bpy.context.scene
assert len(arm.data.bones)==34
arm.animation_data.action=bpy.data.actions['A_FrogBoss_Idle'];sc.frame_set(0)
neutral={b.name:b.matrix.copy() for b in arm.pose.bones}
for name,end in [('Attack_Tongue',90),('Attack_JumpSlam',108)]:
 action=bpy.data.actions.get('A_FrogBoss_'+name);assert action,'Missing attack '+name
 arm.animation_data.action=action;low=100;root_high=0;tip_y=0
 for f in range(end+1):
  sc.frame_set(f);root=arm.pose.bones['root'].matrix.translation
  assert abs(root.x)<1e-5 and abs(root.y)<1e-5,'Jump must be vertical'
  root_high=max(root_high,root.z)
  if name=='Attack_JumpSlam' and (f<=27 or f>=62):assert abs(root.z)<1e-5
  if name=='Attack_Tongue':
   y=arm.pose.bones['tongue_08'].matrix.translation.y;tip_y=min(tip_y,y)
   if f<=24:assert y>-5,'Tongue strikes before windup ends'
  for side in ['l','r']:
   for typ,parts in [('arm',['upper','lower','hand']),('leg',['upper','lower','tarsus','foot'])]:
    for parent,child in zip(parts,parts[1:]):
     pa=arm.pose.bones[f'{typ}_{side}_{parent}'];ch=arm.pose.bones[f'{typ}_{side}_{child}']
     assert (pa.tail-ch.head).length<1e-4,(name,f,'Joint gap',pa.name,(pa.tail-ch.head).length)
   eye=arm.pose.bones['eye_'+side]
   assert (eye.scale-V((1,1,1))).length<1e-6
   assert eye.location.length<1e-5
  e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh()
  z=min(v.co.z for v in me.vertices);e.to_mesh_clear();low=min(low,z)
  assert z>=-.015,(name,f,'skin penetrates floor',z)
  if f in (0,end):
   assert max(abs(neutral[b.name][i][j]-b.matrix[i][j]) for b in arm.pose.bones for i in range(4) for j in range(4))<1e-5,'Transition differs from Idle'
 if name=='Attack_Tongue':assert tip_y<-15,(name,tip_y)
 else:assert root_high>4.4
 print('PASS',name,'floor',round(low,5),'jump',round(root_high,3),'tongue',round(tip_y,3))
for name,sha in json.loads((H/'backup_before_attacks_2026-11-17/hashes.json').read_text()).items():
 assert hashlib.sha256((H/name).read_bytes()).hexdigest()==sha,name+' changed'
print('PASS approved model, Idle and Death FBX unchanged')
