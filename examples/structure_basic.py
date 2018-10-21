from afem.config import Settings
from afem.exchange import ImportVSP
from afem.geometry import *
from afem.graphics import Viewer
from afem.structure import *
from afem.topology import *

Settings.log_to_console()

# Set units to inch.
Settings.set_units('in')

# Initialize a viewer
gui = Viewer()

# Import an OpenVSP model that includes OML reference geometry
fn = r'../models/simple_wing.stp'
vsp_import = ImportVSP(fn)
wing = vsp_import['WingGeom']
wing.set_color(1., 0., 0.)
wing.set_transparency(0.75)

# gui.add(wing.sref, wing)
# gui.start()
# gui.clear()

# Define a group to put the structure in
wingbox = GroupAPI.create_group('wing box')

# Define a front spar between parameters on the wing reference surface
fspar = RibByParameters('fspar', 0.15, 0.1, 0.15, 0.98, wing).part

# gui.add(wing.sref, fspar, fspar.cref, fspar.cref.p1, fspar.cref.p2)
# gui.start()

# Define a rear spar between parameters on the wing reference surface
rspar = RibByParameters('rspar', 0.65, 0.1, 0.65, 0.98, wing).part

# gui.add(rspar, rspar.cref, rspar.cref.p1, rspar.cref.p2)
# gui.start()

# Define root rib between front and rear spar
root = RibByPoints('root', fspar.cref.p1, rspar.cref.p1, wing).part

# gui.add(root, root.cref, root.cref.p1, root.cref.p2)
# gui.start()

# Define tip rib between front and rear spar
tip = RibByPoints('tip', fspar.cref.p2, rspar.cref.p2, wing).part

# gui.add(tip, tip.cref, tip.cref.p1, tip.cref.p2)
# gui.start()

# Add ribs between root and tip perpendicular to rear spar reference curve
ribs = RibsAlongCurveByDistance('rib', rspar.cref, 30., fspar, rspar, wing,
                                d1=30., d2=-30.).parts

# for rib in ribs:
#     gui.add(rib, rib.cref, rib.cref.p1, rib.cref.p2)
# gui.start()

# Add a front center spar considering the intersection between the front spar
# and the root rib. If this is not considered, the front center spar may be
# oriented in such a way that causes it to have a gap with the front spar and
# root rib.
p1 = wing.sref.eval(0.25, .0)
pln = PlaneByIntersectingShapes(fspar.shape, root.shape, p1).plane
fcspar = SparByPoints('fcspar', p1, root.cref.p1, wing, pln).part

# gui.add(fcspar, fcspar.cref, fcspar.cref.p1, fcspar.cref.p2)
# gui.start()

# Add rear center spar
p1 = wing.sref.eval(0.75, .0)
pln = PlaneByIntersectingShapes(rspar.shape, root.shape, p1).plane
rcspar = SparByPoints('rcspar', p1, root.cref.p2, wing, pln).part

# gui.add(rcspar, rcspar.cref, rcspar.cref.p1, rcspar.cref.p2)
# gui.start()

# Add center ribs using a reference plane alonge the rear center spar
ref_pln = PlaneByAxes(origin=(0., 0., 0.), axes='xz').plane
ribs = RibsAlongCurveByNumber('center rib', rcspar.cref, 3, fcspar, rcspar,
                              wing, ref_pln, d1=6, d2=-18).parts

# for rib in ribs:
#     gui.add(rib, rib.cref, rib.cref.p1, rib.cref.p2)
# gui.start()

# Draw the part reference curves to see what the layout will eventually look
# like
# gui.clear()
# gui.add(wing.sref)
# for part in wingbox.get_parts():
#     gui.add(part.cref)
# gui.start()

# Join the internal structure using their reference curves to check for actual
# intersection
internal_parts = wingbox.get_parts()
FuseSurfacePartsByCref(internal_parts)

# gui.add(wingbox)
# gui.start()

# Discard faces of parts using the reference curve
DiscardByCref(internal_parts)

# gui.clear()
# gui.add(wingbox)
# gui.start()

# Extract the shell of wing to define the wing skin
skin = SkinByBody('skin', wing).part
skin.set_transparency(0.5)

# gui.add(skin)
# gui.start()

# Join the wing skin with the internal structure
skin.fuse(*internal_parts)

# Discard wing skin that is touching the wing reference surface. This should
# leave only the upper and lower skins.
print(skin.shape.shape_type)
skin.discard_by_dmin(wing.sref, 1.)

# After removing the faces, the skin is now a compound of two shells, one upper
# shell and one lower. Use the Part.fix() to alter the shape from an invalid
# shell to a compound of two shells.
print('Skin shape type before fix:', skin.shape.shape_type)
skin.fix()
print('Skin shape type after fix:', skin.shape.shape_type)

gui.clear()
gui.add(wingbox)
gui.start()

# Check for free edges
shape = GroupAPI.get_shape()
tool = ExploreFreeEdges(shape)

gui.clear()
gui.add(shape, *tool.free_edges)
gui.start()

# Begin meshing
print('Creating mesh')
mesh = MeshVehicle(4.)
mesh.compute()

# View
gui.clear()
gui.add(wingbox)
gui.add(mesh.mesh)
gui.start()
