

SUPPORTED_TYPES = [
    "rectangle",
    "circle",
    "triangle",
    "helix",
    "sphere",
    "cone",
    "pyramid",
    "wedge",
    "mesh",
    "l_bracket",
    "washer",
    "shaft",
    "flange",
    "o_ring",
    "pulley",
    "sprocket",
    "spur_gear",
    "hex_bolt",
    "machine_screw",
    "hex_nut",
    "compression_spring",
    "extension_spring",
    "bevel_gear",
    "helical_gear",
]


DEFAULT_PARAMS = {
    "rectangle": {"length": 40, "width": 20, "height": 5},
    "circle": {"diameter": 40, "height": 5},
    "triangle": {"length": 40, "width": 30, "height": 5},
    "helix": {"radius": 10, "pitch": 5, "height": 50},
    "sphere": {"radius": 20},
    "cone": {"bottom_radius": 20, "top_radius": 0.1, "height": 40},
    "pyramid": {"length": 40, "width": 40, "height": 40},
    "wedge": {"length": 40, "width": 20, "height": 20},
    "mesh": {"length": 40, "width": 20, "height": 20},
    "l_bracket": {"length": 60, "height": 40, "width": 20, "thickness": 5},
    "washer": {"outer_diameter": 30, "inner_diameter": 10, "thickness": 3},
    "shaft": {"diameter": 20, "length": 100},
    "flange": {
        "outer_diameter": 80,
        "inner_diameter": 25,
        "thickness": 10,
        "bolt_count": 6,
        "bolt_diameter": 6,
        "bolt_circle_diameter": 60,
    },
    "o_ring": {"major_radius": 20, "tube_radius": 3},
    "pulley": {
        "outer_diameter": 60,
        "bore_diameter": 10,
        "width": 20,
        "hub_diameter": 25,
    },
    "sprocket": {
        "teeth": 48,
        "root_radius": 72,
        "outer_radius": 82,
        "thickness": 6,
        "center_bore_diameter": 80,
        "large_hole_count": 16,
        "large_hole_diameter": 18,
        "large_hole_circle_diameter": 120,
        "small_hole_count": 16,
        "small_hole_diameter": 6,
        "small_hole_circle_diameter": 150,
    },
    "spur_gear": {
        "teeth": 20,
        "root_radius": 25,
        "outer_radius": 32,
        "thickness": 8,
        "bore_diameter": 8,
    },
    "hex_bolt": {
        "shank_diameter": 8,
        "shank_length": 40,
        "head_radius": 8,
        "head_height": 5,
        "thread_pitch": 2,
        "thread_depth": 0.35,
    },
    "machine_screw": {
        "shank_diameter": 5,
        "length": 30,
        "head_diameter": 10,
        "head_height": 4,
        "thread_pitch": 1.5,
        "thread_depth": 0.25,
    },
    "hex_nut": {"outer_radius": 10, "hole_diameter": 8, "thickness": 6},
    "compression_spring": {"radius": 10, "wire_radius": 1, "pitch": 5, "height": 50},
    "extension_spring": {"radius": 10, "wire_radius": 1, "pitch": 4, "height": 50},
    "bevel_gear": {
        "teeth": 20,
        "bottom_radius": 30,
        "top_radius": 15,
        "height": 20,
        "bore_diameter": 8,
        "tooth_height": 4,
    },
    "helical_gear": {
        "teeth": 20,
        "root_radius": 25,
        "outer_radius": 32,
        "thickness": 12,
        "bore_diameter": 8,
        "helix_angle": 20,
    },
}


def get_default_params(shape_type: str) -> dict:
    if shape_type not in DEFAULT_PARAMS:
        return {}
    return dict(DEFAULT_PARAMS[shape_type])


def merge_params(shape_type: str, params: dict | None = None) -> dict:
    values = get_default_params(shape_type)

    if params:
        for key, value in params.items():
            if value is not None:
                values[key] = value

    return values


