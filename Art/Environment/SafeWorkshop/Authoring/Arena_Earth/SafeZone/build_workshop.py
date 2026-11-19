# Blender --background --factory-startup --python build_workshop.py
import bpy,bmesh,sys,math,os
from pathlib import Path
from mathutils import Vector as V
H=Path(__file__).resolve().parent;ROOT=H.parents[1];OUT=H.parent/'Export'
sys.path.insert(0,str(ROOT/'Shared'));sys.path.insert(0,str(ROOT/'Weapons'))
import lowpoly as lp
import weapon_kit as wk
lp.clear_scene();mat=lp.palette_material('M_Palette');OUT.mkdir(exist_ok=True)

def box(mb,c,size,sw):
 x,y,z=c;wx,wy,wz=size
 mb.box((x-wx/2,y,z),(1,0,0),(0,1,0),wx,wy/2,wz/2,sw=sw,bone='root',bevel=min(.015,wy/8,wz/8))
def collision(owner,c,size,i):
 x,y,z=c;dx,dy,dz=[t/2 for t in size]
 vs=[(x+a*dx,y+b*dy,z+d*dz) for a in (-1,1) for b in (-1,1) for d in (-1,1)]
 bm=bmesh.new();verts=[bm.verts.new(p) for p in vs];bmesh.ops.convex_hull(bm,input=verts)
 me=bpy.data.meshes.new(f'UCX_{owner}_{i:02}');bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(ob);return ob

def export(mb,name,colliders):
 obj=mb.finish(name,[mat],uv_mode='flat',smooth_angle=40)
 cols=[collision(name,*c,i) for i,c in enumerate(colliders)]
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
 for c in cols:c.select_set(True)
 bpy.context.view_layer.objects.active=obj
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_scale_options='FBX_SCALE_ALL',bake_anim=False,mesh_smooth_type='FACE',path_mode='COPY',embed_textures=True)
 for c in cols:c.hide_render=True;c.hide_viewport=True
 print('WORKSHOP',name,'tris',sum(len(f.vertices)-2 for f in obj.data.polygons))
 return obj

# Thin, taped wooden pad leaves the blue button rim visible.
mb=lp.MeshBuilder(seed=31)
for i in range(3):
 x=(i-1)*.60
 box(mb,(x,-.76,1.005),(.585,1.12,.09),'wood_dry')
 # Thin side rails lift the working area to the 1.08m animation datum.
box(mb,(0,-.76,1.065),(1.84,1.14,.03),'coat_dirty')
for x in (-.79,.79):
 box(mb,(x,-.76,1.084),(.11,1.19,.008),'tape')
 for y in (-1.21,-.31):
  mb.ellipsoid((x,y,1.094),(.022,.022,.006),8,4,'steel','root')
# A small clamp at one edge, outside the hand contact zone.
box(mb,(.79,-.42,1.16),(.13,.22,.14),'steel')
mb.tube([(.79,-.42,1.16),(.79,-.42,1.34)],[.018,.018],8,'brass','root')
mb.tube([(.70,-.42,1.31),(.88,-.42,1.31)],[.016,.016],6,'steel','root')
export(mb,'SM_Safe_WorkSurface',[((0,-.76,1.02),(1.84,1.16,.12))])

# Wall-mounted tool board: matchwood slats, copper bindings, salvaged tools.
mb=lp.MeshBuilder(seed=32)
for i in range(5):
 box(mb,((i-2)*.48,.02,.66),(.455,.10,1.32),'wood_dry' if i%2 else 'wood')
for z in (.12,1.20):
 box(mb,(0,.10,z),(2.48,.13,.10),'palps')
for x in (-1.07,1.07):
 for z in (.13,1.17):mb.ellipsoid((x,-.046,z),(.035,.018,.035),8,5,'copper','root')
# Needle screwdriver, wire pliers and a salvaged razor.
mb.tube([(-.82,-.10,.36),(-.82,-.10,.75)],[.055,.055],8,'cap_red','root')
mb.tube([(-.82,-.10,.75),(-.82,-.10,1.10)],[.018,.010],6,'steel','root')
for s in (-1,1):
 mb.tube([(-.38+s*.075,-.11,.27),(-.38+s*.025,-.11,.58),(-.38-s*.055,-.11,.84)],[.031,.025,.017],6,'steel','root')
 mb.tube([(-.38+s*.075,-.11,.27),(-.38+s*.048,-.11,.46)],[.042,.038],6,'tape','root')
mb.ellipsoid((-.38,-.14,.59),(.045,.025,.045),8,5,'brass','root')
box(mb,(.12,-.12,.70),(.28,.025,.35),'steel')
box(mb,(.12,-.14,.68),(.12,.012,.045),'eye_black')
# A coil of wire and a gear show the same materials as crafting loot.
wk.gear(mb,V((.63,-.12,.83)),(0,-1,0),.19,14,.014,'brass','root',up=(1,0,0),spokes=4)
for i in range(4):
 pts=[(.61+.21*math.cos(t),-.105-i*.012,.38+.21*math.sin(t)) for t in [j*math.tau/24 for j in range(25)]]
 mb.tube(pts,[.012]*len(pts),5,'copper','root')
for x,z in [(-.82,1.12),(-.38,.92),(.12,.94),(.63,1.07)]:
 mb.tube([(x,-.04,z),(x,-.17,z)],[.018,.018],5,'steel','root')
export(mb,'SM_Safe_ToolRack',[((0,.04,.66),(2.5,.15,1.34))])

# Low storage shelf: sorting trays instead of a trading counter.
mb=lp.MeshBuilder(seed=33)
for x in (-.72,.72):
 for y in (-.28,.28):box(mb,(x,y,.69),(.12,.12,1.38),'wood_dry')
for z in (.18,.73,1.28):
 box(mb,(0,0,z),(1.60,.75,.09),'wood')
 for x in (-.48,0,.48):
  box(mb,(x,-.02,z+.075),(.42,.55,.045),'trash_metal')
  for yy in (-.30,.25):box(mb,(x,yy,z+.16),(.43,.035,.18),'palps')
  for xx in (x-.21,x+.21):box(mb,(xx,-.025,z+.16),(.035,.55,.18),'palps')
  # Sorted components, no cash or price labels.
  if z<.3:
   for j in range(3):
    mb.ellipsoid((x-.10+j*.09,-.03,z+.14),(.043,.043,.043),8,5,'steel','root')
  elif x<-.2:
   wk.gear(mb,V((x,0,z+.115)),(0,0,1),.15,12,.012,'brass','root',up=(1,0,0),spokes=4)
  elif x>.2:
   mb.tube([(x-.12,0,z+.14),(x+.12,0,z+.14)],[.075,.075],10,'bandage','root')
  else:
   for j in range(3):
    pts=[(x+.13*math.cos(t),.13*math.sin(t),z+.13+j*.018) for t in [i*math.tau/16 for i in range(17)]]
    mb.tube(pts,[.013]*len(pts),5,'copper','root')
export(mb,'SM_Safe_PartsShelf',[((0,0,.72),(1.6,.76,1.46))])
bpy.ops.wm.save_as_mainfile(filepath=str(H/'Workshop_Props.blend'))
