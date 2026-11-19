# Blender -b FrogBoss.blend --python anim_frog.py
import bpy, math, os, sys
from mathutils import Vector, Matrix
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(HERE,'..','Shared'))
import rigkit as rk
arm=bpy.data.objects['Armature']; sc=bpy.context.scene
V=Vector; B=arm.data.bones; I=Matrix.Identity(4)
R={b.name:b.matrix_local.copy() for b in B}
RI={n:m.inverted() for n,m in R.items()}
obj=bpy.data.objects['SK_FrogBoss']
# Only torso/face vertices determine the belly's floor contact. Feet solve separately.
body_samples=[]
for v in obj.data.vertices:
    weights=[(obj.vertex_groups[g.group].name,g.weight) for g in v.groups]
    if weights and all(not n.startswith(('arm_','leg_')) for n,w in weights):
        body_samples.append((v.co.copy(),weights))
rest_bottom=min(co.z for co,w in body_samples)

def ease(f,a,b):
    t=max(0.,min(1.,(f-a)/(b-a))); return t*t*(3-2*t)
def bump(f,a,b):
    return math.sin(math.pi*(f-a)/(b-a))**2 if a<f<b else 0.
def closure(f,death):
    if death: return ease(f,4,9)
    return ease(f,27,30)*(1-ease(f,32,36))+ease(f,90,93)*(1-ease(f,95,99))
def fall_amount(f):
    if f<=4: return 0.
    if f<11: return ((f-4)/7)**2
    return 1.
def segment(n,a,c):
    q=(B[n].tail_local-B[n].head_local).normalized().rotation_difference((c-a).normalized())
    return Matrix.Translation(a) @ q.to_matrix().to_4x4() @ R[n].to_quaternion().to_matrix().to_4x4()
def solve(a,c,l1,l2,p):
    u=(c-a).normalized(); d=min(max((c-a).length,abs(l1-l2)+.0001),l1+l2-.0001)
    v=p-a; v=(v-u*v.dot(u)).normalized(); x=(l1*l1-l2*l2+d*d)/(2*d)
    return a+u*x+v*math.sqrt(max(0.,l1*l1-x*x))

def pose(f,death=False):
    drop=fall_amount(f) if death else 0.
    recoil=bump(f,0,5) if death else 0.
    bounce=.18*bump(f,11,19) if death else 0.
    br=math.sin(2*math.pi*f/60)*(1-drop)
    pelvis=Matrix.Translation((0,-.35*drop,-1.1*drop+.10*recoil)) @ rk.about(R['pelvis'].translation,rk.rot(18*drop-3*recoil,0,0))
    chest=pelvis @ rk.about(R['chest'].translation,rk.rot(.45*br-4*drop-4*recoil,0,0))
    head=chest @ rk.about(R['head'].translation,rk.rot(.35*br+4*drop-6*recoil,0,0))
    jaw=head @ rk.about(R['jaw'].translation,rk.rot(14*drop+3*recoil,0,0))
    ds={'root':I,'pelvis':pelvis,'chest':chest,'head':head,'jaw':jaw}; out={'root':R['root']}
    blink=closure(f,death)
    for b in B:
        if b.name=='root': continue
        parent=ds[b.parent.name]; d=ds.get(b.name,parent)
        if b.name.startswith('lid_'):
            side=b.name[-1]; s=1 if side=='l' else -1
            lower='lower' in b.name
            axis=V((0,.8,-.6 if lower else .6)).normalized(); closed=V((0,0,-1 if lower else 1))
            q=axis.rotation_difference(closed)
            q=I.to_quaternion().slerp(q,blink)
            d=parent @ rk.about(R[b.name].translation,q.to_matrix().to_4x4())
        if b.name=='throat': d=parent @ Matrix.Translation((0,-.025*br,-.045*br))
        ds[b.name]=d; out[b.name]=d @ R[b.name]
    if death:
        deform={n:out[n] @ RI[n] for n in out}
        low=min(sum(((deform[n] @ co)*w for n,w in weights),V((0,0,0))).z for co,weights in body_samples)
        target=rest_bottom*(1-drop)+.065*drop+bounce
        lift=Matrix.Translation((0,0,target-low))
        for n in out:
            if n!='root': out[n]=lift @ out[n]
        pelvis=out['pelvis'] @ RI['pelvis']; chest=out['chest'] @ RI['chest']
    for side,s in [('l',1),('r',-1)]:
        for typ in ['arm','leg']:
            upper,lower=f'{typ}_{side}_upper',f'{typ}_{side}_lower'
            parent=chest if typ=='arm' else pelvis
            a=parent @ B[upper].head_local
            shift=V((s*(.95 if typ=='arm' else .7)*drop,-.45*drop,0))
            c=B[lower].tail_local+shift
            if death:
                c=B[lower].tail_local+shift
            pole=B[upper].tail_local + V((s*.8*drop,0,1.8*drop))
            if death:
                raised=V((s*12,(a.y+c.y)*.5,1.0 if typ=='leg' else .55))
                pole=pole.lerp(raised,drop)
            if death: pole+=V((s*.08*bump(f,23,30),0,.08*bump(f,23,30)))
            mid=solve(a,c,B[upper].length,B[lower].length,pole)
            out[upper]=segment(upper,a,mid); out[lower]=segment(lower,mid,c)
            if typ=='arm':
                n=f'arm_{side}_hand'; out[n]=Matrix.Translation(c-B[n].head_local) @ R[n]
            else:
                n,foot=f'leg_{side}_tarsus',f'leg_{side}_foot'; ball=B[n].tail_local+shift
                if death:
                    ball=B[n].tail_local+shift
                    delta=ball-c; length=B[n].length
                    dz=max(.28-c.z,min(length-.001,delta.z))
                    dz=max(-length+.001,min(length-.001,dz))
                    horizontal=V((delta.x,delta.y,0)).normalized()
                    ball=c+horizontal*math.sqrt(length*length-dz*dz)+V((0,0,dz))
                out[n]=segment(n,c,ball); out[foot]=Matrix.Translation(ball-B[foot].head_local) @ R[foot]
    return out

def main():
    ANIMS=[('Idle',120,True,[]),('Death',60,False,[('Death_Start',0),('Impact',11),('Settled',30)])]
    want=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['Idle','Death']
    for name,end,loop,markers in ANIMS:
        if name not in want: continue
        key=rk.Keyer(arm,'A_FrogBoss_'+name)
        for p in arm.pose.bones: p.scale=(1,1,1)
        for f in range(end+1):
            desired=pose(0 if loop and f==end else f,name=='Death')
            for b in B:
                key._key(b.name,desired[b.name],desired[b.parent.name] if b.parent else None,f)
        rk.export_anim(sc,arm,'SK_FrogBoss',os.path.join(HERE,'A_FrogBoss_'+name+'.fbx'),end,markers=markers)
        print('ANIM',name,end)
    arm.animation_data.action=bpy.data.actions['A_FrogBoss_Idle']
    sc.frame_start,sc.frame_end=0,120; sc.frame_set(0)
    bpy.ops.wm.save_mainfile()



if __name__=='__main__': main()