def format_object_name(shape_type: str) -> str:
    return "AI_" + shape_type


def header_code() -> str:
    return '''
import FreeCAD
import Part
import math

doc = FreeCAD.ActiveDocument
if doc is None:
    doc = FreeCAD.newDocument("AI_CAD_Output")


def shape_is_valid(shape):
    try:
        return shape is not None and not shape.isNull()
    except Exception:
        return shape is not None


def safe_cut(shape, cutter):
    try:
        result = shape.cut(cutter)
        if shape_is_valid(result):
            return result
    except Exception:
        pass
    return shape


def safe_fuse(shape_a, shape_b):
    try:
        result = shape_a.fuse(shape_b)
        if shape_is_valid(result):
            return result
    except Exception:
        pass

    try:
        return Part.makeCompound([shape_a, shape_b])
    except Exception:
        return shape_a


def make_ring(outer_diameter, inner_diameter, thickness):
    outer = Part.makeCylinder(outer_diameter / 2.0, thickness)
    inner = Part.makeCylinder(
        inner_diameter / 2.0,
        thickness + 2,
        FreeCAD.Vector(0, 0, -1),
        FreeCAD.Vector(0, 0, 1),
    )
    return safe_cut(outer, inner)


def make_hex_prism(radius, height):
    points = []
    for i in range(6):
        angle = 2.0 * math.pi * i / 6.0
        points.append(FreeCAD.Vector(radius * math.cos(angle), radius * math.sin(angle), 0))
    points.append(points[0])
    wire = Part.makePolygon(points)
    face = Part.Face(wire)
    return face.extrude(FreeCAD.Vector(0, 0, height))


def create_spur_gear_body(teeth, root_radius, outer_radius, thickness):
    points = []
    for i in range(teeth):
        base = 2.0 * math.pi * i / teeth
        a0 = base + 2.0 * math.pi * 0.00 / teeth
        a1 = base + 2.0 * math.pi * 0.22 / teeth
        a2 = base + 2.0 * math.pi * 0.50 / teeth
        a3 = base + 2.0 * math.pi * 0.78 / teeth
        a4 = base + 2.0 * math.pi * 1.00 / teeth
        points.append(FreeCAD.Vector(root_radius * math.cos(a0), root_radius * math.sin(a0), 0))
        points.append(FreeCAD.Vector(outer_radius * math.cos(a1), outer_radius * math.sin(a1), 0))
        points.append(FreeCAD.Vector(outer_radius * math.cos(a2), outer_radius * math.sin(a2), 0))
        points.append(FreeCAD.Vector(root_radius * math.cos(a3), root_radius * math.sin(a3), 0))
        points.append(FreeCAD.Vector(root_radius * math.cos(a4), root_radius * math.sin(a4), 0))
    points.append(points[0])
    wire = Part.makePolygon(points)
    face = Part.Face(wire)
    return face.extrude(FreeCAD.Vector(0, 0, thickness))


def create_sprocket_tooth_profile(teeth, root_radius, outer_radius, thickness):
    points = []
    tooth_step = 2.0 * math.pi / teeth
    valley_radius = root_radius
    tip_radius = outer_radius
    radius_delta = tip_radius - valley_radius

    for i in range(teeth):
        base = i * tooth_step

        for j in range(7):
            t = j / 6.0
            angle = base + tooth_step * (0.00 + 0.20 * t)
            radius = valley_radius + radius_delta * (1.0 - math.cos(math.pi * t)) / 2.0
            points.append(FreeCAD.Vector(radius * math.cos(angle), radius * math.sin(angle), 0))

        for j in range(5):
            t = j / 4.0
            angle = base + tooth_step * (0.20 + 0.18 * t)
            crown = 0.03 * radius_delta * math.sin(math.pi * t)
            radius = tip_radius + crown
            points.append(FreeCAD.Vector(radius * math.cos(angle), radius * math.sin(angle), 0))

        for j in range(7):
            t = j / 6.0
            angle = base + tooth_step * (0.38 + 0.20 * t)
            radius = tip_radius - radius_delta * (1.0 - math.cos(math.pi * t)) / 2.0
            points.append(FreeCAD.Vector(radius * math.cos(angle), radius * math.sin(angle), 0))

        for j in range(12):
            t = j / 11.0
            angle = base + tooth_step * (0.58 + 0.42 * t)
            dip = math.sin(math.pi * t)
            radius = valley_radius - radius_delta * 0.22 * dip
            points.append(FreeCAD.Vector(radius * math.cos(angle), radius * math.sin(angle), 0))

    points.append(points[0])
    wire = Part.makePolygon(points)
    face = Part.Face(wire)
    return face.extrude(FreeCAD.Vector(0, 0, thickness))


def create_threaded_shaft(diameter, length, pitch, ridge_radius):
    shaft_radius = diameter / 2.0
    shaft = Part.makeCylinder(shaft_radius, length)

    try:
        thread = Part.makeHelix(pitch, length, shaft_radius + ridge_radius * 1.25)
        return Part.makeCompound([shaft, thread])
    except Exception:
        return shaft


def add_shape_to_doc(shape, name):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    doc.recompute()
    return obj


'''


