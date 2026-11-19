import bpy,math,json
from mathutils import Vector as V
from pathlib import Path
H=Path(__file__).parent;arm=bpy.data.objects['Armature'];obj=bpy.data.objects['SK_FrogBoss'];sc=bpy.context.scene
cases=[('Attack_JumpSlam',V((0,0,0))),('Jump_Forward_Demo',V((0,-10,0))),('Jump_Side_Demo',V((8,0,0)))]
metadata=json.loads((H/'attack_timings.json').read_text());height=metadata['jump_height_m'];T=35/30
for name,goal in cases:
 arm.animation_data.action=bpy.data.actions['A_FrogBoss_'+name];lowest=100
 for f in range(109):
  sc.frame_set(f)
  if f==108:assert (arm.pose.bones['root'].matrix.translation-goal).length<1e-4,(name,'landing target')
  for side in ('l','r'):
   for kind,parts in [('arm',['upper','lower','hand']),('leg',['upper','lower','tarsus','foot'])]:
    for pa,ch in zip(parts,parts[1:]):
     a=arm.pose.bones[f'{kind}_{side}_{pa}'];b=arm.pose.bones[f'{kind}_{side}_{ch}']
     assert (a.tail-b.head).length<1e-4,(name,f,'joint gap',a.name,(a.tail-b.head).length)
  e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();low=min(v.co.z for v in me.vertices);e.to_mesh_clear();lowest=min(lowest,low)
  assert low>=-.015,(name,f,'floor',low)
  if f==44:
   velocity=V((goal.x/T,goal.y/T,(goal.z+4*height)/T));wanted=-velocity.normalized()
   for side in ('l','r'):
    hip=arm.pose.bones['leg_'+side+'_upper'].head;foot=arm.pose.bones['leg_'+side+'_foot'].head;delta=foot-hip
    assert delta.normalized().dot(wanted)>.995,(name,'feet oppose takeoff',delta,wanted)
    if goal.length<.01:assert abs(delta.x)<.01 and abs(delta.y)<.01 and delta.z<-8,'Vertical jump legs must extend downward'
 print('PASS procedural target',name,'goal',tuple(goal),'floor',round(lowest,5))
print('ALL TARGET-DRIVEN JUMP CHECKS PASSED')
