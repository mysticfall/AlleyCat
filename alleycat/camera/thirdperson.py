from collections import OrderedDict
from itertools import chain

from bge.types import KX_Camera
from mathutils import Vector
from mathutils.geometry import distance_point_to_plane

from alleycat.camera import RotatableCamera, ZoomableCamera


class ThirdPersonCamera(RotatableCamera, ZoomableCamera):

    args = OrderedDict(chain(RotatableCamera.args.items(), ZoomableCamera.args.items()))

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj)

    def process(self) -> None:
        super().process()

        # noinspection PyUnresolvedReferences
        pivot = self.pivot

        up_axis = pivot.worldOrientation @ Vector((0, 0, 1))

        height = distance_point_to_plane(self.viewpoint.worldPosition, self.pivot.worldPosition, up_axis)

        rotation = self.rotation.to_matrix()

        # noinspection PyUnresolvedReferences
        orientation = pivot.worldOrientation @ rotation @ self.base_rotation

        # noinspection PyUnresolvedReferences
        offset = pivot.worldOrientation @ rotation @ Vector((0, -1, 0)) * self.distance

        self.object.worldOrientation = orientation

        # noinspection PyUnresolvedReferences
        self.object.worldPosition = pivot.worldPosition - offset + up_axis * height * 0.8