def footer_code(name: str) -> str:
    return f'''
obj = add_shape_to_doc(shape, "{name}")
'''


def generate_rectangle(params: dict) -> str:
    v = merge_params("rectangle", params)
    return f'''
shape = Part.makeBox({v["length"]}, {v["width"]}, {v["height"]})
'''


def generate_circle(params: dict) -> str:
    v = merge_params("circle", params)
    return f'''
shape = Part.makeCylinder({v["diameter"]} / 2.0, {v["height"]})
'''


def generate_triangle(params: dict) -> str:
    v = merge_params("triangle", params)
    return f'''
p1 = FreeCAD.Vector(0, 0, 0)
p2 = FreeCAD.Vector({v["length"]}, 0, 0)
p3 = FreeCAD.Vector({v["length"]} / 2.0, {v["width"]}, 0)
wire = Part.makePolygon([p1, p2, p3, p1])
face = Part.Face(wire)
shape = face.extrude(FreeCAD.Vector(0, 0, {v["height"]}))
'''


def generate_helix(params: dict) -> str:
    v = merge_params("helix", params)
    return f'''
shape = Part.makeHelix({v["pitch"]}, {v["height"]}, {v["radius"]})
'''


def generate_sphere(params: dict) -> str:
    v = merge_params("sphere", params)
    return f'''
shape = Part.makeSphere({v["radius"]})
'''


def generate_cone(params: dict) -> str:
    v = merge_params("cone", params)
    return f'''
shape = Part.makeCone({v["bottom_radius"]}, {v["top_radius"]}, {v["height"]})
'''


def generate_pyramid(params: dict) -> str:
    v = merge_params("pyramid", params)
    return f'''
p1 = FreeCAD.Vector(0, 0, 0)
p2 = FreeCAD.Vector({v["length"]}, 0, 0)
p3 = FreeCAD.Vector({v["length"]}, {v["width"]}, 0)
p4 = FreeCAD.Vector(0, {v["width"]}, 0)
top = FreeCAD.Vector({v["length"]} / 2.0, {v["width"]} / 2.0, {v["height"]})
faces = [
    Part.Face(Part.makePolygon([p1, p2, p3, p4, p1])),
    Part.Face(Part.makePolygon([p1, p2, top, p1])),
    Part.Face(Part.makePolygon([p2, p3, top, p2])),
    Part.Face(Part.makePolygon([p3, p4, top, p3])),
    Part.Face(Part.makePolygon([p4, p1, top, p4])),
]
shape = Part.makeSolid(Part.makeShell(faces))
'''


