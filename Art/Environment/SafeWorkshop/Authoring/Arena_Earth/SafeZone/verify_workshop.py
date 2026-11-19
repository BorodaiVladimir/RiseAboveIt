import bpy,bmesh,math
from pathlib import Path
from mathutils import Vector
H=Path(__file__).parent
for name in ['SM_Safe_WorkSurface','SM_Safe_ToolRack','SM_Safe_PartsShelf']:
 o=bpy.data.objects[name]
 bm=bmesh.new();bm.from_mesh(o.data)
 assert not any(e.is_boundary or not e.is_manifold for e in bm.edges),name+' has open geometry'
 assert all(math.isfinite(t) for v in bm.verts for t in v.co)
 bm.free()
 assert sum(len(f.vertices)-2 for f in o.data.polygons)<15000,name+' too dense'
 assert any(x.name.startswith('UCX_'+name) for x in bpy.data.objects),name+' no collision'
 print('PASS geometry',name)
o=bpy.data.objects['SM_Safe_WorkSurface']
hit,co,normal,face=o.ray_cast(Vector((0,-.9,2)),Vector((0,0,-1)))
assert hit and abs(co.z-1.08)<1e-5,('Work surface mismatch',co)
print('PASS actual assembly surface height',co.z)
