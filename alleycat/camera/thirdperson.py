from bge.types import KX_Camera, KX_GameObject
from mathutils import Vector
from mathutils.geometry import distance_point_to_plane

from alleycat.camera import PerspectiveCamera
from alleycat.control import ZoomControl


class ThirdPersonCamera(ZoomControl, PerspectiveCamera):

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj=obj)

    def process(self, pivot: KX_GameObject, viewpoint: KX_GameObject) -> None:
        assert pivot
        assert viewpoint

        # noinspection PyUnresolvedReferences
        up_axis = pivot.worldOrientation @ Vector((0, 0, 1))

        height = distance_point_to_plane(viewpoint.worldPosition, pivot.worldPosition, up_axis)

        rotation = self.rotation.to_matrix()

        # noinspection PyUnresolvedReferences
        orientation = pivot.worldOrientation @ rotation @ self.base_rotation

        # noinspection PyUnresolvedReferences
        offset = pivot.worldOrientation @ rotation @ Vector((0, -1, 0)) * self.distance

        self.object.worldOrientation = orientation

        # noinspection PyUnresolvedReferences
        self.object.worldPosition = pivot.worldPosition - offset + up_axis * height * 0.8
