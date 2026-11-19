# Blender -b FrogBoss.blend --python bake_jump_target.py -- X Y Z ClipName
import bpy,sys,re
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import anim_attacks as attacks
import procedural_jump as solver
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['0','0','0','Jump_Custom']
goal=tuple(float(x) for x in args[:3]);name=args[3] if len(args)>3 else 'Jump_Custom'
assert len(goal)==3 and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',name),'Use XYZ in metres and a simple clip name'
arm=attacks.arm;B=attacks.B;key=attacks.rk.Keyer(arm,'A_FrogBoss_'+name)
for b in arm.pose.bones:b.scale=(1,1,1)
for f in range(109):
 desired=solver.pose(f,goal,attacks.body_pose)
 for b in B:key._key(b.name,desired[b.name],desired[b.parent.name] if b.parent else None,f)
out=H/'ProceduralExports';out.mkdir(exist_ok=True)
attacks.rk.export_anim(attacks.sc,arm,'SK_FrogBoss',str(out/('A_FrogBoss_'+name+'.fbx')),108,markers=attacks.TIMINGS['Attack_JumpSlam']['markers'])
attacks.sc.frame_set(108)
from mathutils import Vector
assert (arm.pose.bones['root'].matrix.translation-Vector(goal)).length<1e-4
print('PASS custom landing goal',goal,'output',out/('A_FrogBoss_'+name+'.fbx'))