def generate_wedge(params: dict) -> str:
    v = merge_params("wedge", params)
    return f'''
p1 = FreeCAD.Vector(0, 0, 0)
p2 = FreeCAD.Vector({v["length"]}, 0, 0)
p3 = FreeCAD.Vector({v["length"]}, {v["width"]}, 0)
p4 = FreeCAD.Vector(0, {v["width"]}, 0)
p5 = FreeCAD.Vector(0, 0, {v["height"]})
p6 = FreeCAD.Vector(0, {v["width"]}, {v["height"]})
faces = [
    Part.Face(Part.makePolygon([p1, p2, p3, p4, p1])),
    Part.Face(Part.makePolygon([p1, p2, p5, p1])),
    Part.Face(Part.makePolygon([p4, p3, p6, p4])),
    Part.Face(Part.makePolygon([p1, p4, p6, p5, p1])),
    Part.Face(Part.makePolygon([p2, p3, p6, p5, p2])),
]
shape = Part.makeSolid(Part.makeShell(faces))
'''


def generate_mesh(params: dict) -> str:
    v = merge_params("mesh", params)
    return f'''
shape = Part.makeBox({v["length"]}, {v["width"]}, {v["height"]})
'''


def generate_l_bracket(params: dict) -> str:
    v = merge_params("l_bracket", params)
    return f'''
horizontal = Part.makeBox({v["length"]}, {v["width"]}, {v["thickness"]})
vertical = Part.makeBox({v["thickness"]}, {v["width"]}, {v["height"]})
vertical.translate(FreeCAD.Vector(0, 0, {v["thickness"]}))
shape = safe_fuse(horizontal, vertical)
'''


def generate_washer(params: dict) -> str:
    v = merge_params("washer", params)
    return f'''
shape = make_ring({v["outer_diameter"]}, {v["inner_diameter"]}, {v["thickness"]})
'''


def generate_shaft(params: dict) -> str:
    v = merge_params("shaft", params)
    return f'''
shape = Part.makeCylinder({v["diameter"]} / 2.0, {v["length"]})
'''


def generate_flange(params: dict) -> str:
    v = merge_params("flange", params)
    return f'''
shape = make_ring({v["outer_diameter"]}, {v["inner_diameter"]}, {v["thickness"]})
for i in range(int({v["bolt_count"]})):
    angle = 2.0 * math.pi * i / int({v["bolt_count"]})
    x = ({v["bolt_circle_diameter"]} / 2.0) * math.cos(angle)
    y = ({v["bolt_circle_diameter"]} / 2.0) * math.sin(angle)
    hole = Part.makeCylinder(
        {v["bolt_diameter"]} / 2.0,
        {v["thickness"]} + 2,
        FreeCAD.Vector(x, y, -1),
        FreeCAD.Vector(0, 0, 1),
    )
    shape = safe_cut(shape, hole)
'''


def generate_o_ring(params: dict) -> str:
    v = merge_params("o_ring", params)
    return f'''
shape = Part.makeTorus({v["major_radius"]}, {v["tube_radius"]})
'''


def generate_pulley(params: dict) -> str:
    v = merge_params("pulley", params)
    return f'''
main = Part.makeCylinder({v["outer_diameter"]} / 2.0, {v["width"]})
left_flange = Part.makeCylinder(({v["outer_diameter"]} * 1.1) / 2.0, {v["width"]} * 0.15)
right_flange = Part.makeCylinder(({v["outer_diameter"]} * 1.1) / 2.0, {v["width"]} * 0.15)
right_flange.translate(FreeCAD.Vector(0, 0, {v["width"]} * 0.85))
hub = Part.makeCylinder({v["hub_diameter"]} / 2.0, {v["width"]})
shape = safe_fuse(main, left_flange)
shape = safe_fuse(shape, right_flange)
shape = safe_fuse(shape, hub)
bore = Part.makeCylinder(
    {v["bore_diameter"]} / 2.0,
    {v["width"]} + 2,
    FreeCAD.Vector(0, 0, -1),
    FreeCAD.Vector(0, 0, 1),
)
shape = safe_cut(shape, bore)
'''


