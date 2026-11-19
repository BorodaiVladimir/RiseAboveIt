# Target-driven ballistic trajectory and per-frame leg IK. Blender prototype, not a UE runtime rig.
import math
from mathutils import Vector as V,Matrix as M
import anim_frog as base
B=base.B;R=base.R;RI=base.RI
TAKEOFF=27;IMPACT=62;FPS=30
HIND_REACH=sum(B['leg_l_'+p].length for p in ('upper','lower','tarsus'))
# Enough clearance for the existing long hind legs to extend downward without changing bone lengths.
HEIGHT=max(4.5,.97*HIND_REACH+B['leg_l_foot'].head_local.z-B['leg_l_upper'].head_local.z+.35)

def ease(f,a,b):
 t=max(0.,min(1.,(f-a)/(b-a)));return t*t*(3-2*t)
def bump(f,a,b):return math.sin(math.pi*(f-a)/(b-a))**2 if a<f<b else 0.
def trajectory(f,goal=(0,0,0)):
 g=V(goal);t=max(0.,min(1.,(f-TAKEOFF)/(IMPACT-TAKEOFF)))
 p=g*t;p.z+=4*HEIGHT*t*(1-t)
 duration=(IMPACT-TAKEOFF)/FPS
 velocity=V((g.x/duration,g.y/duration,(g.z+4*HEIGHT)/duration))
 return p,-velocity.normalized()

def constrained_point(anchor,candidate,length,minimum_z):
 if minimum_z is None or candidate.z>=minimum_z:return candidate
 dz=max(-length+1e-6,min(length-1e-6,minimum_z-anchor.z))
 horizontal=V((candidate.x-anchor.x,candidate.y-anchor.y,0))
 if horizontal.length<1e-8:horizontal=V((1,0,0))
 return anchor+horizontal.normalized()*math.sqrt(max(0.,length*length-dz*dz))+V((0,0,dz))

def fabrik(root,target,lengths,seed,limits):
 points=[V(p) for p in seed];points[0]=root.copy()
 if (target-root).length>=sum(lengths)-1e-5:
  d=(target-root).normalized()
  for i,l in enumerate(lengths):points[i+1]=points[i]+d*l
  return points
 for _ in range(160):
  points[-1]=target.copy()
  for i in range(len(lengths)-1,-1,-1):
   delta=points[i]-points[i+1]
   if delta.length<1e-8:delta=V((.01,0,1))
   points[i]=constrained_point(points[i+1],points[i+1]+delta.normalized()*lengths[i],lengths[i],limits[i])
  points[0]=root.copy()
  for i,l in enumerate(lengths):
   delta=points[i+1]-points[i]
   if delta.length<1e-8:delta=V((.01,0,-1))
   points[i+1]=constrained_point(points[i],points[i]+delta.normalized()*l,l,limits[i+1])
  if (points[-1]-target).length<1e-6:break
 return points

def pose(f,goal,body_pose):
 goal=V(goal);move,push_dir=trajectory(f,goal)
 wind=ease(f,0,21)*(1-ease(f,27,36));squash=ease(f,59,62)*(1-ease(f,66,102))
 air=ease(f,29,37)*(1-ease(f,50,61))
 out=body_pose(.60*wind+.63*squash,3*wind+5*squash-3*bump(f,27,49),2*wind-3*air,0.,.10*wind,move.z)
 horizontal=M.Translation((move.x,move.y,0))
 out={n:horizontal @ mat for n,mat in out.items()}
 extension=ease(f,27,37)*(1-ease(f,50,62))
 landing=ease(f,35,62)
 floor=max(0.,goal.z*landing)
 for side,s in [('l',1),('r',-1)]:
  for typ,parts in [('arm',['upper','lower']),('leg',['upper','lower','tarsus'])]:
   names=[f'{typ}_{side}_{p}' for p in parts]
   foot=f'{typ}_{side}_'+('hand' if typ=='arm' else 'foot')
   parent=out['chest' if typ=='arm' else 'pelvis'] @ RI['chest' if typ=='arm' else 'pelvis']
   hip=parent @ B[names[0]].head_local
   lengths=[B[n].length for n in names];reach=sum(lengths)
   plant=B[foot].head_local+goal*landing
   air_target=hip+push_dir*(reach*.97)
   air_target.z=max(floor+B[foot].head_local.z+.035,air_target.z)
   target=plant.lerp(air_target,extension)
   target.z=max(floor+B[foot].head_local.z,target.z)
   # Keep the target within the limb reach while retaining direction and fixed segment lengths.
   delta=target-hip
   if delta.length>reach*.995:target=hip+delta.normalized()*reach*.995
   seed=[hip]+[parent @ B[n].tail_local for n in names]
   limits=[None,floor+.90,floor+.45,floor+B[foot].head_local.z] if typ=='leg' else [None,floor+.6,floor+B[foot].head_local.z]
   points=fabrik(hip,target,lengths,seed,limits)
   for i,n in enumerate(names):out[n]=base.segment(n,points[i],points[i+1])
   out[foot]=M.Translation(points[-1]-B[foot].head_local) @ R[foot]
 if f==0:return base.pose(0)
 if f==108:return {n:M.Translation(goal) @ mat for n,mat in base.pose(0).items()}
 return out
