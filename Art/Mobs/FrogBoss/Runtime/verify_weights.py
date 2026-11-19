import unreal,json
from pathlib import Path
bp=unreal.EditorAssetLibrary.load_asset('/Game/RiseAboveIt/Mobs/FrogBoss/CR_FrogBoss_ProceduralJump')
r=bp.create_control_rig();r.request_init();h=r.get_hierarchy();keys=[k for k in h.get_all_keys() if k.type==unreal.RigElementType.BONE]
checks=[]
for weight in [0,.5,1]:
 h.reset_pose_to_initial(unreal.RigElementType.BONE)
 r.set_variable_from_string('JumpWeight',str(weight));r.set_variable_from_string('JumpAlpha','0.5');r.set_variable_from_string('JumpTarget','(X=800,Y=300,Z=0)')
 assert r.execute_event('Forwards Solve')
 length_error=0;pose_error=0
 for k in keys:
  a=h.get_global_transform(k);initial=h.get_global_transform(k,True)
  pose_error=max(pose_error,(a.translation-initial.translation).length())
  parent=h.get_first_parent(k)
  if parent.type==unreal.RigElementType.BONE and str(parent.name)!='None':
   length_error=max(length_error,abs((a.translation-h.get_global_transform(parent).translation).length()-(initial.translation-h.get_global_transform(parent,True).translation).length()))
 assert length_error<.05,(weight,length_error)
 if weight==0:assert pose_error<.02,pose_error
 checks.append({'weight':weight,'bone_length_error_cm':length_error,'pose_position_delta_cm':pose_error})
h.reset_pose_to_initial(unreal.RigElementType.BONE)
root=unreal.RigElementKey(type=unreal.RigElementType.BONE,name='root');tr=h.get_global_transform(root);tr.translation=unreal.Vector(123,456,789);h.set_global_transform(root,tr,False,True)
r.set_variable_from_string('DriveRootWeight','0');r.set_variable_from_string('JumpWeight','1');r.execute_event('Forwards Solve')
assert (h.get_global_transform(root).translation-unreal.Vector(123,456,789)).length()<.02
report={'status':'PASS','weights':checks,'external_root_preserved':True}
Path(r'C:/Users/ROG/Documents/RiseAboveIt/FrogBoss/Runtime/runtime_weight_test.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(report)
registry=unreal.AssetRegistryHelpers.get_asset_registry()
opts=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True)
seen=set();todo=['/Game/RiseAboveIt/Mobs/FrogBoss/BP_FrogBoss_ProceduralJump']
while todo:
 p=todo.pop()
 if p in seen:continue
 seen.add(p)
 for d in registry.get_dependencies(p,opts):
  if str(d).startswith('/Game/'):todo.append(str(d))
print('DEPENDENCIES',sorted(seen))
Path(r'C:/Users/ROG/Documents/RiseAboveIt/FrogBoss/Runtime/dependencies.json').write_text(json.dumps(sorted(seen),indent=2),encoding='utf8')
