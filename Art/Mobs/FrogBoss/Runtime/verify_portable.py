import unreal,json,traceback
from pathlib import Path
out=Path(r'C:/Users/ROG/Documents/RiseAboveIt/FrogBoss/Runtime/portable_reload_test.json')
try:
 base='/Game/RiseAboveIt/Mobs/FrogBoss/'
 bp=unreal.EditorAssetLibrary.load_asset(base+'CR_FrogBoss_ProceduralJump');assert bp
 actor=unreal.EditorAssetLibrary.load_asset(base+'BP_FrogBoss_ProceduralJump');assert actor and actor.generated_class()
 cdo=unreal.get_default_object(actor.generated_class())
 mesh=cdo.get_component_by_class(unreal.SkeletalMeshComponent)
 # Blueprint SCS component templates are checked through their default subobjects.
 sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary
 objects=[lib.get_object_for_blueprint(lib.get_data(k),actor) for k in sub.k2_gather_subobject_data_for_blueprint(actor)]
 objects=list({o.get_path_name():o for o in objects if o}.values())
 meshes=[o for o in objects if isinstance(o,unreal.SkeletalMeshComponent)];components=[o for o in objects if isinstance(o,unreal.ControlRigComponent)]
 assert len(meshes)==1 and len(components)==1,[(str(o),o.get_class().get_name() if o else None) for o in objects]
 assert len(components[0].get_editor_property('user_defined_elements'))==34
 assert meshes[0].get_skeletal_mesh_asset()
 r=bp.create_control_rig();r.request_init();r.set_variable_from_string('JumpAlpha','0.5');r.set_variable_from_string('JumpTarget','(X=0,Y=0,Z=0)');assert r.execute_event('Forwards Solve')
 h=r.get_hierarchy();key=lambda n:unreal.RigElementKey(type=unreal.RigElementType.BONE,name=n)
 hip=h.get_global_transform(key('leg_l_upper')).translation;foot=h.get_global_transform(key('leg_l_foot')).translation
 assert (foot-hip).normal().z<-.995
 assert unreal.EditorAssetLibrary.does_asset_exist(base+'Maps/L_FrogJump_RuntimeTest')
 report={'status':'PASS','project':unreal.Paths.get_project_file_path(),'reloaded_saved_assets':True,'mapped_bones':34,'vertical_leg_direction_z':(foot-hip).normal().z}
except Exception:report={'status':'FAIL','error':traceback.format_exc()}
out.write_text(json.dumps(report,indent=2),encoding='utf8');print('PORTABLE_RELOAD',report)
