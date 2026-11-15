
# capture candidate buildings to C:/MegaJam/shots/cand/*.jpg (L_Town only, adds catalog ground + capture actor)
import os, math
W, H = WH
OUT = 'C:/MegaJam/shots/cand'
os.makedirs(OUT, exist_ok=True)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in world.get_path_name(), world.get_path_name()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
if 'CAT_Ground' not in acts:
    cube = unreal.load_asset('/Engine/BasicShapes/Cube')
    g = eas.spawn_actor_from_object(cube, unreal.Vector(80000, -40000, -12), unreal.Rotator(0, 0, 0))
    g.set_actor_label('CAT_Ground')
    g.set_actor_scale3d(unreal.Vector(2200, 900, 0.2))
    gm = acts.get('Town_Ground')
    if gm:
        try:
            m = gm.static_mesh_component.get_material(0)
            g.static_mesh_component.set_material(0, m)
        except Exception as ex:
            print('mat', ex)
cap = acts.get('CAT_Capture')
if not cap:
    cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0))
    cap.set_actor_label('CAT_Capture')
cc = cap.capture_component2d
rt = unreal.RenderingLibrary.create_render_target2d(world, W, H, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1))
cc.set_editor_property('texture_target', rt)
cc.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cc.set_editor_property('capture_every_frame', False)
cc.set_editor_property('fov_angle', 50.0)
pps = cc.get_editor_property('post_process_settings')
for k, v in (('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL), ('auto_exposure_bias', CAP_EV), ('auto_exposure_apply_physical_camera_exposure', False)):
    pps.set_editor_property(k, v); pps.set_editor_property('override_' + k, True)
pps.set_editor_property('color_gain', unreal.Vector4(CAP_GAIN, CAP_GAIN, CAP_GAIN, 1.0)); pps.set_editor_property('override_color_gain', True)
cc.set_editor_property('post_process_settings', pps)
cc.set_editor_property('post_process_blend_weight', 1.0)
flags = []
for fn in ('EyeAdaptation',):
    f = unreal.EngineShowFlagsSetting(); f.set_editor_property('show_flag_name', fn); f.set_editor_property('enabled', True); flags.append(f)
cc.set_editor_property('show_flag_settings', flags)
opt = unreal.ImageWriteOptions()
opt.set_editor_property('format', unreal.DesiredImageFormat.JPG)
opt.set_editor_property('compression_quality', QUAL)
opt.set_editor_property('overwrite_file', True)
opt.set_editor_property('async_', False)
for lab in LABELS:
    a = acts.get('CAND_' + lab)
    if not a:
        print('MISSING', lab); continue
    mn, mx = ism_bounds(a)
    c = unreal.Vector((mn[0]+mx[0])/2, (mn[1]+mx[1])/2, (mn[2]+mx[2])/2)
    w, d, h = mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]
    r = math.sqrt(w*w + d*d + h*h) / 2
    dist = r / math.sin(math.radians(22)) * 0.95
    for tag, yaw in (('a', -115.0), ('b', 65.0)):
        el = math.radians(14)
        cam = unreal.Vector(c.x + dist*math.cos(el)*math.cos(math.radians(yaw)), c.y + dist*math.cos(el)*math.sin(math.radians(yaw)), max(170.0, c.z + dist*math.sin(el)))
        cap.set_actor_location(cam, False, False)
        cap.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam, c), False)
        for _ in range(PASSES):
            cc.capture_scene()
        p = '%s/%s_%s%s.jpg' % (OUT, lab, tag, SUFFIX)
        unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, p, opt)
        print('SHOT %s %s %dB | W %.0f D %.0f H %.0f' % (lab, tag, os.path.getsize(p) if os.path.exists(p) else -1, w, d, h))
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
