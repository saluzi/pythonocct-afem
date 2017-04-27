from OCC.SMESH import SMESH_Mesh
from OCC.TopAbs import TopAbs_COMPSOLID, TopAbs_SOLID
from OCC.TopoDS import TopoDS_Shape

from .methods.build_parts import build_surface_part
from .methods.explore_parts import get_shared_edges, get_shared_nodes
from .methods.form_parts import form_with_solid
from .methods.fuse_parts import fuse_surface_part
from .methods.merge_parts import merge_surface_part
from .methods.modify_parts import add_stiffener_to_surface_part, \
    discard_faces_by_distance, discard_faces_by_solid, unify_surface_part
from .methods.sew_parts import sew_surface_parts
from .part import Part
from .stiffener import Stiffener
from ..fem import MeshData
from ..fem.elements import Elm2D
from ..topology import ShapeTools


class SurfacePart(Part):
    """
    Base class for surface-based parts.
    """

    def __init__(self, label, surface_shape):
        super(SurfacePart, self).__init__(label)
        self._surface_shape = ShapeTools.to_shape(surface_shape)
        self._fshapes = set()
        self._sref = None
        self._set_sref()

    @property
    def surface_shape(self):
        return self._surface_shape

    @property
    def fshapes(self):
        return list(self._fshapes)

    @property
    def faces(self):
        return ShapeTools.get_faces(self)

    @property
    def edges(self):
        return ShapeTools.get_edges(self)

    @property
    def nfaces(self):
        return len(self.faces)

    @property
    def sref(self):
        return self._sref

    @property
    def reshapes(self):
        return self.faces

    @property
    def stiffeners(self):
        return [part for part in self.subparts if isinstance(part, Stiffener)]

    @property
    def elements(self):
        smesh_mesh = MeshData.get_mesh().smesh_obj
        if not isinstance(smesh_mesh, SMESH_Mesh):
            return []
        compound = ShapeTools.get_faces(self, True)
        submesh = smesh_mesh.GetSubMesh(compound)
        if submesh.IsEmpty():
            return []
        submesh_ds = submesh.GetSubMeshDS()
        if not submesh_ds:
            return []
        elm_iter = submesh_ds.GetElements()
        elm_set = set()
        while elm_iter.more():
            elm = Elm2D(elm_iter.next())
            elm_set.add(elm)
        return elm_set

    @property
    def nodes(self):
        node_set = set()
        for e in self.elements:
            for n in e.nodes:
                node_set.add(n)
        return node_set

    def _set_sref(self):
        """
        Set part reference surface is available.
        """
        if not self._surface_shape or self._surface_shape.IsNull():
            return False

        # Use largest face of surface shape.
        faces = ShapeTools.get_faces(self._surface_shape)
        if not faces:
            return False
        face = ShapeTools.largest_face(faces)
        if not face:
            return False

        # Convert to ASAP surface.
        sref = ShapeTools.surface_of_face(face)
        if not sref:
            return False

        self._sref = sref
        return True

    def form(self, *bodies):
        """
        Form part with bodies.

        :param bodies:

        :return:
        """
        status = {}
        for body in bodies:
            shape = form_with_solid(self._surface_shape, body)
            if not shape:
                status[body] = False
            else:
                self._fshapes.add(shape)
                status[body] = True
        return status

    def build(self, unify=False):
        """
        Build the part shape.

        :param bool unify:

        :return:
        """
        return build_surface_part(self, unify)

    def fuse(self, *other_parts):
        """
        Fuse with other parts.

        :param other_parts:

        :return:
        """
        _other_parts = []
        for part in other_parts:
            if isinstance(part, TopoDS_Shape) and not part.IsNull():
                _other_parts.append(part)
        if not _other_parts:
            return False
        return fuse_surface_part(self, *_other_parts)

    def sew(self, *other_parts):
        """
        Sew with other parts.

        :param other_parts:

        :return:
        """
        _other_parts = []
        for part in other_parts:
            if isinstance(part, TopoDS_Shape) and not part.IsNull():
                _other_parts.append(part)
        if not _other_parts:
            return False
        return sew_surface_parts([self] + _other_parts)

    def merge(self, other, unify=False):
        """
        Merge other part or shape with this one.
        
        :param other:
        :param bool unify:
         
        :return: 
        """
        return merge_surface_part(self, other, unify)

    def unify(self, edges=True, faces=True, concat_bsplines=False):
        """
        Attempt to unify the same domains of the part shape.
        
        :param edges: 
        :param faces: 
        :param concat_bsplines:
         
        :return: 
        """
        return unify_surface_part(self, edges, faces, concat_bsplines)

    def discard(self, shape, tol=None):
        """
        Discard faces of the part.

        :param shape:
        :param tol:

        :return:
        """
        shape = ShapeTools.to_shape(shape)
        if not shape:
            return False
        if shape.ShapeType() in [TopAbs_SOLID, TopAbs_COMPSOLID]:
            return discard_faces_by_solid(self, shape, tol)
        return discard_faces_by_distance(self, shape, tol)

    def shared_edges(self, other_part):
        """
        Get edges shared between the two parts.

        :param other_part:

        :return:
        """
        return get_shared_edges(self, other_part)

    def shared_nodes(self, other_part):
        """
        Get nodes shared between the two parts.

        :param other_part:

        :return:
        """
        return get_shared_nodes(self, other_part)

    def add_stiffener(self, label, stiffener):
        """
        Add a stiffener to the surface part.
        
        :param label:
        :param stiffener: 
        
        :return: 
        """
        stiffener = add_stiffener_to_surface_part(self, stiffener, label)
        if not stiffener:
            return None
        self._subparts[stiffener.label] = stiffener
        return stiffener

    def get_stiffener(self, label):
        """
        Get stiffener.
        
        :param label:
         
        :return: 
        """
        return self.get_subpart(label)
