# Adds ONE unbound PostProcessVolume "MJ_Exposure_PPV" to the open L_Building that caps eye adaptation,
# so the exterior no longer darkens when the player walks up to the building.
# Touches NO light actor and no other actor. Re-running only updates the same PPV (no duplicates).
# Needs confirmation before running (it modifies and saves L_Building).
import math
import unreal

EV_OUT = None        # outdoor EV100 to lock to; None = estimate from the sun intensity
INTERIOR_RANGE = 3.0  # how many EV the image may still brighten indoors (0 = fully fixed exposure)
SAVE = True

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
lvl = world.get_path_name().split('.')[0]
if not lvl.endswith('L_Building'):
    raise RuntimeError('Open level is %s, not L_Building. Nothing changed.' % lvl)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()

ev = EV_OUT
if ev is None:
    lux = None
    for a in actors:
        if a.get_class().get_name() == 'DirectionalLight':
            lux = a.get_component_by_class(unreal.DirectionalLightComponent).get_editor_property('intensity')
            break
    # incident-meter rule EV100 = log2(lux / 2.5); keep sane for low, non-physical sun values
    ev = math.log2(max(lux or 10.0, 1.0) / 2.5) if lux else 10.0
    ev = max(-2.0, min(15.0, ev - 1.0))   # -1 EV so the sunny exterior is not too dark
    print('sun lux', lux, '-> EV_OUT', round(ev, 2))

ext = True
try:
    ext = bool(unreal.get_default_object(unreal.RendererSettings).get_editor_property('default_feature_auto_exposure_extend_default_luminance_range'))
except Exception:
    pass
def unit(e):  # PPV min/max are EV100 when the extended range is on, else luminance (cd/m2)
    return e if ext else 0.125 * (2.0 ** e)
print('extended luminance range:', ext)

ppv = None
for a in actors:
    if a.get_actor_label() == 'MJ_Exposure_PPV':
        ppv = a
if ppv is None:
    ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    ppv.set_actor_label('MJ_Exposure_PPV')
    print('spawned MJ_Exposure_PPV')
ppv.set_editor_property('unbound', True)
ppv.set_editor_property('enabled', True)
ppv.set_editor_property('priority', 10.0)
ppv.set_editor_property('blend_weight', 1.0)
s = ppv.get_editor_property('settings')
s.set_editor_property('override_auto_exposure_method', True)
s.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_HISTOGRAM)
s.set_editor_property('override_auto_exposure_min_brightness', True)
s.set_editor_property('auto_exposure_min_brightness', unit(ev - INTERIOR_RANGE))
s.set_editor_property('override_auto_exposure_max_brightness', True)
s.set_editor_property('auto_exposure_max_brightness', unit(ev))   # cap: never darker than outdoors
s.set_editor_property('override_auto_exposure_bias', True)
s.set_editor_property('auto_exposure_bias', 0.0)
s.set_editor_property('override_auto_exposure_speed_up', True)
s.set_editor_property('auto_exposure_speed_up', 2.0)
s.set_editor_property('override_auto_exposure_speed_down', True)
s.set_editor_property('auto_exposure_speed_down', 1.0)
ppv.set_editor_property('settings', s)
print('MJ_Exposure_PPV: EV100 min %.2f max %.2f' % (ev - INTERIOR_RANGE, ev))
if SAVE:
    print('saved', unreal.EditorLevelLibrary.save_current_level())
