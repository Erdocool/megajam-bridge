import unreal
# Small overlap tidy after dc_17: store-room boxes off the cupboard (F3), study lamp off the phone (F4), kitchen tables off the cupboards (F2/F4).
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
A = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
def bb(a): o, e = a.get_actor_bounds(False); return (o.x - e.x, o.x + e.x, o.y - e.y, o.y + e.y, o.z - e.z, o.z + e.z)
def put(a, x0, y0, zb):
    b = bb(a); p = a.get_actor_location(); a.set_actor_location(V(p.x + x0 - b[0], p.y + y0 - b[2], p.z + zb - b[4]), False, False)
Z = 901.5
put(A['Furn_F3_Store_Box0'], 700, 360, Z); put(A['Furn_F3_Store_Box1'], 705, 362, Z + 40); put(A['Furn_F3_Store_Box2'], 758, 362, Z)
la, ph, fo = A['Furn_F4_Study_Lamp'], A['Furn_F4_Study_Phone'], A['Furn_F4_Study_Folder']
top = bb(A['Furn_F4_Std_DeskTop'])[5]; pb = bb(ph); fb = bb(fo); lb = bb(la); w = lb[1] - lb[0]
x0 = 772 if fb[0] > 772 + w + 2 else None
if x0 is None:
    if pb[0] - fb[1] > w + 4: x0 = fb[1] + 2
    else: put(fo, 772 + w + 4, fb[2], top); x0 = 772
put(la, x0, 776 - (lb[3] - lb[2]), top)
for fl in (2, 4):
    t = A.get('Furn_F%d_Kit_Table' % fl); c = A.get('Furn_F%d_Kit_Cupboard' % fl)
    if t and c:
        tb, cb = bb(t), bb(c)
        if tb[0] < cb[1] and tb[3] > cb[2]: p = t.get_actor_location(); t.set_actor_location(V(p.x + cb[1] - tb[0] + 3, p.y, p.z), False, False)
print('TIDY lamp', [round(v) for v in bb(la)[:4]], 'phone', [round(v) for v in pb[:4]])
print('saved LI', les.save_current_level()); les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
