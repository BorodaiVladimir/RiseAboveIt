import bpy
from pathlib import Path
from mathutils import Vector
h=Path(r'C:/Users/ROG/Documents/RiseAboveIt/Arena_Earth/SafeZone')
sc=bpy.context.scene;cam=sc.camera;cam.location=(.5,2.65,1.7);cam.rotation_euler=(Vector((-.55,-1.6,1.30))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=30
bpy.ops.file.pack_all();bpy.ops.wm.save_mainfile()
print('PASS packed scene ready at player camera')
