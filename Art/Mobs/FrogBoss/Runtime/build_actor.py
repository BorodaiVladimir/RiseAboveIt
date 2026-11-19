import unreal
rigBP=unreal.EditorAssetLibrary.load_asset('/Game/RiseAboveIt/Mobs/FrogBoss/CR_FrogBoss_ProceduralJump')
asset_tools=unreal.AssetToolsHelpers.get_asset_tools();folder='/Game/RiseAboveIt/Mobs/FrogBoss'
ACTOR_BP=unreal.EditorAssetLibrary.load_asset(folder+'/BP_FrogBoss_ProceduralJump')
if not ACTOR_BP:
 factory=unreal.BlueprintFactory();factory.set_editor_property('parent_class',unreal.Actor)
 ACTOR_BP=asset_tools.create_asset('BP_FrogBoss_ProceduralJump',folder,unreal.Blueprint,factory)
SUB=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);LIB=unreal.SubobjectDataBlueprintFunctionLibrary
handles=SUB.k2_gather_subobject_data_for_blueprint(ACTOR_BP);root_handle=handles[0]
objects={}
for handle in handles:
 ob=LIB.get_object_for_blueprint(LIB.get_data(handle),ACTOR_BP)
 if ob:objects[ob.get_name()]=ob

def component(name,cls):
 # Match existing components by class, so rerunning this builder does not duplicate them.
 for ob in objects.values():
  if isinstance(ob,cls):return ob
 handle,reason=SUB.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root_handle,new_class=cls,blueprint_context=ACTOR_BP))
 assert not str(reason),str(reason)
 assert SUB.rename_subobject(handle,unreal.Text(name))
 return LIB.get_object_for_blueprint(LIB.get_data(handle),ACTOR_BP)
MESH_TEMPLATE=component('FrogMesh',unreal.SkeletalMeshComponent)
MESH_TEMPLATE.set_skeletal_mesh_asset(unreal.EditorAssetLibrary.load_asset(folder+'/SK_FrogBoss'))
RIG_TEMPLATE=component('JumpRig',unreal.ControlRigComponent)
RIG_TEMPLATE.set_editor_property('control_rig_class',rigBP.get_control_rig_class())
RIG_TEMPLATE.set_editor_property('reset_transform_before_tick',True)
RIG_TEMPLATE.set_editor_property('update_rig_on_tick',True)
RIG_TEMPLATE.set_editor_property('update_in_editor',True)
RIG_TEMPLATE.set_editor_property('enable_lazy_evaluation',False)
keys=[k for k in rigBP.hierarchy.get_all_keys() if k.type == unreal.RigElementType.BONE]
mapping=[]
for key in keys:
 e=unreal.ControlRigComponentMappedElement()
 e.component_reference=unreal.SoftComponentReference(component_property='FrogMesh')
 e.element_name=key.name;e.element_type=unreal.RigElementType.BONE;e.transform_name=key.name
 e.direction=unreal.ControlRigComponentMapDirection.OUTPUT;e.weight=1.0
 mapping.append(e)
RIG_TEMPLATE.set_editor_property('user_defined_elements',mapping)
unreal.BlueprintEditorLibrary.compile_blueprint(ACTOR_BP)
assert unreal.EditorAssetLibrary.save_loaded_asset(ACTOR_BP,False)
print('BUILT ACTOR',ACTOR_BP.get_path_name(),'mapped bones',len(mapping),'mesh template',MESH_TEMPLATE.get_name())
