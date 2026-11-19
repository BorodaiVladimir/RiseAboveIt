import bpy,sys
from pathlib import Path
H=Path(__file__).resolve().parent;version=sys.argv[sys.argv.index('--')+1]
source=H.parent/'FP_Fists_Reach.blend' if version=='before' else H/'FP_Fists_Reach_Sleeves.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
p=H.parent/'render_compare.py'
code=p.read_text(encoding='utf8').replace('ROOT=H.parent.parent','ROOT=H.parents[2]').replace("action=('Before_'+name if version=='before' and name!='Idle' else 'A_FP_Fists_'+name)","action='A_FP_Fists_'+name")
exec(compile(code,str(p),'exec'),{'__file__':str(H/'render_sleeves.py')})
