
# BPC_MJExitTeleport: when the player pawn comes within Radius of the owner -> fade to black, teleport to the actor tagged TargetTag
# (or OpenLevel(FallbackLevel) if none), fade in. Host actor BP_MJExitTrigger. Placed in L_Town: trigger inside the NYAF doorway, TargetPoint at SFA door.
BPC = '/Game/DirectorsCut/Blueprints/Components/BPC_MJExitTeleport'
HOST = '/Game/DirectorsCut/Blueprints/BP_MJExitTrigger'
PCM = '/Script/Engine.PlayerCameraManager.'
c, g = fresh_component_bp(BPC)
ensure_var(c, g, 'Radius', 'real', 110, True)
ensure_var(c, g, 'TargetTag', 'name', 'MJ_SFA_Entrance', True)
ensure_var(c, g, 'FallbackLevel', 'name', 'L_Town', True)
ensure_var(c, g, 'FadeTime', 'real', 0.6, True)
ensure_var(c, g, 'MJ_State', 'int', 0)
ensure_var(c, g, 'MJ_T', 'real', 0)
g.x, g.y = 400, 300
tk = BEL.add_event_override(c, 'ReceiveTick', unreal.IntPoint(0, 300))
dt = tk.find_output_pin('DeltaSeconds')
own = g.fn('/Script/Engine.ActorComponent.GetOwner')
pawn = g.fn(GPS + 'GetPlayerPawn', PlayerIndex='0')
cam = g.fn(GPS + 'GetPlayerCameraManager', PlayerIndex='0')
# state 0: wait for the pawn
b0 = g.chain(tk.find_then_pin(), g.branch(g.fn(KML + 'EqualEqual_IntInt', A=g.get('MJ_State'), B='0')))
d = g.fn(KML + 'Vector_Distance', V1=g.fn(ACT + 'K2_GetActorLocation', self=g.pin_out(pawn)), V2=g.fn(ACT + 'K2_GetActorLocation', self=g.pin_out(own)))
near = g.fn(KML + 'BooleanAND', A=g.fn(KSL + 'IsValid', Object=pawn), B=g.fn(KML + 'Less_DoubleDouble', A=d, B=g.get('Radius')))
bn = g.chain(g.then(b0), g.branch(near))
f1 = g.chain(g.then(bn), g.fn(PCM + 'StartCameraFade', self=g.pin_out(cam), FromAlpha='0', ToAlpha='1', Duration=g.get('FadeTime'), Color='(R=0,G=0,B=0,A=1)', bHoldWhenFinished='true'))
s1 = g.chain(g.then(f1), g.setv('MJ_T', '0'))
g.chain(g.then(s1), g.setv('MJ_State', '1'))
# state 1: count, then teleport
b1 = g.chain(b0.find_else_pin(), g.branch(g.fn(KML + 'EqualEqual_IntInt', A=g.get('MJ_State'), B='1')))
st = g.chain(g.then(b1), g.setv('MJ_T', g.fn(KML + 'Add_DoubleDouble', A=g.get('MJ_T'), B=dt)))
late = g.fn(KML + 'Greater_DoubleDouble', A=g.get('MJ_T'), B=g.fn(KML + 'Add_DoubleDouble', A=g.get('FadeTime'), B='0.15'))
bt = g.chain(g.then(st), g.branch(late))
fa = g.chain(g.then(bt), g.fn(GPS + 'GetAllActorsWithTag', Tag=g.get('TargetTag')))
arr = g.by_menu(['Utilities|Array|Get (a copy)', 'Utilities|Array|Get'], ['Array', 'Get'])
ins = [str(p.get_pin_name()) for p in arr.list_input_pins()]; outs = [str(p.get_pin_name()) for p in arr.list_output_pins()]
fo = [str(p.get_pin_name()) for p in fa.list_output_pins()]
say('arr pins', ins, outs, 'fa outs', fo)
g.connect(fa.find_output_pin([n for n in fo if 'ctor' in n][0]), arr.find_input_pin([n for n in ins if 'rray' in n][0]), 'arr')
tgt = arr.find_output_pin([n for n in [str(p.get_pin_name()) for p in arr.list_output_pins()]][0])
s2 = g.chain(g.then(fa), g.setv('MJ_State', '2'))
bv = g.chain(g.then(s2), g.branch(g.fn(KSL + 'IsValid', Object=tgt)))
tp = g.chain(g.then(bv), g.fn(ACT + 'K2_TeleportTo', self=g.pin_out(pawn), DestLocation=g.fn(ACT + 'K2_GetActorLocation', self=tgt), DestRotation=g.fn(ACT + 'K2_GetActorRotation', self=tgt)))
ctl = g.fn('/Script/Engine.Pawn.GetController', self=g.pin_out(pawn))
cr = g.chain(g.then(tp), g.fn('/Script/Engine.Controller.SetControlRotation', self=g.pin_out(ctl), NewRotation=g.fn(ACT + 'K2_GetActorRotation', self=tgt)))
g.chain(g.then(cr), g.fn(PCM + 'StartCameraFade', self=g.pin_out(cam), FromAlpha='1', ToAlpha='0', Duration='0.8', Color='(R=0,G=0,B=0,A=1)', bHoldWhenFinished='false'))
g.chain(bv.find_else_pin(), g.fn(GPS + 'OpenLevel', LevelName=g.get('FallbackLevel')))
ok_c = finish(c, BPC)
# host actor
if unreal.EditorAssetLibrary.does_asset_exist(HOST):
    host = unreal.load_asset(HOST)
else:
    host = BEL.create_blueprint_asset_with_parent(HOST, unreal.Actor)
if ok_c:
    ensure_component(host, unreal.load_asset(BPC))
    BEL.compile_blueprint(host); unreal.EditorAssetLibrary.save_loaded_asset(host, only_if_is_dirty=False); say('SAVED', HOST)
# place in L_Town
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if ok_c and 'L_Town' in w.get_path_name():
    acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    o, e = acts['Town_Sidewalk_N'].get_actor_bounds(False); ZS = o.z + e.z
    if 'MJ_SFA_Entrance' not in acts:
        t = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(12720, 7680, ZS + 100), unreal.Rotator(0, 0, 0))
        t.set_actor_label('MJ_SFA_Entrance'); t.tags = [unreal.Name('MJ_SFA_Entrance')]
    if 'MJ_StudioExit_Trigger' not in acts:
        x = eas.spawn_actor_from_class(host.generated_class(), unreal.Vector(4088, -1150, ZS + 90), unreal.Rotator(0, 0, 0))
        x.set_actor_label('MJ_StudioExit_Trigger')
    say('placed; saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
