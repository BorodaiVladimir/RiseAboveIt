from pathlib import Path
import csv, math
p=Path(__file__).resolve().parents[1]/'Export/ArenaEarth_Layout.csv'
rows=list(csv.DictReader(p.open(encoding='utf8'))); by={r['Label']:r for r in rows}
required={'SafeZone_Crafter','SafeZone_Assembly','SafeZone_WorkSurface','SafeZone_ToolRack','SafeZone_PartsShelf','SafeZone_PlayerApproach'}
assert required<=by.keys(), 'Missing workshop placement: '+str(required-by.keys())
assert len(rows)==len(by),'Duplicate placement labels'
b=by['SafeZone_Workbench']; n=by['SafeZone_Crafter']; a=by['SafeZone_Assembly']
assert abs(float(n['Z'])-float(b['Z']))<.01,'NPC feet must stand on floor'
assert abs(float(a['Z'])-float(b['Z'])-108)<.01,'Assembly surface must match Work animation height'
assert 190<math.hypot(float(n['X'])-float(b['X']),float(n['Y'])-float(b['Y']))<210,'NPC must stand behind button rim'
print('PASS workshop placement, floor, working height, unique labels')
