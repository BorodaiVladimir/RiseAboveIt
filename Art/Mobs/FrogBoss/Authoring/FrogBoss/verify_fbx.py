import bpy, os
H=os.path.dirname(os.path.abspath(__file__))
expected=None
for name in ['SK_FrogBoss','A_FrogBoss_Idle','A_FrogBoss_Death','A_FrogBoss_Attack_Tongue','A_FrogBoss_Attack_JumpSlam']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=os.path.join(H,name+'.fbx'))
 arms=[o for o in bpy.data.objects if o.type=='ARMATURE']; assert len(arms)==1
 arm=arms[0]; names=set(b.name for b in arm.data.bones)
 if expected is None: expected=names
 else:
  assert names==expected,(name,names^expected)
  assert not any(o.type=='MESH' for o in bpy.data.objects)
  assert arm.animation_data and arm.animation_data.action
  act=arm.animation_data.action
  print('PASS FBX',name,'bones',len(names),'frames',list(act.frame_range))
 print('IMPORT OK',name)