def generate_sprocket(params: dict) -> str:
    v = merge_params("sprocket", params)
    return f'''
shape = create_sprocket_tooth_profile(
    int({v["teeth"]}),
    {v["root_radius"]},
    {v["outer_radius"]},
    {v["thickness"]},
)

center_bore = Part.makeCylinder(
    {v["center_bore_diameter"]} / 2.0,
    {v["thickness"]} + 2,
    FreeCAD.Vector(0, 0, -1),
    FreeCAD.Vector(0, 0, 1),
)
shape = safe_cut(shape, center_bore)

for i in range(int({v["large_hole_count"]})):
    angle = 2.0 * math.pi * i / int({v["large_hole_count"]})
    x = ({v["large_hole_circle_diameter"]} / 2.0) * math.cos(angle)
    y = ({v["large_hole_circle_diameter"]} / 2.0) * math.sin(angle)
    hole = Part.makeCylinder(
        {v["large_hole_diameter"]} / 2.0,
        {v["thickness"]} + 2,
        FreeCAD.Vector(x, y, -1),
        FreeCAD.Vector(0, 0, 1),
    )
    shape = safe_cut(shape, hole)

for i in range(int({v["small_hole_count"]})):
    angle = 2.0 * math.pi * i / int({v["small_hole_count"]})
    x = ({v["small_hole_circle_diameter"]} / 2.0) * math.cos(angle)
    y = ({v["small_hole_circle_diameter"]} / 2.0) * math.sin(angle)
    hole = Part.makeCylinder(
        {v["small_hole_diameter"]} / 2.0,
        {v["thickness"]} + 2,
        FreeCAD.Vector(x, y, -1),
        FreeCAD.Vector(0, 0, 1),
    )
    shape = safe_cut(shape, hole)
'''


def generate_spur_gear(params: dict) -> str:
    v = merge_params("spur_gear", params)
    return f'''
shape = create_spur_gear_body(
    int({v["teeth"]}),
    {v["root_radius"]},
    {v["outer_radius"]},
    {v["thickness"]},
)
bore = Part.makeCylinder(
    {v["bore_diameter"]} / 2.0,
    {v["thickness"]} + 2,
    FreeCAD.Vector(0, 0, -1),
    FreeCAD.Vector(0, 0, 1),
)
shape = safe_cut(shape, bore)
'''


def generate_hex_bolt(params: dict) -> str:
    v = merge_params("hex_bolt", params)
    return f'''
shank = create_threaded_shaft(
    {v["shank_diameter"]},
    {v["shank_length"]},
    {v["thread_pitch"]},
    {v["thread_depth"]},
)
head = make_hex_prism({v["head_radius"]}, {v["head_height"]})
head.translate(FreeCAD.Vector(0, 0, {v["shank_length"]}))
shape = safe_fuse(shank, head)
'''


def generate_machine_screw(params: dict) -> str:
    v = merge_params("machine_screw", params)
    return f'''
shank = create_threaded_shaft(
    {v["shank_diameter"]},
    {v["length"]},
    {v["thread_pitch"]},
    {v["thread_depth"]},
)
head = Part.makeCylinder({v["head_diameter"]} / 2.0, {v["head_height"]})
head.translate(FreeCAD.Vector(0, 0, {v["length"]}))
shape = safe_fuse(shank, head)

slot_length = {v["head_diameter"]} * 0.8
slot_width = {v["head_diameter"]} * 0.18
slot_depth = {v["head_height"]} * 0.65
slot = Part.makeBox(slot_length, slot_width, slot_depth)
slot.translate(
    FreeCAD.Vector(
        -slot_length / 2.0,
        -slot_width / 2.0,
        {v["length"]} + {v["head_height"]} - slot_depth,
    )
)
shape = safe_cut(shape, slot)
'''


