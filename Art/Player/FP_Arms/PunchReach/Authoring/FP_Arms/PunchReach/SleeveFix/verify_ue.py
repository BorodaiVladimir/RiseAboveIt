import unreal,json,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;reload=globals().get('RELOAD_ONLY',False);report={'status':'FAIL'}
try:
 E=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();base='/Game/RiseAboveIt/Player/FP_Arms';mesh=E.load_asset(base+'/SK_FP_Arms');sk=E.load_asset(base+'/SK_FP_Arms_Skeleton');assert mesh and sk
 if not reload:
  previous_materials=[s.get_editor_property('material_interface') for s in mesh.get_editor_property('materials')];physics=mesh.get_editor_property('physics_asset')
  unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX False');ui=unreal.FbxImportUI()
  for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':unreal.FBXImportType.FBXIT_SKELETAL_MESH,'original_import_type':unreal.FBXImportType.FBXIT_SKELETAL_MESH,'import_mesh':True,'import_as_skeletal':True,'import_animations':False,'import_materials':False,'import_textures':False,'create_physics_asset':False,'skeleton':sk}.items():ui.set_editor_property(k,v)
  data=ui.get_editor_property('skeletal_mesh_import_data');data.import_uniform_scale=100;data.convert_scene=True;data.convert_scene_unit=False
  task=unreal.AssetImportTask();task.filename=str(H/'SK_FP_Arms.fbx');task.destination_path=base;task.options=ui;task.automated=True;task.replace_existing=True;task.save=True;tools.import_asset_tasks([task]);mesh=E.load_asset(base+'/SK_FP_Arms')
  slots=list(mesh.get_editor_property('materials'));assert len(slots)==len(previous_materials)
  for slot,mat in zip(slots,previous_materials):slot.set_editor_property('material_interface',mat)
  mesh.set_editor_property('materials',slots);mesh.set_editor_property('physics_asset',physics);assert E.save_loaded_asset(mesh,False)
 assert mesh.get_editor_property('skeleton')==sk
 bounds=mesh.get_bounds();rear=bounds.origin.y-bounds.box_extent.y;assert rear<-60,('sleeves not extended',rear)
 materials=[s.get_editor_property('material_interface').get_path_name() for s in mesh.get_editor_property('materials')]
 physics=mesh.get_editor_property('physics_asset');assert physics
 report={'status':'PASS','mesh':mesh.get_path_name(),'skeleton':sk.get_path_name(),'rear_bound_cm':rear,'materials':materials,'physics_asset':physics.get_path_name()}
 if reload:
  previous=json.loads((H/'ue_mesh_report.json').read_text());assert materials==previous['materials'] and report['physics_asset']==previous['physics_asset']
except Exception:report['error']=traceback.format_exc();unreal.log_error(report['error'])
(H/('ue_mesh_reload_report.json' if reload else 'ue_mesh_report.json')).write_text(json.dumps(report,indent=2));print('SLEEVE UE MESH',report)
if report['status']=='PASS':
 p=H.parent/'verify_ue.py';exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),{'__file__':str(H/'verify_ue.py'),'RELOAD_ONLY':reload})
else:unreal.SystemLibrary.quit_editor()
