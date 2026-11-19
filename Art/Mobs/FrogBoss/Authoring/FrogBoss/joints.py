import bpy
s=bpy.context.scene;a=bpy.data.objects['Armature'];a.animation_data.action=bpy.data.actions['A_FrogBoss_Death'];s.frame_set(30)
for n in ['pelvis','leg_l_upper','leg_l_lower','leg_l_tarsus','leg_r_upper','leg_r_lower']:
 p=a.pose.bones[n];print(n,tuple(p.head),tuple(p.tail))
