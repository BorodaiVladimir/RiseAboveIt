# Анимация мобов ключами по FK-дельтам: для каждой кости задаётся смещение и поворот
# в осях арматуры вокруг её головы; дети наследуют движение родителя.
import bpy, math, os
from mathutils import Matrix, Vector, Euler

def rot(pitch=0.0, yaw=0.0, roll=0.0):
    """pitch — вокруг X (плюс опускает нос, нос смотрит в -Y), roll — вокруг Y, yaw — вокруг Z."""
    return Euler((math.radians(pitch), math.radians(roll), math.radians(yaw))).to_matrix().to_4x4()

def about(pivot, R):
    return Matrix.Translation(pivot) @ R @ Matrix.Translation(-pivot)

class Keyer:
    def __init__(self, arm, action_name):
        self.arm = arm
        self.bones = arm.data.bones
        self.rest = {b.name: b.matrix_local.copy() for b in self.bones}
        self.last_q = {}
        arm.animation_data_create()
        old = bpy.data.actions.get(action_name)
        if old:
            bpy.data.actions.remove(old)
        act = bpy.data.actions.new(action_name)
        act.use_fake_user = True
        arm.animation_data.action = act
        for p in arm.pose.bones:
            p.rotation_mode = "QUATERNION"
            p.location, p.rotation_quaternion = (0, 0, 0), (1, 0, 0, 0)

    def _key(self, name, desired, parent_desired, f):
        b = self.bones[name]
        local_rest = (b.parent.matrix_local.inverted() @ b.matrix_local) if b.parent else b.matrix_local
        pd = parent_desired if b.parent else Matrix.Identity(4)
        loc, q, _ = (local_rest.inverted() @ pd.inverted() @ desired).decompose()
        prev = self.last_q.get(name)
        if prev is not None and prev.dot(q) < 0:
            q.negate()                        # держим знак, иначе интерполяция крутит через левую ось
        self.last_q[name] = q.copy()
        p = self.arm.pose.bones[name]
        p.location, p.rotation_quaternion = loc, q
        p.keyframe_insert("location", frame=f)
        p.keyframe_insert("rotation_quaternion", frame=f)

    def pose(self, f, deltas):
        """deltas: {кость: (смещение, (pitch, yaw, roll) или Matrix)} — в осях арматуры, поворот вокруг головы кости."""
        delta = {}
        desired = {}
        for b in self.bones:                  # bones идут от родителей к детям
            parent_delta = delta[b.parent.name] if b.parent else Matrix.Identity(4)
            off, angles = deltas.get(b.name, ((0, 0, 0), (0, 0, 0)))
            head = self.rest[b.name].translation
            R = angles if isinstance(angles, Matrix) else rot(*angles)
            d = parent_delta @ Matrix.Translation(Vector(off)) @ about(head, R)
            delta[b.name] = d
            desired[b.name] = d @ self.rest[b.name]
            self._key(b.name, desired[b.name], desired[b.parent.name] if b.parent else None, f)

def export_anim(scene, arm, mesh_name, path, frame_end, fps=30, markers=()):
    """markers: [(имя, кадр)] — маркеры таймлайна, подсказка для Notify в UE.
    В FBX анимации только скелет, без меша (mesh_name не выгружается, оставлен для совместимости вызовов):
    с мешем UE при ручном импорте без выбранного Skeleton молча заводил на каждый файл свой скелет,
    а без меша он не даст импортировать анимацию, пока скелет не выбран."""
    scene.frame_start, scene.frame_end = 0, frame_end
    scene.render.fps = fps
    scene.timeline_markers.clear()
    for name, f in markers:
        scene.timeline_markers.new(name, frame=f)
    scene.frame_set(0)
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    scene.name = os.path.splitext(os.path.basename(path))[0]   # FBX называет take по сцене
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"ARMATURE"},
        apply_scale_options="FBX_SCALE_ALL", add_leaf_bones=False,
        use_armature_deform_only=True, mesh_smooth_type="FACE",
        bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
    )
