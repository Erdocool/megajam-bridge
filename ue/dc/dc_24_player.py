# UNSAFE - DO NOT RUN: Python K2 graph-node creation in BPC_MJPlayerFX crashed UE 5.8 (2026-11-15 ~23:10 TSI). Kept for reference only.
# (send with town bp_helpers prepended)
# BP_MJPlayer = duplicate of BP_FirstPersonCharacter (originals untouched). First person with a visible rigged body:
# CharacterMesh0 (SKM_Manny_Simple + ABP_Unarmed locomotion) now visible to the player, head bone hidden at BeginPlay,
# FP arms mesh hidden (still ticks so the camera keeps its feel). BPC_MJPlayerFX plays a one-shot body animation on E
# (desk -> AnimDesk, door leaf -> AnimDoor, low item -> AnimPick, else AnimReach); game logic for E is NOT changed.
# BP_MJGameMode.DefaultPawnClass -> BP_MJPlayer. Door leaves/BP doors get tag MJ_DoorLeaf (LI level).
EAL = unreal.EditorAssetLibrary
PL = '/Game/DirectorsCut/Blueprints/BP_MJPlayer'; FX = '/Game/DirectorsCut/Blueprints/Components/BPC_MJPlayerFX'
GMP = '/Game/DirectorsCut/Blueprints/BP_MJGameMode'
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
if not EAL.does_asset_exist(PL): EAL.duplicate_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter', PL)
bp = unreal.load_asset(PL)
c, g = fresh_component_bp(FX)
SKC = '/Script/Engine.SkeletalMeshComponent.'
ensure_var(c, g, 'Char', BEL.get_object_reference_type(unreal.Character), '')
ensure_var(c, g, 'bPlaying', 'bool', 'false'); ensure_var(c, g, 'EndT', 'real', 0)
for n in ('Pick', 'Reach', 'Door', 'Desk'):
    ensure_var(c, g, 'Anim' + n, BEL.get_object_reference_type(unreal.AnimSequenceBase), '', True); ensure_var(c, g, 'Len' + n, 'real', 2.0, True)
def link(outs, node):
    for o in outs: g.connect(o, node.find_execute_pin(), 'x')
    return [node.find_then_pin()]
def steps(outs, nodes):
    for n in nodes: outs = link(outs, n)
    return outs
def br(outs, cond):
    b = g.ed.add_branch_node(); g._pos(b); g.y = 600
    g.connect(cond if isinstance(cond, unreal.BlueprintGraphPin) else g.pin_out(cond), b.find_condition_pin(), 'cond')
    link(outs, b); return b
