import csv, math
from pathlib import Path
SPECS=[
 ('SafeZone_WorkSurface','StaticMesh','SM_Safe_WorkSurface',(0,0,0),0,'Подкладка для сборки, верх 108 см над полом'),
 ('SafeZone_ToolRack','StaticMesh','SM_Safe_ToolRack',(0,-3.25,1.05),180,'Инструменты на задней стенке'),
 ('SafeZone_PartsShelf','StaticMesh','SM_Safe_PartsShelf',(-2.65,-1.4,0),0,'Материалы для крафта; декоративные ёмкости'),
 ('SafeZone_Crafter','TargetPoint','',(0,-2,0),-90,'Точка NPC: Actor yaw; меш +Y повернуть на -90 градусов'),
 ('SafeZone_Assembly','TargetPoint','',(0,-.90,1.08),0,'Поверхность сборки; игровую анимацию запускает Blueprint'),
 ('SafeZone_PlayerApproach','TargetPoint','',(0,2.25,0),90,'Подход к мастеру, свободная площадка для игрока')]
def augment(rows):
 labels={x[0] for x in SPECS}
 result=[r for r in rows if r['Label'] not in labels]
 b=next(r for r in result if r['Label']=='SafeZone_Workbench')
 x,y,z=[float(b[a]) for a in ('X','Y','Z')];yaw=float(b['Yaw']);c=math.cos(math.radians(yaw));s=math.sin(math.radians(yaw))
 for label,kind,asset,(dx,dy,dz),angle,note in SPECS:
  result.append(dict(Label=label,Kind=kind,Asset=asset,X=round(x+100*(dx*c+dy*s),2),Y=round(y+100*(dx*s-dy*c),2),Z=round(z+100*dz,2),Yaw=round(yaw+angle,2),Note=note))
 return result
if __name__=='__main__':
 p=Path(__file__).resolve().parents[1]/'Export/ArenaEarth_Layout.csv'
 rows=list(csv.DictReader(p.open(encoding='utf8')))
 with p.open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(augment(rows))
 print('Workshop placement updated')
