
import os
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
cap = acts['CAT_Capture']; cc = cap.capture_component2d
if PHASE == 1:
    cc.set_editor_property('fov_angle', FOV)
    cam = unreal.Vector(*CAM); tgt = unreal.Vector(*TGT)
    cap.set_actor_location(cam, False, False); cap.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam, tgt), False)
    cc.set_editor_property('capture_every_frame', True)
    print('live on')
else:
    rt = cc.get_editor_property('texture_target')
    opt = unreal.ImageWriteOptions()
    opt.set_editor_property('format', unreal.DesiredImageFormat.JPG); opt.set_editor_property('compression_quality', 72)
    opt.set_editor_property('overwrite_file', True); opt.set_editor_property('async_', False)
    p = 'C:/MegaJam/shots/town/%s.jpg' % NAME; unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, p, opt)
    cc.set_editor_property('capture_every_frame', False)
    print('SHOT', NAME, os.path.getsize(p))
