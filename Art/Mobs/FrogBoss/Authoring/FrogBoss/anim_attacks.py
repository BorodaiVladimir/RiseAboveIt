# Blender -b FrogBoss.blend --python anim_attacks.py [-- Attack_Tongue Attack_JumpSlam]
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector as V,Matrix as M
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import anim_frog as base
rk=base.rk;B=base.B;R=base.R;RI=base.RI;arm=base.arm;sc=base.sc;I=M.Identity(4)
ease=base.ease;bump=base.bump
TIMINGS={
 'Attack_Tongue':{'frames':90,'markers':[('Telegraph_Start',0),('Aim_Lock',24),('Damage_Start',29),('Damage_End',33),('Tongue_Retracted',48),('Recovery_End',90)]},
 'Attack_JumpSlam':{'frames':108,'markers':[('Telegraph_Start',0),('Takeoff',27),('Apex',44),('Impact',62),('Recovery_End',108)]}}
# The mesh's tongue rings need translation tracks; Blender's connected flag blocks them.
# Rest positions, hierarchy and all 34 bone names stay unchanged. UE supports these tracks.
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.object.mode_set(mode='EDIT')
for b in arm.data.edit_bones:
 if b.name.startswith('tongue_'):b.use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')

def body_pose(crouch=0.,pitch=0.,head_pitch=0.,jaw_open=0.,surge=0.,height=0.):
 root=M.Translation((0,0,height))
 pelvis=root @ M.Translation((0,surge,-crouch)) @ rk.about(R['pelvis'].translation,rk.rot(pitch,0,0))
 chest=pelvis @ rk.about(R['chest'].translation,rk.rot(pitch*.35,0,0))
 head=chest @ rk.about(R['head'].translation,rk.rot(head_pitch,0,0))
 jaw=head @ rk.about(R['jaw'].translation,rk.rot(jaw_open,0,0))
 ds={'root':root,'pelvis':pelvis,'chest':chest,'head':head,'jaw':jaw};out={}
 for b in B:
  if b.name not in ds:ds[b.name]=ds[b.parent.name] if b.parent else root
  out[b.name]=ds[b.name] @ R[b.name]
 # Keep the skin of the torso above the floor during anticipation and compression.
 deform={n:out[n] @ RI[n] for n in out}
 low=min(sum(((deform[n] @ co)*w for n,w in weights),V()) .z for co,weights in base.body_samples)
 if low<.055:
  lift=M.Translation((0,0,.055-low))
  for n in out:
   if n!='root':out[n]=lift @ out[n]
 return out

def trail_direction(rest,target,t):
 # Turn the webbed feet outward in the horizontal plane when recovering for landing.
 a=math.atan2(rest.x,rest.y)*(1-t)+math.atan2(target.x,target.y)*t
 z=rest.z*(1-t)+target.z*t;horizontal=math.sqrt(max(0.,1-z*z))
 return V((math.sin(a)*horizontal,math.cos(a)*horizontal,z))

def limbs(out,height=0.,tuck=0.,spread=0.,back_lift=None,extension=0.):
 pelvis=out['pelvis'] @ RI['pelvis'];chest=out['chest'] @ RI['chest']
 for side,s in [('l',1),('r',-1)]:
  for typ in ['arm','leg']:
   up,lo=f'{typ}_{side}_upper',f'{typ}_{side}_lower'
   parent=chest if typ=='arm' else pelvis
   a=parent @ B[up].head_local
   foot_height=height if typ=='arm' or back_lift is None else back_lift
   shift=V((s*(.18 if typ=='arm' else -.30)*tuck+s*.18*spread,.38*tuck,foot_height+.70*tuck))
   c=B[lo].tail_local+shift
   extended_dir=V((s*.12,.975,-.185)).normalized() if typ=='leg' else V((s*.10,-.76,-.64)).normalized()
   if extension:
    target=a+extended_dir*(B[up].length+B[lo].length)*.98
    c=c.lerp(target,extension)
   pole=B[up].tail_local+V((s*.35*tuck,0,height+.55*tuck))
   mid=base.solve(a,c,B[up].length,B[lo].length,pole)
   out[up]=base.segment(up,a,mid);out[lo]=base.segment(lo,mid,c)
   if typ=='arm':
    n=f'arm_{side}_hand'
    direction=(B[n].tail_local-B[n].head_local).normalized().lerp(extended_dir,extension).normalized()
    out[n]=base.segment(n,c,c+direction*B[n].length)
   else:
    n,foot=f'leg_{side}_tarsus',f'leg_{side}_foot'
    rest_dir=(B[n].tail_local-B[n].head_local).normalized()
    tar_dir=trail_direction(rest_dir,extended_dir,extension)
    ball=c+tar_dir*B[n].length
    foot_dir=trail_direction((B[foot].tail_local-B[foot].head_local).normalized(),extended_dir,extension)
    out[n]=base.segment(n,c,ball);out[foot]=base.segment(foot,ball,ball+foot_dir*B[foot].length)
 return out

