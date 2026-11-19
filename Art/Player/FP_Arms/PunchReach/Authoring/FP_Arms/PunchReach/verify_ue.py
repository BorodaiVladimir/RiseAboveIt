import unreal,json,traceback,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;before=json.loads((H/'before_report.json').read_text());expected=json.loads((H/'pose_report.json').read_text());result={'status':'FAIL'}
try:
 E=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();base='/Game/RiseAboveIt/Player/FP_Arms';sk=E.load_asset(base+'/SK_FP_Arms_Skeleton');assert sk
 unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX False')
 A=unreal.AnimPoseExtensions;opts=unreal.AnimPoseEvaluationOptions();space=unreal.AnimPoseSpaces.WORLD
 nativebones=[n for n,b in before['bones'].items() if b['deform']];checks={}
 pairs=[(b['parent'],n,before['bones'][b['parent']]['length']) for n,b in before['bones'].items() if b['parent'] and n not in ['weapon','clavicle_l','clavicle_r','ik_hand_l','ik_hand_r'] and n in nativebones]
 # Finger bases are intentionally unconnected to the palm; only test connected arm/finger joints.
 pairs=[p for p in pairs if not p[1].startswith(('index_01','middle_01','ring_01','pinky_01','thumb_01'))]
 for name,side,peak,end in [('Jab_L','l',5,18),('Cross_R','r',8,22)]:
  path=base+'/A_FP_Fists_'+name;a=E.load_asset(path);assert a
  flags={k:a.get_editor_property(k) for k in ['enable_root_motion','force_root_lock','rate_scale']}
  if not globals().get('RELOAD_ONLY',False):
   ui=unreal.FbxImportUI()
   for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':unreal.FBXImportType.FBXIT_ANIMATION,'original_import_type':unreal.FBXImportType.FBXIT_ANIMATION,'import_mesh':False,'import_as_skeletal':True,'import_animations':True,'import_materials':False,'import_textures':False,'create_physics_asset':False,'skeleton':sk}.items():ui.set_editor_property(k,v)
   d=ui.get_editor_property('anim_sequence_import_data');d.import_uniform_scale=100;d.convert_scene=True;d.convert_scene_unit=False
   task=unreal.AssetImportTask();task.filename=str(H/f'A_FP_Fists_{name}.fbx');task.destination_path=base;task.options=ui;task.automated=True;task.replace_existing=True;task.save=True;tools.import_asset_tasks([task]);a=E.load_asset(path)
  assert a.get_editor_property('skeleton')==sk
  assert {k:a.get_editor_property(k) for k in flags}==flags,('playback flags',name)
  assert abs(a.get_play_length()-end/30)<.0001
  first=None;hit=None;last=None;root=gap=length=0.
  for f in range(end+1):
   pose=A.get_anim_pose_at_frame(a,f,opts);bones={n:A.get_bone_pose(pose,n,space) for n in nativebones}
   if first is None:first=bones
   if f==peak:hit=bones
   last=bones;root=max(root,bones['root'].translation.length())
   for parent,child,l in pairs:gap=max(gap,abs((bones[child].translation-bones[parent].translation).length()-l*100))
   for s in ['l','r']:
    d=(bones['hand_'+s].translation-bones['upperarm_'+s].translation).length();max_len=(before['bones']['upperarm_'+s]['length']+before['bones']['lowerarm_'+s]['length'])*100;assert d<max_len*.99
  travel=hit['hand_'+side].translation.y-first['hand_'+side].translation.y
  assert abs(travel-expected['clips'][name]['forward_wrist_travel_m']*100)<.01,(name,'travel',travel)
  assert root<.001 and gap<.01,(name,root,gap)
  assert max((first[n].translation-last[n].translation).length() for n in nativebones)<.001
  checks[name]={'frames':end,'impact':peak,'forward_wrist_travel_cm':travel,'max_joint_length_error_cm':gap,'root_translation_cm':root,'skeleton':sk.get_path_name(),'playback_flags':{k:str(v) for k,v in flags.items()}}
 result={'status':'PASS','engine':unreal.SystemLibrary.get_engine_version(),'clips':checks,'canonical_skeleton':sk.get_path_name(),'updated_assets':2}
except Exception:result['error']=traceback.format_exc();unreal.log_error(result['error'])
(H/('ue_reload_report.json' if globals().get('RELOAD_ONLY',False) else 'ue_report.json')).write_text(json.dumps(result,indent=2));print('PUNCH UE CHECK',result);unreal.SystemLibrary.quit_editor()