def generate_hex_nut(params: dict) -> str:
    v = merge_params("hex_nut", params)
    return f'''
nut = make_hex_prism({v["outer_radius"]}, {v["thickness"]})
hole = Part.makeCylinder(
    {v["hole_diameter"]} / 2.0,
    {v["thickness"]} + 2,
    FreeCAD.Vector(0, 0, -1),
    FreeCAD.Vector(0, 0, 1),
)
shape = safe_cut(nut, hole)
'''


def generate_compression_spring(params: dict) -> str:
    v = merge_params("compression_spring", params)
    return f'''
try:
    helix = Part.makeHelix({v["pitch"]}, {v["height"]}, {v["radius"]})
    profile = Part.Wire([
        Part.makeCircle(
            {v["wire_radius"]},
            FreeCAD.Vector({v["radius"]}, 0, 0),
            FreeCAD.Vector(1, 0, 0),
        )
    ])
    shape = helix.makePipeShell([profile], True, True)
except Exception:
    shape = Part.makeHelix({v["pitch"]}, {v["height"]}, {v["radius"]})
'''


def generate_extension_spring(params: dict) -> str:
    v = merge_params("extension_spring", params)
    return f'''
try:
    helix = Part.makeHelix({v["pitch"]}, {v["height"]}, {v["radius"]})
    profile = Part.Wire([
        Part.makeCircle(
            {v["wire_radius"]},
            FreeCAD.Vector({v["radius"]}, 0, 0),
            FreeCAD.Vector(1, 0, 0),
        )
    ])
    spring = helix.makePipeShell([profile], True, True)
except Exception:
    spring = Part.makeHelix({v["pitch"]}, {v["height"]}, {v["radius"]})

hook1 = Part.makeTorus({v["radius"]} * 0.45, {v["wire_radius"]})
hook1.translate(FreeCAD.Vector(0, 0, -{v["wire_radius"]} * 2))
hook2 = Part.makeTorus({v["radius"]} * 0.45, {v["wire_radius"]})
hook2.translate(FreeCAD.Vector(0, 0, {v["height"]} + {v["wire_radius"]} * 2))
shape = safe_fuse(spring, hook1)
shape = safe_fuse(shape, hook2)
'''

