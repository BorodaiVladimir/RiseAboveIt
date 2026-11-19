import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector as V
H=Path(__file__).resolve().parent;meta=json.loads((H/'build_report.json').read_text());N=meta['body_segments'];arm=bpy.data.objects['Armature'];obj=bpy.data.objects['SK_Snake'];B=arm.data.bones;sc=bpy.context.scene
bm=bmesh.new();bm.from_mesh(obj.data);assert all(e.is_manifold for e in bm.edges);bm.free()
for v in obj.data.vertices:assert v.groups and abs(sum(g.weight for g in v.groups)-1)<1e-5
def snapshot(name,f):
 arm.animation_data.action=bpy.data.actions['A_Snake_'+name];sc.frame_set(f);return {p.name:p.matrix.copy() for p in arm.pose.bones}
normal=snapshot('Idle',0);coil=snapshot('Coil_Idle',0)
report={'status':'PASS','version':4,'clips':{},'transition_checks':{}};failures=[]
def error(a,b):return max(abs(a[n][i][j]-b[n][i][j]) for n in a for i in range(4) for j in range(4))
checks=[('Coil_Enter',0,normal),('Coil_Enter',60,coil),('Coil_Exit',0,coil),('Coil_Exit',60,normal)]
for name in ['Attack_Bite','Attack_Combo','Hit','Death']:checks.append((name,0,coil))
for name in ['Hit_Move','Death_Move']:checks.append((name,0,normal))
for name in ['Attack_Bite','Attack_Combo','Hit']:checks.append((name,meta['clips'][name]['frames'],coil))
checks.append(('Hit_Move',30,normal))
for name,f,expected in checks:
 e=error(snapshot(name,f),expected);report['transition_checks'][name+'_'+str(f)]=e
 assert e<.0002,('transition',name,f,e)
for name,info in meta['clips'].items():
 arm.animation_data.action=bpy.data.actions['A_Snake_'+name];minimum=1e6;gap=length=angle=0.;first=None;settled=None;still=0.;near=100.;near_case=None;angle_case=None;previous={};jump=0.;tail_jump=0.;tail_bend=0.;up_min=1.
 for f in range(info['frames']+1):
  sc.frame_set(f);mats={p.name:p.matrix.copy() for p in arm.pose.bones};assert arm.pose.bones['root'].location.length<1e-6
  for p in arm.pose.bones:
   assert (p.scale-V((1,1,1))).length<1e-5
   assert all(math.isfinite(q) for row in p.matrix for q in row)
   if p.name.startswith('spine_'):
    q=p.matrix.to_quaternion()
    if p.name in previous:
     step=2*math.acos(min(1.,abs(q.dot(previous[p.name]))));jump=max(jump,step)
     if int(p.name.split('_')[1])>=int(N*.7):tail_jump=max(tail_jump,step)
    previous[p.name]=q
    if not name.startswith('Death'):up_min=min(up_min,p.matrix.to_3x3().col[2].normalized().z)
   length=max(length,abs((p.tail-p.head).length-p.bone.length))
   if p.bone.use_connect:gap=max(gap,(p.head-p.parent.tail).length)
  for side in ['l','r']:
   local=mats['head'].inverted()@mats['eye_'+side];rest=B['head'].matrix_local.inverted()@B['eye_'+side].matrix_local
   assert error({'x':local},{'x':rest})<.0001,('eye',name,f)
  for i in range(1,N):
   a=arm.pose.bones[f'spine_{i:02d}'];b=arm.pose.bones[f'spine_{i+1:02d}'];bend=(a.tail-a.head).angle(b.tail-b.head)
   if bend>angle:angle=bend;angle_case=[f,i]
   if i>=int(N*.7):tail_bend=max(tail_bend,bend)
  for i in range(N):
   for j in range(i+4,N):
    t=i/N;u=j/N;r=lambda q:.40*(1-.97*q**2.1)-.13*math.exp(-18*q)
    ratio=(mats[f'spine_{i+1:02d}'].translation-mats[f'spine_{j+1:02d}'].translation).length/(r(t)+r(u))
    if ratio<near:near=ratio;near_case=[f,i,j]
  ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();minimum=min(minimum,min(v.co.z for v in me.vertices));ev.to_mesh_clear()
  if first is None:first=mats
  if name.startswith('Death') and f==90:settled=mats
  if settled:still=max(still,error(mats,settled))
 assert minimum>-.001 and gap<.0002 and length<.0002,(name,'geometry',minimum,gap,length)
 if angle>=math.radians(65):failures.append((name,'kink',math.degrees(angle),angle_case))
 if tail_bend>=math.radians(45):failures.append((name,'tail bend',math.degrees(tail_bend)))
 if jump>=math.radians(45):failures.append((name,'rotation jump',math.degrees(jump)))
 if tail_jump>=math.radians(30):failures.append((name,'tail rotation jump',math.degrees(tail_jump)))
 if up_min<-.0001:failures.append((name,'belly rolled over',up_min))
 if near<.85:failures.append((name,'body collision',near,near_case))
 if info['loop']:assert error(first,mats)<.0002,(name,'loop')
 if name.startswith('Death'):assert still<1e-5,(name,'not settled',still)
 report['clips'][name]={'frames':info['frames']+1,'min_skin_z_m':minimum,'joint_gap_m':gap,'length_error_m':length,'max_bend_deg':math.degrees(angle),'max_bend_case':angle_case,'min_body_center_clearance_ratio':near,'closest_body_case':near_case,'settled_motion':still}
 report['clips'][name].update(max_tail_bend_deg=math.degrees(tail_bend),max_frame_rotation_deg=math.degrees(jump),max_tail_frame_rotation_deg=math.degrees(tail_jump),lowest_up_dot=up_min)
if failures:report['status']='FAIL';report['failures']=failures
(H/'pose_report_v4.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('SNAKE V4 POSE',report)
assert not failures,failures