def tongue_pose(f):
 wind=ease(f,0,18)*(1-ease(f,32,66));strike=bump(f,24,44)
 mouth=ease(f,6,24)*(1-ease(f,44,70))
 out=body_pose(.25*wind,-3*wind+3*strike,-5*wind+3*strike,25*mouth,.28*wind-.18*strike)
 limbs(out)
 extension=ease(f,24,30)*(1-ease(f,34,48))
 jaw=out['jaw'] @ RI['jaw']
 start=jaw @ B['tongue_01'].head_local
 target=V((0,-16.25,1.25))
 points=[]
 for i in range(8):
  n=f'tongue_{i+1:02}';rest=jaw @ B[n].head_local;u=(i/7)**1.12
  extended=start.lerp(target,u)+V((0,0,.18*math.sin(math.pi*u)))
  points.append(rest.lerp(extended,extension))
 for i,p in enumerate(points):
  n=f'tongue_{i+1:02}'
  nextp=points[i+1] if i<7 else p+(points[-1]-points[-2]).normalized()*B[n].length
  out[n]=base.segment(n,p,nextp)
 return out

import procedural_jump as jump_solver

def jump_height(f):
 return jump_solver.trajectory(f)[0].z

def jump_pose(f):
 return jump_solver.pose(f,(0,0,0),body_pose)

def jump_forward(f):
 return jump_solver.pose(f,(0,-10,0),body_pose)

def jump_side(f):
 return jump_solver.pose(f,(8,0,0),body_pose)

POSES={'Attack_Tongue':tongue_pose,'Attack_JumpSlam':jump_pose,'Jump_Forward_Demo':jump_forward,'Jump_Side_Demo':jump_side}
for demo in ('Jump_Forward_Demo','Jump_Side_Demo'):TIMINGS[demo]=TIMINGS['Attack_JumpSlam']
def main():
    want=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['Attack_Tongue','Attack_JumpSlam']
    for name in want:
     data=TIMINGS[name];end=data['frames'];key=rk.Keyer(arm,'A_FrogBoss_'+name)
     for b in arm.pose.bones:b.scale=(1,1,1)
     for f in range(end+1):
      desired=POSES[name](f)
      # Exact neutral endpoints for blending into the approved Idle start.
      if name not in ('Jump_Forward_Demo','Jump_Side_Demo') and f in (0,end):desired=base.pose(0)
      for b in B:key._key(b.name,desired[b.name],desired[b.parent.name] if b.parent else None,f)
     dest=H/'ProceduralExports/Demos' if name.endswith('_Demo') else H
     dest.mkdir(parents=True,exist_ok=True)
     rk.export_anim(sc,arm,'SK_FrogBoss',str(dest/('A_FrogBoss_'+name+'.fbx')),end,markers=data['markers'])
     print('EXPORTED',name,end)
    (H/'attack_timings.json').write_text(json.dumps({'fps':30,'attacks':TIMINGS,'tongue_tip_max_y_m':-16.25,'jump_height_m':jump_solver.HEIGHT,'jump_contains_vertical_root_motion':True},indent=2),encoding='utf8')
    arm.animation_data.action=bpy.data.actions['A_FrogBoss_Idle'];sc.frame_set(0)
    bpy.ops.wm.save_mainfile()

if __name__=='__main__':main()
