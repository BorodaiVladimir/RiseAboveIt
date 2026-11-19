"""Hostile snake art: recessed eyes, folding fangs, coil/strikes and physical collapse."""
import bpy,math,sys,json,hashlib
from pathlib import Path
from mathutils import Vector as V,Matrix as M
H=Path(__file__).resolve().parent;ROOT=H.parent
sys.path[:0]=[str(ROOT/'Shared'),str(ROOT/'Weapons')]
import lowpoly as lp,weapon_kit as wk,rigkit as rk
N=72;SIDES=12;FPS=30;COIL_HEAD=V((0,-1.0,2.95))
def ease(f,a,b):
 t=max(0.,min(1.,(f-a)/(b-a)));return t*t*(3-2*t)
def bump(f,a,b):return math.sin(math.pi*(f-a)/(b-a))**2 if a<f<b else 0.
def radius(t):return .40*(1-.97*t**2.1)-.13*math.exp(-18*t)
def center(t,phase=0):
 a=math.sin(math.pi*t*.95)**.7
 return V((a*math.sin(2*math.pi*2.1*t-phase),-4+20*t,.85*radius(t)+.035+.24*math.exp(-14*t)))
P=[center(i/N) for i in range(N+1)];L=[(b-a).length for a,b in zip(P,P[1:])];BN=[f'spine_{i+1:02d}' for i in range(N)]
lp.clear_scene()
original_palette=ROOT/'Shared/T_Palette.png';original_hash=hashlib.sha256(original_palette.read_bytes()).hexdigest()
source=bpy.data.images.load(str(original_palette),check_existing=True)
image=source.copy();image.name='T_Palette_Snake';pixels=list(source.pixels)
overrides={'frog_green':0x46513a,'frog_dark':0x1b241b,'frog_belly':0x8f8b68,'brass':0x9a904e,'dew':0xd2c79c,'frog_tongue':0x6b343b,'eye_black':0x0a0b08,'mud':0x4b4534}
for sw,color in overrides.items():
 index=lp.SW[sw];red,green,blue=[((color>>shift)&255)/255 for shift in [16,8,0]]
 for yy in range(64):
  shade=.7+.4*yy/63
  for xx in range(64):
   k=(((7-index//8)*64+yy)*512+index%8*64+xx)*4;pixels[k:k+4]=[min(red*shade,1),min(green*shade,1),min(blue*shade,1),1]
image.pixels.foreach_set(pixels);image.filepath_raw=str(H/'T_Palette_Snake.png');image.file_format='PNG';image.save()
mat=bpy.data.materials.new('M_Snake');nodes=mat.node_tree.nodes;shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Closest';nodes.active=tex;mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);shader.inputs['Roughness'].default_value=.65
mb=lp.MeshBuilder(seed=37);rings=[];weights=[]
for j in range(N*3+1):
 i=min(j//3,N-1);f=j/3-i;t=j/(N*3);c=center(t)
 axis=(center(min(1,t+.001))-center(max(0,t-.001))).normalized();u=V((0,0,1)).cross(axis).normalized();v=axis.cross(u).normalized()
 rings.append((c,u,v,radius(t),radius(t)*.85))
 if f<.5 and i>0:w={BN[i-1]:.5-f,BN[i]:.5+f}
 elif f>.5 and i<N-1:w={BN[i]:1.5-f,BN[i+1]:f-.5}
 else:w={BN[i]:1.}
 weights.append({n:q for n,q in w.items() if q>1e-6})
faces=mb.loft(rings,SIDES,'frog_green',BN[0],ring_weights=weights)
for fi,face in enumerate(faces):
 ring=fi//SIDES;a=2*math.pi*((fi%SIDES)+.5)/SIDES
 sw='frog_belly' if math.sin(a)<-.25 else 'frog_dark' if math.sin(a)>.05 and abs(ring%17-8)<4*math.sin(a)**2 else 'mud' if fi%37==0 else 'frog_green'
 face[mb.L_SW]=lp.SW[sw]
# Flattened skull: no projecting ball eyes or smiling lip tubes.
mb.loft([(V((0,y,z)),V((1,0,0)),V((0,0,1)),w,h) for y,z,w,h in [(-4,.67,.28,.20),(-4.45,.67,.58,.26),(-4.95,.56,.49,.19),(-5.55,.49,.26,.12)]],12,'frog_green','head')
mb.loft([(V((0,y,z)),V((1,0,0)),V((0,0,1)),w,h) for y,z,w,h in [(-4.3,.32,.25,.065),(-4.9,.28,.47,.065),(-5.53,.31,.25,.045)]],10,'frog_dark','jaw')
wk.plate(mb,[(-.35,.12),(.35,.12),(.35,-.6),(.18,-1.05),(-.18,-1.05),(-.35,-.6)],(0,-4.45,.365),(1,0,0),(0,1,0),.012,'eye_black','head')
wk.plate(mb,[(-.24,.08),(.24,.08),(.43,-.42),(.22,-1.12),(-.22,-1.12),(-.43,-.42)],(0,-4.35,.345),(1,0,0),(0,1,0),.01,'frog_tongue','jaw')
mb.ellipsoid((0,-4.45,.40),(.23,.12,.11),10,6,'eye_black','head')
FANG_ROOT={};fold=rk.rot(80,0,0)
for s,side in [(1,'l'),(-1,'r')]:
 eye=V((s*.50,-4.66,.755))
 mb.ellipsoid(eye,(.085,.115,.035),10,6,'eye_black','head')
 mb.ellipsoid(eye+V((s*.035,-.024,.010)),(.060,.080,.022),10,6,'brass','eye_'+side)
 mb.ellipsoid(eye+V((s*.058,-.051,.014)),(.009,.026,.022),8,6,'eye_black','eye_'+side)
 # Heavy integrated orbital ridge casts shade over the small slit.
 mb.ellipsoid((s*.455,-4.64,.802),(.09,.145,.018),10,4,'frog_dark','head')
 mb.ellipsoid((s*.18,-5.43,.56),(.021,.04,.013),6,4,'eye_black','head')
 root=V((s*.29,-5.10,.42));FANG_ROOT[side]=root
 unfolded=[root,root+V((s*.008,.015,-.14)),root+V((-s*.012,.075,-.30)),root+V((-s*.035,.14,-.43))]
 folded=[root+fold.to_3x3()@(p-root) for p in unfolded]
 mb.tube(folded,[.052,.043,.023,.0025],8,'dew','fang_'+side)
 for k in range(5):
  y=-4.52-k*.155;x=s*(.29+.04*math.sin(k*.8));base=V((x,y,.35))
  mb.tube([base,base+V((0,.015,.055)),base+V((0,.05,.085))],[.013,.010,.0015],5,'dew','jaw')
mb.tube([(0,-4.92,.37),(0,-5.23,.37)],[.019,.013],5,'frog_tongue','tongue_base')
for s,side in [(1,'l'),(-1,'r')]:mb.tube([(0,-5.21,.37),(s*.10,-5.44,.37)],[.013,.002],4,'frog_tongue','tongue_'+side)
obj=mb.finish('SK_Snake',[mat],smooth_angle=42)
spec=[('root',(0,0,0),(0,.15,0),None,False)]
for i,n in enumerate(BN):spec.append((n,P[i],P[i+1],'root' if i==0 else BN[i-1],i>0))
spec += [('head',P[0],(0,-5.4,.56),'root',False),('jaw',(0,-4.3,.38),(0,-5.53,.31),'head',False)]
for s,side in [(1,'l'),(-1,'r')]:
 eye=V((s*.45,-4.66,.79));spec.append(('eye_'+side,eye,eye+V((s*.15,0,0)),'head',False))
 root=FANG_ROOT[side];spec.append(('fang_'+side,root,root+fold.to_3x3()@V((0,.02,-.25)),'head',False))
spec += [('tongue_base',(0,-4.92,.37),(0,-5.23,.37),'jaw',False),('tongue_l',(0,-5.21,.37),(.10,-5.44,.37),'tongue_base',False),('tongue_r',(0,-5.21,.37),(-.10,-5.44,.37),'tongue_base',False)]
arm=lp.build_armature('SKEL_Snake',spec,roll_up_prefixes=('spine_',));lp.bind_rigid(mb,arm)
B=arm.data.bones;R={b.name:b.matrix_local.copy() for b in B};RI={n:m.inverted() for n,m in R.items()}
samples=[(v.co.copy(),[(obj.vertex_groups[g.group].name,g.weight) for g in v.groups]) for v in obj.data.vertices]
def bezier(a,b,c,d,t):return a*(1-t)**3+b*(3*(1-t)**2*t)+c*(3*(1-t)*t*t)+d*t**3
def body_roll(t,fall):return 95*fall*(.75+.25*math.sin(math.pi*t))
def coil_point(t,head,scale,fall=0.,twitch=0.):
 neck=.16;u=max(0.,(t-neck)/(1-neck));turns=3.1-1.5*fall
 r=.85+.55*fall+(1.15+.25*fall)*u
 z=.45+2.2*(1-u)**1.5
 angle=2*math.pi*turns*u+twitch*math.sin(math.pi*u)*math.sin(4*math.pi*u)
 roll=math.radians(body_roll(t,fall));floor=radius(t)*math.sqrt(math.sin(roll)**2+.85**2*math.cos(roll)**2)+.035
 z=z*(1-fall)+floor*fall
 if t<neck:
  q1=head+V((0,.4,.04*(1-fall)))
  inner=.85+.55*fall
  q2=V((inner*scale,-1.4*scale,2.65*(1-fall)+floor*fall))
  q3=V((inner*scale,0,2.65*(1-fall)+floor*fall))
  return bezier(head,q1,q2,q3,t/neck)
 return V((r*math.cos(angle)*scale,r*math.sin(angle)*scale,z))
def chain(head,phase,coil,fall,twitch,normal_death=False):
 dense=480;ts=[j/dense for j in range(dense+1)]
 def curve(scale):
  result=[]
  for t in ts:
   p=center(t,phase);p+=(head-P[0])*(1-t)**2
   p=head+V(((p.x-head.x)*scale,(p.y-head.y)*scale,p.z-head.z))
   if normal_death:
    roll=math.radians(body_roll(t,fall));p.z=radius(t)*math.sqrt(math.sin(roll)**2+.85**2*math.cos(roll)**2)+.035+.24*math.exp(-14*t)*(1-fall)
    start_roll=math.radians(body_roll(0,fall));start_z=radius(0)*math.sqrt(math.sin(start_roll)**2+.85**2*math.cos(start_roll)**2)+.035+.24*(1-fall)
    p.z+=(head.z-start_z)*(1-t)**2
    p.x+=twitch*math.sin(math.pi*t)*math.sin(5*math.pi*t)
   c=coil_point(t,head,scale,fall,twitch)
   result.append(p.lerp(c,coil))
  result[0]=head.copy();return result
 # All control points are affine in XY scale; sample them once per pose.
 base_curve=curve(0.);unit_curve=curve(1.);delta_curve=[b-a for a,b in zip(base_curve,unit_curve)]
 def march(scale):
  points_on_curve=[a+d*scale for a,d in zip(base_curve,delta_curve)];points=[points_on_curve[0]];index=1
  for length in L:
   a=points[-1]
   while index<len(points_on_curve) and (points_on_curve[index]-a).length_squared<length*length:index+=1
   if index==len(points_on_curve):return None
   p,q=points_on_curve[index-1],points_on_curve[index];d=q-p;v=p-a
   disc=max(0.,v.dot(d)**2-d.length_squared*(v.length_squared-length*length))
   u=max(0.,min(1.,(-v.dot(d)+math.sqrt(disc))/d.length_squared));points.append(p+d*u)
  return points
 low,high=.01,4.
 assert march(high) is not None,'Coil curve is too short'
 for _ in range(24):
  mid=(low+high)/2
  if march(mid) is None:low=mid
  else:high=mid
 return march(high)

TRANSITION_ENDS=None
def transition_chain(q,head):
 global TRANSITION_ENDS
 if TRANSITION_ENDS is None:
  TRANSITION_ENDS=(chain(P[0],0,0,0,0),chain(COIL_HEAD,0,1,0,0))
 return blend_chain(*TRANSITION_ENDS,q,head)

def blend_chain(normal,coiled,q,head):
 out=[head.copy()];last=[None,None]
 for i,length in enumerate(L):
  dirs=[normal[i+1]-normal[i],coiled[i+1]-coiled[i]];angles=[]
  for j,d in enumerate(dirs):
   a=math.atan2(d.x,d.y)
   reference=last[j] if last[j] is not None else (angles[0] if j else a)
   while a-reference>math.pi:a-=2*math.pi
   while a-reference<-math.pi:a+=2*math.pi
   angles.append(a);last[j]=a
  angle=angles[0]*(1-q)+angles[1]*q;z=dirs[0].z*(1-q)+dirs[1].z*q;xy=math.sqrt(max(0.,length*length-z*z))
  out.append(out[-1]+V((xy*math.sin(angle),xy*math.cos(angle),z)))
 return out
def pulse(f,start,peak,end):return ease(f,start,peak)*(1-ease(f,peak,end))
def segment(n,a,b):
 # A world-up frame avoids the shortest-arc quaternion's antipodal roll flip.
 t=(int(n.split('_')[1])-.5)/N
 up=V((0,.6*(1-ease(t,0,.22)),1))
 y=(b-a).normalized();x=y.cross(up).normalized();z=x.cross(y).normalized()
 frame=M((x,y,z)).transposed().to_4x4();frame.translation=a
 return frame
def pose(kind,f):
 coil=0.;fall=0.;phase=0.;yaw=pitch=roll=tongue=twitch=0.;jaw=0.;head=P[0].copy();normal_death=False
 if kind in ['Idle','Move']:
  period=120 if kind=='Idle' else 60
  if f==period:f=0
  phase=2*math.pi*f/60 if kind=='Move' else .015*math.sin(2*math.pi*f/120)
  yaw=.45*math.sin(2*math.pi*f/period)
  if kind=='Idle':tongue=.55*bump(f,54,65);jaw=2*tongue/.55
 elif kind in ['Coil_Enter','Coil_Exit']:
  q=f if kind=='Coil_Enter' else 60-f;coil=ease(q,0,60);head=P[0].lerp(COIL_HEAD,coil);jaw=20*coil
 elif kind in ['Coil_Idle','Attack_Bite','Attack_Combo','Hit','Death']:
  coil=1.;head=COIL_HEAD.copy();jaw=20
  if kind=='Coil_Idle':
   if f==90:f=0
   breath=math.sin(2*math.pi*f/90);head.z+=.045*breath;jaw+=2*breath;yaw=.6*breath;tongue=.18*bump(f,48,59)
  elif kind in ['Attack_Bite','Attack_Combo']:
   peaks=[18] if kind=='Attack_Bite' else [18,42,66]
   for index,peak in enumerate(peaks):
    strike=pulse(f,peak-8,peak,peak+12);wind=pulse(f,peak-16,peak-9,peak-6)
    side=[0,-.28,.32][index];reach=[2.,2.15,2.4][index]
    head+=V((side*strike,.28*wind-reach*strike,.18*wind-1.5*strike));yaw+=[0,-5,6][index]*strike;pitch+=-8*wind+4*strike
    gape=26*pulse(f,peak-12,peak-3,peak+3);snap=15*pulse(f,peak-1,peak+3,peak+8);jaw+=gape-snap
  elif kind=='Hit':
   h=pulse(f,0,3,30);head+=V((-.22*h,.35*h,.12*h));yaw=-10*h;pitch=-7*h;jaw+=14*h
  else:
   fall=ease(f,8,74);twitch=.16*bump(f,20,85)*math.sin(f*1.2)
   head=COIL_HEAD.lerp(V((-1.1,-4.8,.72)),fall);head+=V((.12*twitch,0,.06*bump(f,2,10)))
   roll=95*ease(f,9,32);yaw=-22*fall;pitch=-5*bump(f,0,12);jaw=20+23*ease(f,4,18)-8*ease(f,35,75)
 elif kind in ['Hit_Move','Death_Move']:
  if kind=='Hit_Move':
   h=pulse(f,0,3,30);head+=V((-.18*h,.25*h,.10*h));yaw=-9*h;pitch=-5*h;jaw=10*h
  else:
   normal_death=True;fall=ease(f,8,74);twitch=.16*bump(f,20,85)*math.sin(f*1.2)
   head=P[0].lerp(V((1.1,-4.2,.72)),ease(f,6,32));roll=95*ease(f,9,32);yaw=-22*fall;jaw=35*ease(f,4,18)
 if kind.startswith('Death'):tongue=.30*fall
 points=transition_chain(coil,head) if kind in ['Coil_Enter','Coil_Exit'] else chain(head,phase,coil,fall,twitch,normal_death)
 if kind=='Death':
  dead=chain(V((-1.1,-4.8,.72)),0,0,1,0,True)
  alive=chain(COIL_HEAD,0,1,0,0)
  points=blend_chain(alive,dead,fall,head)
 out={'root':R['root']}
 for i,n in enumerate(BN):out[n]=segment(n,points[i],points[i+1])@rk.rot(0,0,body_roll((i+.5)/N,fall))
 hd=M.Translation(head-P[0])@rk.about(P[0],rk.rot(pitch,yaw,roll));jd=hd@rk.about(R['jaw'].translation,rk.rot(jaw,0,0));td=jd@M.Translation((0,-tongue,0))
 out['head']=hd@R['head'];out['jaw']=jd@R['jaw']
 for side in ['l','r']:
  out['eye_'+side]=hd@R['eye_'+side]
  deploy=max(0.,min(1.,(jaw-4)/22));out['fang_'+side]=hd@rk.about(FANG_ROOT[side],rk.rot(-80*deploy,0,0))@R['fang_'+side]
 for n in ['tongue_base','tongue_l','tongue_r']:out[n]=td@R[n]
 deform={n:m@RI[n] for n,m in out.items()};bottom=min(sum(((deform[n]@co)*w for n,w in weights),V()).z for co,weights in samples)
 if abs(bottom-.02)>1e-7:
  lift=M.Translation((0,0,.02-bottom));out={n:(m if n=='root' else lift@m) for n,m in out.items()}
 return out
ANIMS=[('Idle',120,True),('Move',60,True),('Coil_Enter',60,False),('Coil_Idle',90,True),('Attack_Bite',48,False),('Attack_Combo',90,False),('Coil_Exit',60,False),('Hit',30,False),('Hit_Move',30,False),('Death',102,False),('Death_Move',102,False)]
def main():
 lp.export_mesh(arm,obj,str(H/'SK_Snake.fbx'))
 for name,end,loop in ANIMS:
  key=rk.Keyer(arm,'A_Snake_'+name)
  for pb in arm.pose.bones:pb.scale=(1,1,1)
  for f in range(end+1):
   desired=pose(name,0 if loop and f==end else f)
   for b in B:key._key(b.name,desired[b.name],desired[b.parent.name] if b.parent else None,f)
  marks=[('Bite_1',18),('Bite_2',42),('Bite_3',66)] if name=='Attack_Combo' else [('Bite',18)] if name=='Attack_Bite' else [('Settled',90)] if name.startswith('Death') else []
  rk.export_anim(bpy.context.scene,arm,obj.name,str(H/f'A_Snake_{name}.fbx'),end,markers=marks);print('SNAKE V4 CLIP',name,end,flush=True)
 arm.animation_data.action=bpy.data.actions['A_Snake_Coil_Idle'];bpy.context.scene.frame_set(0);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(H/'Snake.blend'))
 assert hashlib.sha256(original_palette.read_bytes()).hexdigest()==original_hash
 report={'status':'PASS','version':4,'bones':len(B),'bone_names':list(B.keys()),'body_segments':N,'segment_lengths_m':L,'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'vertices':len(obj.data.vertices),'shared_palette_unchanged':True,'body_path_length_m':sum(L),'clips':{n:{'frames':e,'seconds':e/30,'loop':q} for n,e,q in ANIMS},'fangs':'curved, hinged, folded in rest pose','combo_bite_frames':[18,42,66],'root_motion':False}
 (H/'build_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('SNAKE V4 BUILD PASS',report,flush=True)
if __name__=='__main__':main()
