import bpy,json,math
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;before=json.loads((H/'before_report.json').read_text());arm=bpy.data.objects['Armature'];sc=bpy.context.scene
for n,info in before['bones'].items():
 b=arm.data.bones[n];assert (b.parent.name if b.parent else None)==info['parent'];assert max(abs(a-v) for a,v in zip([x for row in b.matrix_local for x in row],info['rest']))<1e-7
report={'status':'PASS','clips':{},'rest_skeleton_unchanged':True}
for name,side,peak,end in [('Jab_L','l',5,18),('Cross_R','r',8,22)]:
 arm.animation_data.action=bpy.data.actions['A_FP_Fists_'+name];first=None;points={};ik_error=gap=length=extension=0.;finger_rest=None;finger_error=0.
 for f in range(end+1):
  sc.frame_set(f);bpy.context.view_layer.update();mats={p.name:p.matrix.copy() for p in arm.pose.bones}
  if first is None:first=mats
  for p in arm.pose.bones:
   assert (p.scale-Vector((1,1,1))).length<1e-6
   length=max(length,abs((p.tail-p.head).length-p.bone.length))
   if p.bone.use_connect:gap=max(gap,(p.head-p.parent.tail).length)
  assert arm.pose.bones['root'].location.length<1e-7
  for s in ['l','r']:
   hand=arm.pose.bones['hand_'+s];ctrl=arm.pose.bones['ik_hand_'+s];ik_error=max(ik_error,(hand.head-ctrl.head).length)
   shoulder=arm.pose.bones['upperarm_'+s];lower=arm.pose.bones['lowerarm_'+s];extension=max(extension,(hand.head-shoulder.head).length/(shoulder.bone.length+lower.bone.length))
  finger={n:mats['hand_'+n[-1]].inverted()@m for n,m in mats.items() if n.startswith(('index_','middle_','ring_','pinky_','thumb_'))}
  if finger_rest is None:finger_rest=finger
  finger_error=max(finger_error,max(abs(finger[n][i][j]-finger_rest[n][i][j]) for n in finger for i in range(4) for j in range(4)))
  if f in [0,peak,end]:points[str(f)]={'wrist':list(arm.pose.bones['hand_'+side].head),'knuckle':list(arm.pose.bones['middle_01_'+side].tail),'shoulder':list(arm.pose.bones['upperarm_'+side].head)}
 forward=points['0']['wrist'][1]-points[str(peak)]['wrist'][1];ratio=forward/before['clips'][name]['forward_wrist_travel_m']
 assert ratio>=1.65,(name,'still short',forward,ratio)
 assert ik_error<.0001 and gap<.0001 and length<.0001 and extension<.99 and finger_error<.0001,(name,ik_error,gap,length,extension,finger_error)
 assert max(abs(first[n][i][j]-mats[n][i][j]) for n in mats for i in range(4) for j in range(4))<.0001,('guard return',name)
 report['clips'][name]={'forward_wrist_travel_m':forward,'travel_ratio':ratio,'points':points,'max_ik_error_m':ik_error,'max_joint_gap_m':gap,'max_length_error_m':length,'max_extension_ratio':extension,'finger_pose_error':finger_error,'frames':end,'impact':peak}
(H/'pose_report.json').write_text(json.dumps(report,indent=2));print('PUNCH REACH PASS',report)
