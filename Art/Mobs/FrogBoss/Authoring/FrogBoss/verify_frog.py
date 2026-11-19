import bpy, math
from mathutils import Vector
arm=bpy.data.objects['Armature']; sc=bpy.context.scene; obj=bpy.data.objects['SK_FrogBoss']
for name,end in [('Idle',120),('Death',60)]:
 arm.animation_data.action=bpy.data.actions['A_FrogBoss_'+name]
 lowest=100.; start=None; last=None; changed=0.
 for f in range(end+1):
  sc.frame_set(f)
  mats={b.name:b.matrix.copy() for b in arm.pose.bones}
  for side in ['l','r']:
   eye=arm.pose.bones['eye_'+side]
   assert (eye.scale-Vector((1,1,1))).length<1e-6,'Eye must not shrink'
   assert eye.location.length<1e-5,'Eye must not retract'
   local=arm.pose.bones['head'].matrix.inverted() @ eye.matrix
   rest=arm.data.bones['head'].matrix_local.inverted() @ eye.bone.matrix_local
   assert max(abs(local[i][j]-rest[i][j]) for i in range(4) for j in range(4))<1e-4

  if start is None: start=mats
  changed=max(changed,max(abs(start[n][i][j]-mats[n][i][j]) for n in mats for i in range(4) for j in range(4)))
  e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=e.to_mesh()
  lowest=min(lowest,min(v.co.z for v in me.vertices)); e.to_mesh_clear()
  assert arm.pose.bones['root'].location.length < 1e-6
  if name=='Idle':
   for side in ['l','r']:
    for typ in ['arm_'+side+'_hand','leg_'+side+'_foot']:
     assert (mats[typ].translation-start[typ].translation).length<1e-4
  last=mats
 assert lowest>=-0.001,(name,lowest)
 assert changed>.01,(name,'no motion')
 if name=='Idle': assert max(abs(start[n][i][j]-last[n][i][j]) for n in last for i in range(4) for j in range(4))<1e-5
 print('PASS',name,'frames',end+1,'min_z',lowest,'motion',changed)


# Eyelids must cover the pupil from either side without changing the eyeball.
arm.animation_data.action=bpy.data.actions['A_FrogBoss_Idle']
for side in ['l','r']:
 for lid in ['lid_'+side,'lid_lower_'+side]:
  sc.frame_set(0); a=arm.pose.bones[lid].matrix.to_quaternion()
  sc.frame_set(31); b=arm.pose.bones[lid].matrix.to_quaternion()
  assert a.rotation_difference(b).angle>.8
print('PASS fixed eyeballs and independently rotating upper/lower eyelids')
