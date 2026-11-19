"""Heavy ordinary Ditch lizard: original art and baked clips, no gameplay."""
import bpy,math,sys,json,hashlib
from pathlib import Path
from mathutils import Vector as V,Matrix as M
H=Path(__file__).resolve().parent;ROOT=H.parent
sys.path[:0]=[str(ROOT/'Shared')]
import lowpoly as lp,rigkit as rk
lp.clear_scene();mb=lp.MeshBuilder(seed=61)
palette=ROOT/'Shared/T_Palette.png';original_hash=hashlib.sha256(palette.read_bytes()).hexdigest()
image=bpy.data.images.load(str(palette),check_existing=True)
mat=bpy.data.materials.new('M_Lizard');shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Closest';mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);shader.inputs['Roughness'].default_value=.78
spec=[('root',(0,0,0),(0,.2,0),None,False),('pelvis',(0,1.6,1.10),(0,.2,1.2),'root',False),('chest',(0,.2,1.2),(0,-1.15,1.2),'pelvis',True),('neck',(0,-1.15,1.2),(0,-2.05,1.05),'chest',True),('head',(0,-2.05,1.05),(0,-3.8,.93),'neck',True),('jaw',(0,-2.45,.75),(0,-4.05,.71),'head',False)]
def torso_weight(y):
 if y>1.:return {'pelvis':1.}
 if y>.2:return {'pelvis':(y-.2)/.8,'chest':1-(y-.2)/.8}
 if y>-.8:return {'chest':1.}
 q=min(1.,(-y-.8)/.8);return {'chest':1-q,'neck':q}
rows=[(2.1,1.1,.58,.49),(1.7,1.13,.99,.63),(.8,1.18,1.24,.70),(-.1,1.2,1.22,.68),(-.85,1.2,.94,.58),(-1.5,1.16,.69,.43),(-2.15,1.04,.62,.34)]
faces=mb.loft([(V((0,y,z)),V((1,0,0)),V((0,0,1)),w,h) for y,z,w,h in rows],16,'frog_green','pelvis',ring_weights=[torso_weight(y) for y,*_ in rows])
for i,face in enumerate(faces):
 a=2*math.pi*((i%16)+.5)/16
 if math.sin(a)<-.2:face[mb.L_SW]=lp.SW['frog_belly']
# Low broad skull, deep jaw and small recessed lateral eyes.
mb.loft([(V((0,y,z)),V((1,0,0)),V((0,0,1)),w,h) for y,z,w,h in [(-2.0,1.08,.61,.32),(-2.5,1.10,.92,.37),(-3.15,.98,.91,.29),(-3.9,.91,.61,.16),(-4.08,.88,.38,.12)]],12,'frog_dark','head')
mb.loft([(V((0,y,z)),V((1,0,0)),V((0,0,1)),w,h) for y,z,w,h in [(-2.4,.71,.62,.13),(-3.2,.65,.82,.14),(-4.02,.69,.49,.09)]],12,'mud','jaw')
mb.ellipsoid((0,-3.2,.805),(.68,.8,.018),12,6,'blood','jaw')
mb.ellipsoid((0,-3.1,.865),(.68,.85,.018),12,6,'eye_black','head')
for side,s in [('l',1),('r',-1)]:
 eye=V((s*.79,-2.78,1.28));spec.append(('eye_'+side,eye,eye+V((s*.12,0,0)),'head',False))
 mb.ellipsoid(eye,(.11,.15,.075),10,6,'eye_black','head')
 mb.ellipsoid(eye+V((s*.047,-.025,.005)),(.065,.10,.041),10,6,'brass','eye_'+side)
 mb.ellipsoid(eye+V((s*.085,-.05,.008)),(.012,.029,.038),8,6,'eye_black','eye_'+side)
 mb.ellipsoid((s*.73,-2.76,1.36),(.18,.27,.055),10,4,'frog_dark','head')
 mb.ellipsoid((s*.36,-3.92,1.00),(.055,.075,.019),8,4,'eye_black','head')
 for j in range(7):
  y=-2.72-j*.17;x=s*(.65-.17*(j/6)**3)
  mb.tube([(x,y,.84),(x,y,.71),(x-s*.015,y+.04,.65)],[.038,.025,.002],6,'dew','head')
  mb.tube([(x,y,.79),(x,y,.90)],[.026,.002],5,'dew','jaw')
