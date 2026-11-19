# Execute in UE5.7. Builds a native runtime Control Rig; Python is only the authoring tool.
import unreal,math,json
PATH='/Game/RiseAboveIt/Mobs/FrogBoss/CR_FrogBoss_ProceduralJump'
BP=unreal.EditorAssetLibrary.load_asset(PATH)
if not BP:BP=unreal.ControlRigBlueprintFactory.create_new_control_rig_asset(PATH)
BP.set_auto_vm_recompile(False)
HIER=BP.hierarchy
HIER.get_controller().import_bones(unreal.EditorAssetLibrary.load_asset('/Game/RiseAboveIt/Mobs/FrogBoss/SK_FrogBoss_Skeleton'))
BP.set_preview_mesh(unreal.EditorAssetLibrary.load_asset('/Game/RiseAboveIt/Mobs/FrogBoss/SK_FrogBoss'))
C=BP.get_controller()
for node in list(C.get_graph().get_nodes()):C.remove_node(node,False)
for var in list(BP.get_member_variables()):BP.remove_member_variable(var.name)
COUNT=0
def unit(name,struct):
 global COUNT
 COUNT+=1
 path=('/Script/ControlRig.' if struct.startswith('RigUnit_') else '/Script/RigVM.')+struct
 n=C.add_unit_node_from_struct_path(path,'Execute',unreal.Vector2D((COUNT%8)*280,(COUNT//8)*210),name,False)
 assert n,name
 return n.get_name()
def val(pin,value):
 if isinstance(value,bool):value='True' if value else 'False'
 elif isinstance(value,(int,float)):value=str(value)
 assert C.set_pin_default_value(pin,value,True,False),('default',pin,value)
def link(a,b):assert C.add_link(a,b,False),('link',a,b)
def variable(name,typ,default):
 actual=BP.add_member_variable(name,'Vector' if typ=='FVector' else typ,True,False,default)
 assert str(actual)==name,(name,actual)
 obj=unreal.load_object(None,'/Script/CoreUObject.Vector') if typ=='FVector' else None
 n=C.add_variable_node(name,typ,obj,True,default,unreal.Vector2D(-600,COUNT*100),'Input_'+name,False)
 return n.get_name()+'.Value'
def mathnode(name,op,inputs,defaults=None):
 n=unit(name,'RigVMFunction_Math'+op)
 for pin,source in inputs.items():link(source,n+'.'+pin)
 for pin,v in (defaults or {}).items():val(n+'.'+pin,v)
 return n+'.Result'
def vec(v):return '(X=%f,Y=%f,Z=%f)'%(v.x,v.y,v.z)
def getbone(name,initial=False):
 n=unit(('Initial_' if initial else 'Current_')+name,'RigUnit_GetTransform')
 val(n+'.Item','(Type=Bone,Name="'+name+'")');val(n+'.bInitial',initial)
 return n+'.Transform'
def initial(name):return HIER.get_global_transform(unreal.RigElementKey(type=unreal.RigElementType.BONE,name=name),True)
TARGET=variable('JumpTarget','FVector','(X=0,Y=0,Z=0)')
START=variable('JumpStart','FVector','(X=0,Y=0,Z=0)')
ALPHA=variable('JumpAlpha','float','0.0')
HEIGHT=variable('JumpHeight','float','806.8412')
WEIGHT=variable('JumpWeight','float','1.0')
ROOTWEIGHT=variable('DriveRootWeight','float','1.0')
GROUND=variable('GroundHeight','float','0.0')
a=mathnode('ClampPhase','FloatClamp',{'Value':ALPHA},{'Minimum':0.,'Maximum':1.})
inv=mathnode('OneMinusPhase','FloatSub',{'B':a},{'A':1.})
h4=mathnode('FourTimesHeight','FloatMul',{'A':HEIGHT},{'B':4.})
launchZ=mathnode('LaunchUp','VectorScale',{'Factor':h4},{'Value':'(X=0,Y=0,Z=1)'})
launch=mathnode('LaunchVector','VectorAdd',{'A':TARGET,'B':launchZ})
norm=mathnode('LaunchUnit','VectorUnit',{'Value':launch})
anti=mathnode('OppositeLaunch','VectorScale',{'Value':norm},{'Factor':-1.})
parabola=mathnode('Parabola','FloatMul',{'A':a,'B':inv})
z=mathnode('ArcHeight','FloatMul',{'A':parabola,'B':h4})
up=mathnode('VerticalMotion','VectorScale',{'Factor':z},{'Value':'(X=0,Y=0,Z=1)'})
travel=mathnode('TargetTravel','VectorScale',{'Value':TARGET,'Factor':a})
position=mathnode('ArcAndTravel','VectorAdd',{'A':up,'B':travel})
position=mathnode('RootPosition','VectorAdd',{'A':position,'B':START})
rw=mathnode('RootWeight','FloatMul',{'A':WEIGHT,'B':ROOTWEIGHT})
rampup=mathnode('IKRise','FloatMul',{'A':a},{'B':4.})
rampup=mathnode('IKRiseClamp','FloatClamp',{'Value':rampup},{'Minimum':0.,'Maximum':1.})
rampdown=mathnode('IKFall','FloatMul',{'A':inv},{'B':4.})
rampdown=mathnode('IKFallClamp','FloatClamp',{'Value':rampdown},{'Minimum':0.,'Maximum':1.})
ik=mathnode('IKEnvelope','FloatMul',{'A':rampup,'B':rampdown})
weight=mathnode('ClampWeight','FloatClamp',{'Value':WEIGHT},{'Minimum':0.,'Maximum':1.})
begin=unit('ForwardsSolve','RigUnit_BeginExecution')
root=unit('DriveRoot','RigUnit_SetTranslation');val(root+'.Item','(Type=Bone,Name="root")');val(root+'.bPropagateToChildren',True)
link(position,root+'.Value');link(rw,root+'.Weight');link(begin+'.ExecutePin',root+'.ExecutePin');previous=root
CHAINS={}
for side in ('l','r'):
 for typ,parts in [('arm',['upper','lower','hand']),('leg',['upper','lower','tarsus','foot'])]:
  names=[f'{typ}_{side}_{p}' for p in parts];hip_name,foot_name=names[0],names[-1]
  poses=[initial(n) for n in names]
  reach=sum((b.translation-a.translation).length() for a,b in zip(poses,poses[1:]))*.97
  CHAINS[typ+'_'+side]=reach
  hip=getbone(hip_name)
  direction=mathnode('Reach_'+typ+'_'+side,'VectorScale',{'Value':anti},{'Factor':reach})
  airTarget=mathnode('AirTarget_'+typ+'_'+side,'VectorAdd',{'A':hip+'.Translation','B':direction})
  floor=mathnode('Floor_'+typ+'_'+side,'FloatAdd',{'A':GROUND},{'B':poses[-1].translation.z})
  clamp=unit('ClampFloor_'+typ+'_'+side,'RigVMFunction_MathVectorMax')
  link(airTarget,clamp+'.A');val(clamp+'.B','(X=-10000000,Y=-10000000,Z=0)');link(floor,clamp+'.B.Z')
  plant=mathnode('Contact_'+typ+'_'+side,'VectorAdd',{'A':travel,'B':START})
  plant=mathnode('RestContact_'+typ+'_'+side,'VectorAdd',{'A':plant},{'B':vec(poses[-1].translation)})
  endpoint=mathnode('BlendTarget_'+typ+'_'+side,'VectorLerp',{'A':plant,'B':clamp+'.Result','T':ik})
  currentfoot=getbone(foot_name)
  endpoint=mathnode('WeightedTarget_'+typ+'_'+side,'VectorLerp',{'A':currentfoot+'.Translation','B':endpoint,'T':weight})
  make=unit('Effector_'+typ+'_'+side,'RigVMFunction_MathTransformFromSRT')
  link(endpoint,make+'.Location');val(make+'.Rotation',vec(poses[-1].rotation.euler()));val(make+'.Scale',vec(poses[-1].scale3d))
  solver=unit('Solve_'+typ+'_'+side,'RigUnit_FABRIK')
  val(solver+'.StartBone',hip_name);val(solver+'.EffectorBone',foot_name);val(solver+'.MaxIterations',64);val(solver+'.Precision',.001)
  val(solver+'.bPropagateToChildren',True);val(solver+'.bSetEffectorTransform',False)
  link(make+'.Transform',solver+'.EffectorTransform');val(solver+'.Weight',1.)
  link(previous+'.ExecutePin',solver+'.ExecutePin');previous=solver
BP.set_auto_vm_recompile(True);BP.recompile_vm()
unreal.EditorAssetLibrary.save_loaded_asset(BP,False)
print('BUILT RUNTIME RIG',PATH,'nodes',COUNT,'chains',CHAINS)
