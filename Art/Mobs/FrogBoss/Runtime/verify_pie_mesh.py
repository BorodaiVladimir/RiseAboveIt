import unreal,json,math,traceback
from pathlib import Path
OUT=Path(r'C:/Users/ROG/Documents/RiseAboveIt/FrogBoss/Runtime/runtime_mesh_test.json')
WORLD=unreal.EditorLevelLibrary.get_game_world()
assert WORLD,'Start Simulate on L_FrogJump_RuntimeTest first'
PA=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(WORLD,unreal.Actor) if a.get_class().get_name()=='BP_FrogBoss_ProceduralJump_C')
PM=PA.get_component_by_class(unreal.SkeletalMeshComponent);PC=PA.get_component_by_class(unreal.ControlRigComponent);PR=PC.get_control_rig()
KEYS=[k for k in PR.get_hierarchy().get_all_keys() if k.type==unreal.RigElementType.BONE]
CASES=[(g,t) for g in [(0,0,0),(0,1000,0),(800,0,0),(-450,700,0)] for t in [0,.125,.25,.5,.75,.875,1]]
RESULTS=[];STATE={'i':0,'ticks':0,'set':False}
def vector(v):return [v.x,v.y,v.z]
def test_tick(dt):
 try:
  i=STATE['i']
  if i>=len(CASES):
   OUT.write_text(json.dumps({'status':'PASS','mode':'UE5.7 PIE native skeletal mesh ticks','same_actor':PA.get_path_name(),'cases':RESULTS},indent=2),encoding='utf8')
   unreal.unregister_slate_post_tick_callback(TEST_HANDLE);return
  goal,t=CASES[i]
  if not STATE['set']:
   assert PR.set_variable_from_string('JumpTarget','(X=%s,Y=%s,Z=%s)'%goal)
   assert PR.set_variable_from_string('JumpAlpha',str(t))
   STATE['ticks']=0;STATE['set']=True;return
  STATE['ticks']+=1
  if STATE['ticks']<4:return
  h=PR.get_hierarchy();poses={};error=0.;length_error=0.
  for key in KEYS:
   a=PM.get_socket_transform(key.name,unreal.RelativeTransformSpace.RTS_COMPONENT).translation
   b=h.get_global_transform(key).translation
   assert all(math.isfinite(x) for x in vector(a)),str(key.name)
   error=max(error,(a-b).length());poses[str(key.name)]=vector(a)
   parent=h.get_first_parent(key)
   if parent.name!='None' and parent.type==unreal.RigElementType.BONE:
    before=(h.get_global_transform(key,True).translation-h.get_global_transform(parent,True).translation).length()
    after=(b-h.get_global_transform(parent).translation).length()
    length_error=max(length_error,abs(before-after))
  root=unreal.Vector(*poses['root']);expected=unreal.Vector(goal[0]*t,goal[1]*t,goal[2]*t+4*806.8412*t*(1-t))
  assert error<.02,('mesh mapping',error)
  assert (root-expected).length()<.02,('root',root,expected)
  assert length_error<.05,('bone lengths',length_error)
  dot=None
  if t==.5:
   delta=(unreal.Vector(*poses['leg_l_foot'])-unreal.Vector(*poses['leg_l_upper'])).normal()
   dot=delta.dot((-unreal.Vector(goal[0],goal[1],goal[2]+4*806.8412)).normal())
   assert dot>.995,('direction',dot)
  RESULTS.append({'target_cm':goal,'phase':t,'mesh_rig_error_cm':error,'bone_length_error_cm':length_error,'peak_direction_dot':dot,'poses_cm':poses})
  STATE['i']+=1;STATE['set']=False
 except Exception:
  OUT.write_text(json.dumps({'status':'FAIL','error':traceback.format_exc(),'cases':RESULTS},indent=2),encoding='utf8')
  unreal.unregister_slate_post_tick_callback(TEST_HANDLE)
TEST_HANDLE=unreal.register_slate_post_tick_callback(test_tick)
print('STARTED 28 PIE POSE CHECKS')