# Broad irregular scale plates lie on the back rather than forming a dragon crest.
for row in range(7):
 y=1.55-row*.45;w=.95 if y>-.7 else .65;bone='pelvis' if y>.7 else 'chest' if y>-.8 else 'neck'
 for col in range(-2,3):
  x=col*w*.34;z=1.83-.28*(abs(col)/2)**1.6
  if y<-.8:z-=.12
  mb.ellipsoid((x,y+(col%2)*.11,z),(.22 if abs(col)<2 else .16,.29,.065),6,4,'frog_dark' if (row+col)%3 else 'mud',bone)
# One smoothly weighted tapering tail.
TN=14;TP=[V((.22*math.sin(math.pi*i/TN),2.05+6.3*i/TN,1.1-.96*(i/TN)**.65)) for i in range(TN+1)]
for i in range(TN):spec.append((f'tail_{i+1:02d}',TP[i],TP[i+1],'pelvis' if i==0 else f'tail_{i:02d}',i>0))
tr=[];tw=[]
for j in range(TN*3+1):
 t=j/(TN*3);i=min(j//3,TN-1);q=j/3-i;c=TP[i].lerp(TP[i+1],q);r=.61*(1-t)**1.2+.018
 tr.append((c,V((1,0,0)),V((0,0,1)),r,r*.72))
 w={f'tail_{i+1:02d}':1.}
 if q<.5 and i>0:w={f'tail_{i:02d}':.5-q,f'tail_{i+1:02d}':.5+q}
 if q>.5 and i<TN-1:w={f'tail_{i+1:02d}':1.5-q,f'tail_{i+2:02d}':q-.5}
 tw.append(w)
tf=mb.loft(tr,12,'frog_green','tail_01',ring_weights=tw)
for i,face in enumerate(tf):
 if math.sin(2*math.pi*((i%12)+.5)/12)<-.2:face[mb.L_SW]=lp.SW['frog_belly']
LEGS={}
for typ in ['front','hind']:
 for side,s in [('l',1),('r',-1)]:
  key=typ+'_'+side;parent='chest' if typ=='front' else 'pelvis'
  a=V((s*.95,-.85 if typ=='front' else 1.55,1.02));b=V((s*1.85,-.6 if typ=='front' else 2.0,.62));c=V((s*2.08,-1.35 if typ=='front' else 1.62,.18))
  LEGS[key]=(a,b,c,s,parent)
  for n,aa,bb,p,connected in [(key+'_upper',a,b,parent,False),(key+'_lower',b,c,key+'_upper',True),(key+'_foot',c,c+V((0,-.45,0)),key+'_lower',True)]:spec.append((n,aa,bb,p,connected))
  lr=[];lw=[]
  for t in [0.,.25,.50,.75,1.,1.25,1.50,1.75,2.]:
   v=a.lerp(b,t) if t<=1 else b.lerp(c,t-1);axis=(b-a if t<1 else c-b).normalized();u=axis.cross(V((0,0,1))).normalized();up=axis.cross(u).normalized();r=.32 if t<.5 else .30 if t<1.3 else .19
   lr.append((v,u,up,r,r*.82));blend=max(0.,min(1.,(t-.6)/.8));lw.append({key+'_upper':1-blend,key+'_lower':blend})
  mb.loft(lr,10,'frog_green',key+'_upper',ring_weights=lw)
  mb.ellipsoid(c+V((0,-.19,-.015)),(.25,.4,.11),10,6,'mud',key+'_foot')
  for toe in range(5):
   x=(toe-2)*.115;start=c+V((x,-.29,-.025));end=start+V((x*.65,-(.42-.055*abs(toe-2)),-.045))
   mb.tube([start,start.lerp(end,.6),end],[.07,.052,.025],6,'frog_dark',key+'_foot')
   mb.tube([end,end+V((0,-.13,-.018))],[.037,.002],6,'dew',key+'_foot')
obj=mb.finish('SK_Lizard',[mat],smooth_angle=42);arm=lp.build_armature('SKEL_Lizard',spec,roll_up_prefixes=('tail_',));lp.bind_rigid(mb,arm)
B=arm.data.bones;R={b.name:b.matrix_local.copy() for b in B};RI={n:m.inverted() for n,m in R.items()};sc=bpy.context.scene
def ease(f,a,b):
 t=max(0.,min(1.,(f-a)/(b-a)));return t*t*(3-2*t)
def pulse(f,a,b,c):return ease(f,a,b)*(1-ease(f,b,c))
def segment(n,a,b):
 q=(B[n].tail_local-B[n].head_local).normalized().rotation_difference((b-a).normalized())
 return M.Translation(a)@q.to_matrix().to_4x4()@R[n].to_quaternion().to_matrix().to_4x4()
PHASE={'front_l':0,'hind_r':.25,'front_r':.5,'hind_l':.75};CYCLE=72;STRIDE=.70;DUTY=.75;SPEED=STRIDE/(CYCLE/30*DUTY)
def contact(key,f):
 p=(f/CYCLE+PHASE[key])%1
 if p<=DUTY:return V((0,-STRIDE/2+STRIDE*p/DUTY,0)),True
 u=(p-DUTY)/(1-DUTY);v=STRIDE*(1-DUTY)/DUTY
 y=(2*u**3-3*u*u+1)*STRIDE/2+(u**3-2*u*u+u)*v+(-2*u**3+3*u*u)*(-STRIDE/2)+(u**3-u*u)*v
 return V((0,y,.21*math.sin(math.pi*u)**2)),False
def pose(kind,f):
 breath=.018*math.sin(2*math.pi*f/120) if kind=='Idle' else 0.;crouch=surge=pitch=yaw=jaw=fall=0.
 if kind=='Move':
  if f==72:f=0
  crouch=.025*(1-math.cos(4*math.pi*f/72));yaw=.6*math.sin(2*math.pi*f/72)
 elif kind=='Attack_Bite':
  wind=pulse(f,0,20,27);strike=pulse(f,22,30,56);crouch=.13*wind+.045*strike;surge=.18*wind-.58*strike;pitch=-2*wind+3*strike;jaw=20*pulse(f,8,23,36)-8*pulse(f,29,33,42)
 elif kind=='Hit':
  h=pulse(f,0,4,30);surge=.20*h;crouch=.12*h;pitch=-4*h;jaw=8*h
 elif kind=='Death':fall=ease(f,8,58);crouch=.40*fall;jaw=10*ease(f,4,20)
 d=M.Translation((0,surge,breath-crouch))@rk.about(R['pelvis'].translation,rk.rot(pitch,yaw,0))
 out={'root':R['root'],'pelvis':d@R['pelvis'],'chest':d@R['chest'],'neck':d@R['neck'],'head':d@R['head']}
 if kind=='Death':
  hd=d@rk.about(R['head'].translation,rk.rot(-12*fall,-12*fall,18*fall));out['head']=hd@R['head']
 else:
  hd=d@rk.about(R['head'].translation,rk.rot(-6*jaw/20,0,0));out['head']=hd@R['head']
 out['jaw']=hd@rk.about(R['jaw'].translation,rk.rot(jaw,0,0))@R['jaw']
 for s in ['l','r']:out['eye_'+s]=hd@R['eye_'+s]
 tail_points=[d@TP[0]]
 for i in range(TN):
  a=TP[i+1]-TP[i];t=(i+.5)/TN;wave=(2.5*math.sin(2*math.pi*f/72-3*t)*math.sin(math.pi*t) if kind=='Move' else .7*math.sin(2*math.pi*f/120)*math.sin(2*t)*math.sin(math.pi*t) if kind=='Idle' else 0.)
  if kind=='Death':wave=5*fall*math.sin(2*math.pi*t)+2*math.sin(f*.8)*math.sin(math.pi*t)*pulse(f,18,35,78)
  t1=(i+1)/TN;z=TP[i+1].z+(tail_points[0].z-TP[0].z)*(1-t1)**2
  dz=z-tail_points[-1].z;xy=math.sqrt(max(0.,a.length_squared-dz*dz));heading=math.atan2(a.x,a.y)-math.radians(wave+yaw)
  tail_points.append(tail_points[-1]+V((xy*math.sin(heading),xy*math.cos(heading),dz)))
  out[f'tail_{i+1:02d}']=segment(f'tail_{i+1:02d}',tail_points[i],tail_points[i+1])
 for key,(a,b,c,s,parent) in LEGS.items():
  hip=d@a;target=c.copy()
  if kind=='Move':target+=contact(key,f)[0]
  if kind=='Death':target+=V((s*.10*fall,.1*fall,0))
  u=(target-hip).normalized();length=(target-hip).length;l1=(b-a).length;l2=(c-b).length
  assert length<l1+l2-.001,(kind,f,key,'unreachable')
  pole=V((s*3,b.y,.65))-hip;pole=(pole-u*pole.dot(u)).normalized();x=(l1*l1-l2*l2+length*length)/(2*length);height=math.sqrt(max(0.,l1*l1-x*x));knee=hip+u*x+pole*height
  out[key+'_upper']=segment(key+'_upper',hip,knee);out[key+'_lower']=segment(key+'_lower',knee,target);out[key+'_foot']=M.Translation(target-c)@R[key+'_foot']
 # Preserve planted feet; lift only body/tail if the crouch would penetrate the floor.
 deform={n:m@RI[n] for n,m in out.items()};bottom=min(sum(((deform[obj.vertex_groups[g.group].name]@v.co)*g.weight for g in v.groups),V()).z for v in obj.data.vertices)
 assert bottom>-.001,(kind,f,'floor',bottom)
 return out
ANIMS=[('Idle',120,True),('Move',72,True),('Attack_Bite',72,False),('Hit',36,False),('Death',96,False)]
def main():
 lp.export_mesh(arm,obj,str(H/'SK_Lizard.fbx'))
 for name,end,loop in ANIMS:
  key=rk.Keyer(arm,'A_Lizard_'+name)
  for f in range(end+1):
   desired=pose(name,0 if loop and f==end else f)
   for b in B:key._key(b.name,desired[b.name],desired[b.parent.name] if b.parent else None,f)
  rk.export_anim(sc,arm,obj.name,str(H/f'A_Lizard_{name}.fbx'),end,markers=[('Bite',30)] if name=='Attack_Bite' else [])
 arm.animation_data.action=bpy.data.actions['A_Lizard_Idle'];sc.frame_set(0);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(H/'Lizard.blend'))
 assert hashlib.sha256(palette.read_bytes()).hexdigest()==original_hash
 report={'status':'PASS','bones':len(B),'bone_names':list(B.keys()),'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'vertices':len(obj.data.vertices),'clips':{n:{'frames':e,'seconds':e/30,'loop':q} for n,e,q in ANIMS},'root_motion':False,'reference_speed_m_s':SPEED,'stance_fraction':DUTY,'shared_palette_sha256':original_hash}
 (H/'build_report.json').write_text(json.dumps(report,indent=2));print('LIZARD BUILD PASS',report)
if __name__=='__main__':main()
