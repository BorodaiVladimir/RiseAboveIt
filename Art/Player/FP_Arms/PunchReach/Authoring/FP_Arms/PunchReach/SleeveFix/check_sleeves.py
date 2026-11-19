import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view
H=Path(__file__).resolve().parent;meta=json.loads((H/'build_report.json').read_text());arm=bpy.data.objects['Armature'];obj=bpy.data.objects['SK_FP_Arms'];sc=bpy.context.scene
bm=bmesh.new();bm.from_mesh(obj.data);assert all(e.is_manifold and e.is_contiguous for e in bm.edges);bm.free()
for v in obj.data.vertices:assert v.groups and abs(sum(g.weight for g in v.groups)-1)<1e-6
data=bpy.data.cameras.new('ValidationCamera');camera=bpy.data.objects.new('ValidationCamera',data);sc.collection.objects.link(camera);camera.location=(0,0,0);camera.rotation_euler=V((0,-1,-.12)).to_track_quat('-Z','Y').to_euler();data.clip_start=.005;data.sensor_width=36
sc.render.resolution_x=1100;sc.render.resolution_y=760;sc.render.resolution_percentage=100
forward=V((0,-1,-.12)).normalized();report={'status':'PASS','clips':{},'fovs_deg':[90,110]};maximum_depth=-100.;old_visible=0;frames=0
for action in bpy.data.actions:
 if not action.name.startswith('A_FP_'):continue
 arm.animation_data.action=action;count=0;bad=0
 for f in range(int(action.frame_range[0]),int(action.frame_range[1])+1):
  sc.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();eo=obj.evaluated_get(dg);me=eo.to_mesh();frames+=1
  for side,info in meta['arms'].items():
   for index in info['far_cap_vertices']:
    point=eo.matrix_world@me.vertices[index].co;depth=forward.dot(point);maximum_depth=max(maximum_depth,depth);assert depth<-.15,(action.name,f,side,'cap in front',depth)
   for fov in [90,110]:
    data.lens=36/(2*math.tan(math.radians(fov/2)))
    if any((lambda p:p.z>.005 and 0<=p.x<=1 and 0<=p.y<=1)(world_to_camera_view(sc,camera,eo.matrix_world@me.vertices[i].co)) for i in info['old_cap_vertices']):old_visible+=1;count+=1
  eo.to_mesh_clear()
 report['clips'][action.name]={'frames':int(action.frame_range[1]-action.frame_range[0])+1,'old_shoulder_rim_in_view_samples':count,'new_cap_in_view':bad}
assert old_visible>0,'Regression was not reproduced'
report.update(frames_checked=frames,old_visible_samples=old_visible,closest_far_cap_depth_m=maximum_depth,far_cap_always_behind_camera=True)
(H/'visibility_report.json').write_text(json.dumps(report,indent=2));print('SLEEVE VISIBILITY PASS',report)
