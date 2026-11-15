import unreal
def ism_bounds(actor):
    mn = [1e18] * 3; mx = [-1e18] * 3
    for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        sm = c.get_editor_property('static_mesh')
        if not sm:
            continue
        bb = sm.get_bounding_box()
        lo, hi = bb.min, bb.max
        corners = [unreal.Vector(x, y, z) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        n = c.get_instance_count()
        step = max(1, n // 400)
        for i in range(0, n, step):
            t = c.get_instance_transform(i, True)
            for p in corners:
                w = t.transform_location(p)
                for k, v in enumerate((w.x, w.y, w.z)):
                    mn[k] = min(mn[k], v); mx[k] = max(mx[k], v)
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        if isinstance(c, unreal.InstancedStaticMeshComponent):
            continue
        o, e, r = unreal.SystemLibrary.get_component_bounds(c)
        if e.x + e.y + e.z <= 0:
            continue
        for k, (ov, ev) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
            mn[k] = min(mn[k], ov - ev); mx[k] = max(mx[k], ov + ev)
    return mn, mx
