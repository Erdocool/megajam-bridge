
import os
OUT = 'C:/MegaJam/shots/town'; os.makedirs(OUT, exist_ok=True)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in world.get_path_name()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
cap = acts['CAT_Capture']; cc = cap.capture_component2d
rt = unreal.RenderingLibrary.create_render_target2d(world, 1280, 720, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1))
cc.set_editor_property('texture_target', rt)
cc.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
pps = cc.get_editor_property('post_process_settings')
pps.set_editor_property('color_gain', unreal.Vector4(GAIN, GAIN, GAIN, 1.0)); pps.set_editor_property('override_color_gain', True)
cc.set_editor_property('post_process_settings', pps)
opt = unreal.ImageWriteOptions()
opt.set_editor_property('format', unreal.DesiredImageFormat.JPG); opt.set_editor_property('compression_quality', 72)
opt.set_editor_property('overwrite_file', True); opt.set_editor_property('async_', False)
for name, cam, tgt, fov in CAMS:
    cam = unreal.Vector(*cam); tgt = unreal.Vector(*tgt)
    cc.set_editor_property('fov_angle', fov)
    cap.set_actor_location(cam, False, False); cap.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam, tgt), False)
    for _ in range(PASSES): cc.capture_scene()
    p = '%s/%s.jpg' % (OUT, name); unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, p, opt)
    print('SHOT', name, os.path.getsize(p))
