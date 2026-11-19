# Run after importing the workshop assets. Places props relative to the existing button workbench.
import unreal,json,math
from pathlib import Path
H=Path(__file__).parent
E=unreal.EditorAssetLibrary;actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors=actors.get_all_level_actors()
benches=[]
for a in all_actors:
 if isinstance(a,unreal.StaticMeshActor):
  m=a.static_mesh_component.static_mesh
  if m and m.get_name()=='SM_Safe_Workbench':benches.append(a)
if len(benches)!=1:raise RuntimeError('Откройте уровень с одним SM_Safe_Workbench; найдено: '+str(len(benches)))
bench=benches[0];specs=json.loads((H/'Workshop_Layout.json').read_text(encoding='utf8'))
assets={s['asset']:E.load_asset('/Game/RiseAboveIt/Arena_Earth/'+s['asset']) for s in specs if s['kind']=='StaticMesh'}
assert all(assets.values()),'Сначала импортируйте три модели мастерской'
existing={a.get_actor_label():a for a in all_actors}
tr=bench.get_actor_transform();yaw=bench.get_actor_rotation().yaw
for s in specs:
 x,y,z=s['position'];location=tr.transform_location(unreal.Vector(x*100,-y*100,z*100))
 rotation=unreal.Rotator(pitch=0,yaw=yaw+s['yaw'],roll=0)
 a=existing.get(s['label'])
 if s['kind']=='StaticMesh':
  if a:
   assert isinstance(a,unreal.StaticMeshActor),'Имя занято другим объектом: '+s['label']
   a.static_mesh_component.set_static_mesh(assets[s['asset']])
  else:a=actors.spawn_actor_from_object(assets[s['asset']],location,rotation)
 else:
  if a:assert isinstance(a,unreal.TargetPoint),'Имя занято другим объектом: '+s['label']
  else:a=actors.spawn_actor_from_class(unreal.TargetPoint,location,rotation)
 a.set_actor_label(s['label']);a.set_actor_location(location,False,False);a.set_actor_rotation(rotation,False)
 a.set_folder_path('Arena_Earth/Workshop')
unreal.log('[Workshop] 3 предмета и 3 точки расставлены. Уровень сохранить вручную. NPC не создавался: SafeZone_Crafter указывает место существующего таракана.')
