"""Extend the proximal sleeve rims behind the FP camera; preserve the rig."""
import bpy,bmesh,sys,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector as V
H=Path(__file__).resolve().parent;SOURCE=H.parent/'FP_Fists_Reach.blend';ROOT=H.parents[2]
sys.path[:0]=[str(ROOT/'Shared')];import lowpoly as lp
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));obj=bpy.data.objects['SK_FP_Arms'];arm=bpy.data.objects['Armature']
hash_before=hashlib.sha256(SOURCE.read_bytes()).hexdigest();rest={b.name:[x for row in b.matrix_local for x in row] for b in arm.data.bones}
source_vertices=[v.co.copy() for v in obj.data.vertices]
if 'root' not in obj.vertex_groups:obj.vertex_groups.new(name='root')
bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();weights=bm.verts.layers.deform.verify();uv=bm.loops.layers.uv.active
report={'status':'PASS','source_blend_sha256':hash_before,'arms':{},'rest_skeleton_unchanged':True,'original_vertices_unchanged':True}
for side,s in [('l',1),('r',-1)]:
 group=obj.vertex_groups['upperarm_'+side].index
 candidates=[f for f in bm.faces if len(f.verts)==8 and all(v[weights].get(group,0)>.99 for v in f.verts)]
 # The shoulder end of the authored three-ring sleeve is its most proximal cap.
 shoulder=arm.data.bones['upperarm_'+side].head_local
 cap=min(candidates,key=lambda f:(f.calc_center_median()-shoulder).length)
 ring=list(cap.verts);center=cap.calc_center_median();tex=sum((loop[uv].uv for loop in cap.loops),V((0,0)))/len(cap.loops)
 material=cap.material_index;old_ids=[v.index for v in ring];offsets=[v.co-center for v in ring]
 # Cap winding faces the body; extrusion along that winding closes consistently.
 bm.faces.remove(cap);previous=ring;new_rings=[]
 for t in [.25,.55,1.]:
  anchor=V((s*.30,.65,-.32));c=center.lerp(anchor,t);scale=1+.8*t
  current=[bm.verts.new(c+delta*scale) for delta in offsets]
  for v in current:v[weights][group]=1-t;v[weights][obj.vertex_groups['root'].index]=t
  for i in range(8):
   f=bm.faces.new((previous[i],previous[(i+1)%8],current[(i+1)%8],current[i]));f.material_index=material;f.smooth=True
   for loop in f.loops:loop[uv].uv=tex
  previous=current;new_rings.append(current)
 f=bm.faces.new(previous);f.material_index=material;f.smooth=True
 for loop in f.loops:loop[uv].uv=tex
 bm.verts.index_update();report['arms'][side]={'old_cap_vertices':old_ids,'far_cap_vertices':[v.index for v in previous],'new_vertices':[v.index for row in new_rings for v in row],'anchor_m':list(anchor)}
bm.normal_update();assert all(e.is_manifold and e.is_contiguous for e in bm.edges)
bm.to_mesh(obj.data);bm.free();obj.data.update()
assert all((obj.data.vertices[i].co-v).length<1e-8 for i,v in enumerate(source_vertices))
assert rest=={b.name:[x for row in b.matrix_local for x in row] for b in arm.data.bones}
arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update();lp.export_mesh(arm,obj,str(H/'SK_FP_Arms.fbx'))
arm.animation_data.action=bpy.data.actions['A_FP_Fists_Idle'];bpy.context.scene.frame_set(0);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(H/'FP_Fists_Reach_Sleeves.blend'))
for name in ['Jab_L','Cross_R']:shutil.copy2(H.parent/f'A_FP_Fists_{name}.fbx',H/f'A_FP_Fists_{name}.fbx')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==hash_before
report.update(vertices=len(obj.data.vertices),triangles=sum(len(p.vertices)-2 for p in obj.data.polygons),added_vertices=len(obj.data.vertices)-len(source_vertices),source_unchanged=True)
(H/'build_report.json').write_text(json.dumps(report,indent=2));print('SLEEVE BUILD PASS',report)