AND = lambda a, b: g.fn(KML + 'BooleanAND', A=a, B=b)
NOT = lambda a: g.fn(KML + 'Not_PreBool', A=a)
CHAR = lambda: g.pin_out(g.get('Char'))
MESH = lambda: g.pin_out(g.get('Mesh', '/Script/Engine.Character', target=CHAR()))
NOW = lambda: g.fn(KSL.replace('KismetSystemLibrary', 'KismetSystemLibrary') + 'GetGameTimeInSeconds')
# BeginPlay
g.x, g.y = 400, 0
ev = BEL.add_event_override(c, 'ReceiveBeginPlay', unreal.IntPoint(0, 0))
cast = owner_cast(g, 'Utilities|Casting|CastToCharacter', 'Char'); g.chain(ev.find_then_pin(), cast)
asc = [p for p in cast.list_output_pins() if 'Character' in str(p.get_pin_name())][0]
s0 = g.chain(g.then(cast), g.setv('Char', asc))
hb = g.chain(g.then(s0), g.fn('/Script/Engine.SkinnedMeshComponent.HideBoneByName', self=MESH(), BoneName='head', PhysBodyOption='PBO_None'))
# Tick
g.x, g.y = 400, 1200
tk = BEL.add_event_override(c, 'ReceiveTick', unreal.IntPoint(0, 1200))
b0 = br([tk.find_then_pin()], g.fn(KSL + 'IsValid', Object=g.get('Char')))
bA = br([b0.find_then_pin()], AND(g.get('bPlaying'), g.fn(KML + 'Greater_DoubleDouble', A=NOW(), B=g.get('EndT'))))
endA = steps([bA.find_then_pin()], [g.fn(SKC + 'SetAnimationMode', self=MESH(), InAnimationMode='AnimationBlueprint'), g.setv('bPlaying', 'false')])
E = g.fn('/Script/Engine.PlayerController.WasInputKeyJustPressed', self=g.fn(GPS + 'GetPlayerController', PlayerIndex='0'), Key='E')
bE = br(endA + [bA.find_else_pin()], AND(E, NOT(g.get('bPlaying'))))
pcm = g.fn(GPS + 'GetPlayerCameraManager', PlayerIndex='0')
cl = g.fn('/Script/Engine.PlayerCameraManager.GetCameraLocation', self=pcm)
fwd = g.fn(KML + 'GetForwardVector', InRot=g.fn('/Script/Engine.PlayerCameraManager.GetCameraRotation', self=g.fn(GPS + 'GetPlayerCameraManager', PlayerIndex='0')))
endv = g.fn(KML + 'Add_VectorVector', A=cl, B=g.fn(KML + 'Multiply_VectorFloat', A=fwd, B='220'))
tr = g.fn(KSL + 'LineTraceSingle', Start=cl, End=endv, TraceChannel='TraceTypeQuery1', bTraceComplex='false', bIgnoreSelf='true')
link([bE.find_then_pin()], tr)
bH = br([tr.find_then_pin()], g.pin_out(tr, 'ReturnValue'))
brk = g.fn(GPS + 'BreakHitResult', Hit=g.pin_out(tr, 'OutHit'))
hitA = g.pin_out(brk, 'HitActor')
def play(outs, n):
    a = g.get('Anim' + n); bv = br(outs, g.fn(KSL + 'IsValid', Object=a))
    return steps([bv.find_then_pin()], [g.fn(SKC + 'PlayAnimation', self=MESH(), NewAnimToPlay=g.get('Anim' + n), bLooping='false'),
                                       g.setv('EndT', g.fn(KML + 'Add_DoubleDouble', A=NOW(), B=g.get('Len' + n))), g.setv('bPlaying', 'true')])
b1 = br([bH.find_then_pin()], g.fn(ACT + 'ActorHasTag', self=hitA, Tag='MJ_EditDesk')); play([b1.find_then_pin()], 'Desk')
b2 = br([b1.find_else_pin()], g.fn(ACT + 'ActorHasTag', self=g.pin_out(brk, 'HitActor'), Tag='MJ_DoorLeaf')); play([b2.find_then_pin()], 'Door')
iz = g.pin_out(g.fn(KML + 'BreakVector', InVec=g.pin_out(brk, 'ImpactPoint')), 'Z')
cz = g.pin_out(g.fn(KML + 'BreakVector', InVec=g.fn(ACT + 'K2_GetActorLocation', self=CHAR())), 'Z')
low = g.fn(KML + 'Less_DoubleDouble', A=g.fn(KML + 'Subtract_DoubleDouble', A=iz, B=cz), B='-41')  # impact < 55 cm above the feet (capsule half 96)
b3 = br([b2.find_else_pin()], low); play([b3.find_then_pin()], 'Pick'); play([b3.find_else_pin()], 'Reach')
ok = finish(c, FX)
say('FX ok', ok)
if ok:
    ensure_component(bp, c)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        o = L.get_object(L.get_data(h))
        if isinstance(o, unreal.SkeletalMeshComponent):
            if o.get_name() == 'CharacterMesh0':
                o.set_editor_property('owner_no_see', False); o.set_editor_property('cast_shadow', True)
            elif 'FirstPersonMesh' in o.get_name():
                o.set_editor_property('visible', False)
                o.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    okp = finish(bp, PL); say('PLAYER ok', okp)
    if okp:
        gm = unreal.load_asset(GMP); unreal.get_default_object(gm.generated_class()).set_editor_property('default_pawn_class', bp.generated_class())
        BEL.compile_blueprint(gm); say('GM saved', EAL.save_loaded_asset(gm, False))
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ'); n = 0
        for a in eas.get_all_level_actors():
            if a.get_class().get_name().startswith('BP_Door'):
                for t in [a, a.get_editor_property('MJ_Proxy')]:
                    if t and unreal.Name('MJ_DoorLeaf') not in t.tags: t.tags = list(t.tags) + [unreal.Name('MJ_DoorLeaf')]; n += 1
        say('DOORTAG', n, 'saved', les.save_current_level()); les.load_level('/Game/DirectorsCut/Maps/L_Town')
