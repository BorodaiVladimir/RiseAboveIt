import bpy,math
from mathutils import Vector as V
sc=bpy.context.scene
meshes=[bpy.data.objects[n] for n in ['SM_Earth_SafeZone','SM_Safe_Workbench','SM_Safe_WorkSurface','SM_Safe_ToolRack','SM_Safe_PartsShelf']]
route=[(6,5.7),(6,3.7),(3,2.2),(0,2.25)]
clearance=100.
for a,b in zip(route,route[1:]):
 start,end=V((*a,.9)),V((*b,.9));steps=max(2,int((end-start).length/.08))
 for k in range(steps+1):
  p=start.lerp(end,k/steps)
  for o in meshes:
   hit,co,normal,index=o.closest_point_on_mesh(o.matrix_world.inverted() @ p)
   if hit:
    distance=(o.matrix_world @ co-p).length;clearance=min(clearance,distance)
    assert distance>.42,('Player route blocked',o.name,tuple(p),distance)
arm=bpy.data.objects['Armature'];obj=bpy.data.objects['SK_RoachCrafter']
e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh()
zs=[(e.matrix_world @ v.co).z for v in me.vertices];e.to_mesh_clear()
assert min(zs)>-.025 and max(zs)<3.3,('NPC floor/ceiling',min(zs),max(zs))
print('PASS capsule route, minimum solid clearance',round(clearance,3),'m')
print('PASS NPC floor and ceiling',round(min(zs),3),round(max(zs),3))
