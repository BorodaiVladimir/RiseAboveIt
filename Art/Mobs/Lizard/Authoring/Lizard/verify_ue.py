import unreal,json,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;meta=json.loads((H/'build_report.json').read_text());result={'status':'FAIL'}
try:
    E=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();base='/Game/RiseAboveIt/Mobs/Lizard'
    unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX False')
    def load(path,sk=None):
        if globals().get('RELOAD_ONLY',False):
            asset=E.load_asset(base+'/'+path.stem);assert asset,path.name;return asset
        anim=path.name.startswith('A_');typ=unreal.FBXImportType.FBXIT_ANIMATION if anim else unreal.FBXImportType.FBXIT_SKELETAL_MESH
        ui=unreal.FbxImportUI()
        for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':typ,'original_import_type':typ,'import_mesh':not anim,'import_as_skeletal':True,'import_animations':anim,'import_materials':False,'import_textures':False,'create_physics_asset':False}.items():ui.set_editor_property(k,v)
        if sk:ui.set_editor_property('skeleton',sk)
        for name in ['skeletal_mesh_import_data','anim_sequence_import_data']:
            d=ui.get_editor_property(name);d.import_uniform_scale=100;d.convert_scene_unit=False;d.convert_scene=True
        t=unreal.AssetImportTask();t.filename=str(path);t.destination_path=base;t.options=ui;t.automated=True;t.replace_existing=True;t.save=True
        tools.import_asset_tasks([t]);a=E.load_asset(base+'/'+path.stem);assert a,path.name;return a
    mesh=load(H/'SK_Lizard.fbx');sk=mesh.get_editor_property('skeleton');assert sk
    if not globals().get('RELOAD_ONLY',False):
        t=unreal.AssetImportTask();t.filename=str(H/'T_Palette_Lizard.png');t.destination_path=base;t.automated=True;t.replace_existing=True;t.save=True
        tools.import_asset_tasks([t])
    texture=E.load_asset(base+'/T_Palette_Lizard');assert texture
    texture.filter=unreal.TextureFilter.TF_NEAREST
    mat=E.load_asset(base+'/M_Lizard')
    if not globals().get('RELOAD_ONLY',False):
        mat=mat or tools.create_asset('M_Lizard',base,unreal.Material,unreal.MaterialFactoryNew())
        mel=unreal.MaterialEditingLibrary;mel.delete_all_material_expressions(mat)
        node=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample);node.texture=texture
        mel.connect_material_property(node,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
        rough=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);rough.r=.78
        mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS);mel.recompile_material(mat)
        assert E.save_loaded_asset(mat,False) and E.save_loaded_asset(texture,False)
    assert mat
    slots=list(mesh.get_editor_property('materials'))
    for slot in slots:slot.set_editor_property('material_interface',mat)
    mesh.set_editor_property('materials',slots);assert E.save_loaded_asset(mesh,False);assert E.save_loaded_asset(sk,False)
    pairs=json.loads((H/'pose_report.json').read_text())['connected_pairs'];A=unreal.AnimPoseExtensions;options=unreal.AnimPoseEvaluationOptions();space=unreal.AnimPoseSpaces.WORLD
    poses={};clips={};eyes={};results={}
    for name,info in meta['clips'].items():
        a=load(H/f'A_Lizard_{name}.fbx',sk);assert a.get_editor_property('skeleton')==sk
        assert abs(a.get_play_length()-info['seconds'])<.01
        first=None;last=None;contacts={};gap=root=eye_error=drift=head_motion=0.
        for f in range(info['frames']+1):
            pose=A.get_anim_pose_at_frame(a,f,options);bones={n:A.get_bone_pose(pose,n,space) for n in meta['bone_names']}
            if first is None:first=bones
            last=bones;root=max(root,bones['root'].translation.length());head_motion=max(head_motion,(bones['head'].translation-first['head'].translation).length())
            for parent,child,length in pairs:gap=max(gap,abs((bones[parent].translation-bones[child].translation).length()-length*100))
            for side in ['l','r']:
                distance=(bones['eye_'+side].translation-bones['head'].translation).length()
                if side not in eyes:eyes[side]=distance
                eye_error=max(eye_error,abs(distance-eyes[side]))
            if name=='Move':
                support=0
                for key,phase in {'front_l':0,'hind_r':.25,'front_r':.5,'hind_l':.75}.items():
                    p=(f/72+phase)%1;point=bones[key+'_foot'].translation+unreal.Vector(0,meta['reference_speed_m_s']*100*f/30,0)
                    if p<=.75+1e-8:
                        support+=1
                        if key in contacts:drift=max(drift,(point-contacts[key]).length())
                        else:contacts[key]=point
                    else:contacts.pop(key,None)
                assert support>=3
        assert gap<.01 and root<.001 and eye_error<.01 and drift<.01,(name,gap,root,eye_error,drift)
        if info['loop']:assert max((first[n].translation-last[n].translation).length() for n in first)<.001
        if name=='Attack_Bite':assert head_motion>35,head_motion
        if name=='Hit':assert head_motion>10,head_motion
        poses[name]=(first,last);clips[name]=a.get_play_length();results[name]={'joint_length_error_cm':gap,'root_translation_cm':root,'eye_attachment_error_cm':eye_error,'planted_foot_drift_cm':drift,'head_motion_cm':head_motion}
    idle=poses['Idle'][0]
    for name in ['Attack_Bite','Hit','Death']:assert max((poses[name][0][n].translation-idle[n].translation).length() for n in idle)<.001
    for name in ['Attack_Bite','Hit']:assert max((poses[name][1][n].translation-idle[n].translation).length() for n in idle)<.001
    assert E.save_loaded_asset(sk,False)
    result={'status':'PASS','engine':unreal.SystemLibrary.get_engine_version(),'mesh':mesh.get_path_name(),'skeleton':sk.get_path_name(),'clips':clips,'pose_checks':results,'material':mat.get_path_name()}
except Exception:result['error']=traceback.format_exc();unreal.log_error(result['error'])
(H/('ue_reload_report.json' if globals().get('RELOAD_ONLY',False) else 'ue_report.json')).write_text(json.dumps(result,indent=2));print('LIZARD UE CHECK',result)
unreal.SystemLibrary.quit_editor()
