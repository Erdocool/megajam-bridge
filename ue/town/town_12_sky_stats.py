
# L_Town step 12: brighter day sky via our own SkyAtmosphere luminance factor + skylight, fixed outdoor EV; numeric capture stats (tiny output)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in w.get_path_name()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
atm = acts['L_SkyAtmosphere'].get_component_by_class(unreal.SkyAtmosphereComponent)
atm.set_editor_property('sky_luminance_factor', unreal.LinearColor(SKYF, SKYF, SKYF, 1))
sl = acts['L_SkyLight'].get_component_by_class(unreal.SkyLightComponent)
sl.set_editor_property('intensity', SKY_INT); sl.recapture_sky()
out = acts['MJ_Exposure_PPV']; s = out.settings
s.set_editor_property('auto_exposure_min_brightness', OUT_EV); s.set_editor_property('auto_exposure_max_brightness', OUT_EV)
out.set_editor_property('settings', s)
cap = acts['CAT_Capture']; cc = cap.capture_component2d
rt = unreal.RenderingLibrary.create_render_target2d(w, 320, 180, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1))
cc.set_editor_property('texture_target', rt); cc.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
pps = cc.get_editor_property('post_process_settings')
pps.set_editor_property('color_gain', unreal.Vector4(1, 1, 1, 1)); pps.set_editor_property('auto_exposure_bias', OUT_EV)
cc.set_editor_property('post_process_settings', pps); cc.set_editor_property('fov_angle', 80)
for name, cam, tgt in STAT_CAMS:
    cam = unreal.Vector(*cam); tgt = unreal.Vector(*tgt)
    cap.set_actor_location(cam, False, False); cap.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam, tgt), False)
    for _ in range(6): cc.capture_scene()
    bands = []
    for y0, y1 in ((0, 45), (45, 135), (135, 180)):
        tot = 0; n = 0; clip = 0; blk = 0
        for y in range(y0 + 4, y1, 9):
            for x in range(4, 320, 10):
                c = unreal.RenderingLibrary.read_render_target_pixel(w, rt, x, y)
                l = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b; tot += l; n += 1
                clip += l > 245; blk += l < 12
        bands.append('%d/%d%%w/%d%%b' % (tot / n, 100 * clip // n, 100 * blk // n))
    print('STAT', name, 'top,mid,bot', ' '.join(bands))
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
