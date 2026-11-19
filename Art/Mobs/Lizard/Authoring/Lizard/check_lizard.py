import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector as V
H=Path(__file__).resolve().parent;meta=json.loads((H/'build_report.json').read_text());arm=bpy.data.objects['Armature'];obj=bpy.data.objects['SK_Lizard'];sc=bpy.context.scene;B=arm.data.bones
bm=bmesh.new();bm.from_mesh(obj.data);assert all(e.is_manifold for e in bm.edges);bm.free()
for v in obj.data.vertices:assert v.groups and abs(sum(g.weight for g in v.groups)-1)<1e-5
def snapshot(n,f):
 arm.animation_data.action=bpy.data.actions['A_Lizard_'+n];sc.frame_set(f);return {p.name:p.matrix.copy() for p in arm.pose.bones}
def err(a,b):return max(abs(a[n][i][j]-b[n][i][j]) for n in a for i in range(4) for j in range(4))
idle=snapshot('Idle',0);report={'status':'PASS','clips':{},'connected_pairs':[(b.parent.name,b.name,b.parent.length) for b in B if b.use_connect]}
for name,info in meta['clips'].items():
 first=snapshot(name,0);minimum=1e9;gap=length=drift=tail_bend=0.;contacts={};prev={};jump=0.;settled=None;still=0.
 if name in ['Attack_Bite','Hit','Death']:assert err(first,idle)<.0001,(name,'start')
 for f in range(info['frames']+1):
  mats=snapshot(name,f);assert arm.pose.bones['root'].location.length<1e-6
  for p in arm.pose.bones:
   assert (p.scale-V((1,1,1))).length<1e-5
   length=max(length,abs((p.tail-p.head).length-p.bone.length))
   if p.bone.use_connect:gap=max(gap,(p.head-p.parent.tail).length)
   if p.name in prev:
    q=p.matrix.to_quaternion();jump=max(jump,2*math.acos(min(1.,abs(q.dot(prev[p.name])))))
   prev[p.name]=p.matrix.to_quaternion()
  for i in range(1,14):
   a=arm.pose.bones[f'tail_{i:02d}'];b=arm.pose.bones[f'tail_{i+1:02d}'];tail_bend=max(tail_bend,(a.tail-a.head).angle(b.tail-b.head))
  if name=='Move':
   support=0
   for key,phase in {'front_l':0,'hind_r':.25,'front_r':.5,'hind_l':.75}.items():
    p=(f/72+phase)%1;point=mats[key+'_foot'].translation-V((0,meta['reference_speed_m_s']*f/30,0))
    if p<=.75+1e-8:
     support+=1
     if key in contacts:drift=max(drift,(point-contacts[key]).length)
     else:contacts[key]=point.copy()
    else:contacts.pop(key,None)
   assert support>=3,(f,'support')
  ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();minimum=min(minimum,min(v.co.z for v in mesh.vertices));ev.to_mesh_clear()
  if name=='Death' and f==84:settled=mats
  if settled:still=max(still,err(settled,mats))
 assert minimum>-.001 and gap<.0001 and length<.0001,(name,'geometry',minimum,gap,length)
 assert drift<.0001 and tail_bend<math.radians(30) and jump<math.radians(35),(name,'motion',drift,math.degrees(tail_bend),math.degrees(jump))
 if info['loop']:assert err(first,mats)<.0001,(name,'loop')
 if name in ['Attack_Bite','Hit']:assert err(mats,idle)<.0001,(name,'end')
 if name=='Death':assert still<.00001,('death still',still)
 report['clips'][name]={'min_skin_z_m':minimum,'joint_gap_m':gap,'length_error_m':length,'planted_foot_drift_m':drift,'max_tail_bend_deg':math.degrees(tail_bend),'max_frame_rotation_deg':math.degrees(jump),'settled_motion':still}
(H/'pose_report.json').write_text(json.dumps(report,indent=2));print('LIZARD POSES PASS',report)
