# READ-ONLY: lighting / exposure audit of the open level (expects L_Building). Changes and saves nothing.
import os
import unreal

def p(*a):
    print(' '.join(str(x) for x in a))

def g(o, prop, d='?'):
    try:
        return o.get_editor_property(prop)
    except Exception:
        return d

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
p('== LEVEL', world.get_path_name().split('.')[0])
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
by = {}
for a in actors:
    by.setdefault(a.get_class().get_name(), []).append(a)
p('actor classes with light/sky/post:', sorted(k for k in by if any(s in k for s in ('Light', 'Sky', 'Fog', 'Post', 'Exposure', 'Cloud', 'Atmos'))))

for a in by.get('DirectionalLight', []):
    c = a.get_component_by_class(unreal.DirectionalLightComponent)
    p('SUN', a.get_actor_label(), 'rot', a.get_actor_rotation(), 'intensity', g(c, 'intensity'), 'atmos_sun', g(c, 'atmosphere_sun_light'),
      'mobility', g(c, 'mobility'), 'visible', g(c, 'visible'), 'hidden_in_game', a.is_hidden_ed())
for a in by.get('SkyLight', []):
    c = a.get_component_by_class(unreal.SkyLightComponent)
    p('SKYLIGHT', a.get_actor_label(), 'intensity', g(c, 'intensity'), 'real_time', g(c, 'real_time_capture'), 'mobility', g(c, 'mobility'))
for k in ('SkyAtmosphere', 'ExponentialHeightFog', 'VolumetricCloud', 'SkyDomeBP'):
    for a in by.get(k, []):
        p(k.upper(), a.get_actor_label())
pt = by.get('PointLight', []) + by.get('SpotLight', []) + by.get('RectLight', [])
p('local lights:', len(pt))

for a in by.get('PostProcessVolume', []):
    s = a.get_editor_property('settings')
    p('PPV', a.get_actor_label(), 'unbound', g(a, 'unbound'), 'enabled', g(a, 'enabled'), 'priority', g(a, 'priority'), 'blend_weight', g(a, 'blend_weight'))
    for prop in ('override_auto_exposure_method', 'auto_exposure_method', 'override_auto_exposure_min_brightness', 'auto_exposure_min_brightness',
                 'override_auto_exposure_max_brightness', 'auto_exposure_max_brightness', 'override_auto_exposure_bias', 'auto_exposure_bias',
                 'override_auto_exposure_apply_physical_camera_exposure', 'auto_exposure_apply_physical_camera_exposure',
                 'auto_exposure_speed_up', 'auto_exposure_speed_down'):
        p('   ', prop, g(s, prop))

try:
    rs = unreal.get_default_object(unreal.RendererSettings)
    for prop in ('default_feature_auto_exposure', 'default_feature_auto_exposure_method', 'default_feature_auto_exposure_bias',
                 'default_feature_auto_exposure_extend_default_luminance_range'):
        p('project', prop, g(rs, prop))
except Exception as e:
    p('project renderer settings ERR', e)

proj = unreal.Paths.project_dir()
for root, _, files in os.walk(os.path.join(proj, 'Content', 'Python')):
    for f in files:
        if 'night' in f.lower() or 'light' in f.lower():
            p('python file:', os.path.join(root, f))
for a in actors:
    lab = a.get_actor_label().lower()
    if 'night' in lab or 'moon' in lab or 'dusk' in lab:
        p('night-ish actor:', a.get_actor_label(), a.get_class().get_name())
p('== DONE (read-only)')
