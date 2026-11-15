
# viewport (PPV-aware) screenshot via HighResShot; set VP_CAMS=[(name, cam, target)]
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
for name, cam, tgt in VP_CAMS:
    cam = unreal.Vector(*cam); tgt = unreal.Vector(*tgt)
    ues.set_level_viewport_camera_info(cam, unreal.MathLibrary.find_look_at_rotation(cam, tgt))
    r = unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, 'C:/MegaJam/shots/town/%s.png' % name)
    print('REQ', name, r)