def generate_bevel_gear(params: dict) -> str:
    v = merge_params("bevel_gear", params)

    return f'''
def create_bevel_gear(teeth, bottom_radius, top_radius, height, bore_diameter, tooth_height):
    gear = Part.makeCone(bottom_radius, top_radius, height)

    if bottom_radius <= 0:
        return gear

    tooth_span = 0.56
    tooth_top_span = 0.26

    for i in range(teeth):
        base_angle = 2.0 * math.pi * i / teeth

        a0 = base_angle - (math.pi / teeth) * tooth_span
        a1 = base_angle - (math.pi / teeth) * tooth_top_span
        a2 = base_angle + (math.pi / teeth) * tooth_top_span
        a3 = base_angle + (math.pi / teeth) * tooth_span

        bottom_outer = bottom_radius + tooth_height
        top_outer = top_radius + tooth_height * (top_radius / bottom_radius)

        bottom_points = [
            FreeCAD.Vector(bottom_radius * math.cos(a0), bottom_radius * math.sin(a0), 0),
            FreeCAD.Vector(bottom_outer * math.cos(a1), bottom_outer * math.sin(a1), 0),
            FreeCAD.Vector(bottom_outer * math.cos(a2), bottom_outer * math.sin(a2), 0),
            FreeCAD.Vector(bottom_radius * math.cos(a3), bottom_radius * math.sin(a3), 0),
        ]

        top_points = [
            FreeCAD.Vector(top_radius * math.cos(a0), top_radius * math.sin(a0), height),
            FreeCAD.Vector(top_outer * math.cos(a1), top_outer * math.sin(a1), height),
            FreeCAD.Vector(top_outer * math.cos(a2), top_outer * math.sin(a2), height),
            FreeCAD.Vector(top_radius * math.cos(a3), top_radius * math.sin(a3), height),
        ]

        try:
            faces = [
                Part.Face(Part.makePolygon(bottom_points + [bottom_points[0]])),
                Part.Face(Part.makePolygon(top_points + [top_points[0]])),
                Part.Face(Part.makePolygon([bottom_points[0], bottom_points[1], top_points[1], top_points[0], bottom_points[0]])),
                Part.Face(Part.makePolygon([bottom_points[1], bottom_points[2], top_points[2], top_points[1], bottom_points[1]])),
                Part.Face(Part.makePolygon([bottom_points[2], bottom_points[3], top_points[3], top_points[2], bottom_points[2]])),
                Part.Face(Part.makePolygon([bottom_points[3], bottom_points[0], top_points[0], top_points[3], bottom_points[3]])),
            ]

            shell = Part.makeShell(faces)
            tooth = Part.makeSolid(shell)
            gear = safe_fuse(gear, tooth)

        except Exception:
            pass

    bore = Part.makeCylinder(
        bore_diameter / 2.0,
        height + 2,
        FreeCAD.Vector(0, 0, -1),
        FreeCAD.Vector(0, 0, 1),
    )

    return safe_cut(gear, bore)


shape = create_bevel_gear(
    int({v["teeth"]}),
    {v["bottom_radius"]},
    {v["top_radius"]},
    {v["height"]},
    {v["bore_diameter"]},
    {v["tooth_height"]},
)
'''
def generate_helical_gear(params: dict) -> str:
    v = merge_params("helical_gear", params)
    return f'''
shape = create_spur_gear_body(
    int({v["teeth"]}),
    {v["root_radius"]},
    {v["outer_radius"]},
    {v["thickness"]},
)
bore = Part.makeCylinder(
    {v["bore_diameter"]} / 2.0,
    {v["thickness"]} + 2,
    FreeCAD.Vector(0, 0, -1),
    FreeCAD.Vector(0, 0, 1),
)
shape = safe_cut(shape, bore)

helix = Part.makeHelix(
    {v["thickness"]} / 2.0,
    {v["thickness"]},
    {v["outer_radius"]} * 0.95,
)
shape = Part.makeCompound([shape, helix])
'''


GENERATOR_MAP = {
    "rectangle": generate_rectangle,
    "circle": generate_circle,
    "triangle": generate_triangle,
    "helix": generate_helix,
    "sphere": generate_sphere,
    "cone": generate_cone,
    "pyramid": generate_pyramid,
    "wedge": generate_wedge,
    "mesh": generate_mesh,
    "l_bracket": generate_l_bracket,
    "washer": generate_washer,
    "shaft": generate_shaft,
    "flange": generate_flange,
    "o_ring": generate_o_ring,
    "pulley": generate_pulley,
    "sprocket": generate_sprocket,
    "spur_gear": generate_spur_gear,
    "hex_bolt": generate_hex_bolt,
    "machine_screw": generate_machine_screw,
    "hex_nut": generate_hex_nut,
    "compression_spring": generate_compression_spring,
    "extension_spring": generate_extension_spring,
    "bevel_gear": generate_bevel_gear,
    "helical_gear": generate_helical_gear,
}


def generate_freecad_code(shape_type: str, params: dict | None = None) -> str:
    if shape_type not in GENERATOR_MAP:
        raise ValueError(f"Unsupported shape type: {shape_type}")

    params = merge_params(shape_type, params)
    body = GENERATOR_MAP[shape_type](params)
    name = format_object_name(shape_type)

    return header_code() + body + footer_code(name)


def get_supported_types() -> list[str]:
    return list(SUPPORTED_TYPES)


if __name__ == "__main__":
    print(generate_freecad_code("sprocket"))
