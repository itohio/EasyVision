# -*- coding: utf-8 -*-
import cv2
import numpy as np
from .base import *


class PinholeCamera(namedtuple('PinholeCamera', ['size', 'matrix', 'distortion', 'rectify', 'projection'])):

    """

        size - (width, height)
        matrix - camera matrix
        distortion - camera distortion coefficients
        rectify - rectification transform matrix
        projection - reprojection matrix

    """

    def __new__(cls, size, matrix, distortion, rectify=None, projection=None):
        matrix = np.array(matrix) if isinstance(matrix, list) else matrix
        distortion = np.array(distortion) if isinstance(distortion, list) else distortion
        rectify = np.array(rectify) if isinstance(rectify, list) else rectify
        projection = np.array(projection) if isinstance(projection, list) else projection

        return super(PinholeCamera, cls).__new__(cls, size, matrix, distortion, rectify, projection)

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    @property
    def focal_point(self):
        return (self.matrix[0, 0], self.matrix[1, 1])

    @property
    def center(self):
        return (self.matrix[0, 2], self.matrix[1, 2])

    @staticmethod
    def fromdict(as_dict):
        return PinholeCamera(**as_dict)

    def todict(self):
        d = {
            "size": self.size,
            "matrix": self.matrix.tolist(),
            "distortion": self.distortion.tolist(),
            "rectify": self.rectify.tolist() if self.rectify is not None else None,
            "projection": self.projection.tolist() if self.projection is not None else None
        }
        return d

    @staticmethod
    def from_parameters(frame_size, focal_point, center, distortion, rectify=None, projection=None):
        if len(distortion) != 5:
            raise ValueError("distortion must be vector of length 5")
        if len(frame_size) != 2:
            raise ValueError("frame size must be vector of length 2")
        if len(focal_point) != 2:
            raise ValueError("focal point must be vector of length 2")
        if len(center) != 2:
            raise ValueError("center must be vector of length 2")
        matrix = np.zeros((3, 3), np.float32)
        matrix[0, 0] = focal_point[0]
        matrix[1, 1] = focal_point[1]
        matrix[0, 2] = center[0]
        matrix[1, 2] = center[1]
        matrix[2, 2] = 1
        d = np.zeros((1, 5), np.float32)
        d[0] = distortion
        return PinholeCamera(frame_size, matrix, d, rectify, projection)


class CalibratedCamera(ProcessorBase):
    def __init__(self, vision, camera, grid_shape=(7, 6), max_samples=20, debug=False, display_results=False, enabled=True, *args, **kwargs):
        calibrate = camera is None
        if not calibrate:
            if not isinstance(camera, PinholeCamera) and not (isinstance(camera, tuple) and len(camera) == 3):
                raise TypeError("Camera must be either PinholeCamera or tuple with (frame_size, camera_matrix, distortion)")
            self._camera = PinholeCamera._make(camera)
        else:
            self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            self._camera = None
            self._grid_shape = grid_shape
            self._max_samples = max_samples

        self._calibrate = calibrate
        super(CalibratedCamera, self).__init__(vision, debug=debug, display_results=display_results, enabled=enabled, *args, **kwargs)

    def setup(self):
        super(CalibratedCamera, self).setup()
        if self._calibrate:
            # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
            self.objp = np.zeros((np.prod(self._grid_shape), 3), np.float32)
            self.objp[:, :2] = np.indices(self._grid_shape).T.reshape(-1, 2)

            # Arrays to store object points and image points from all the images.
            self.objpoints = []  # 3d point in real world space
            self.imgpoints = []  # 2d points in image plane.
            self.calibration_samples = 0
        else:
            print self.camera.rectify, self.camera.projection
            self._mapx, self._mapy = cv2.initUndistortRectifyMap(
                    self.camera.matrix,
                    self.camera.distortion,
                    self.camera.rectify,
                    self.camera.projection,
                    self.camera.size,
                    cv2.CV_32FC1)

    @property
    def description(self):
        return "Pinhole camera undistort processor"

    @property
    def camera(self):
        return self._camera

    def process(self, image):
        if self._calibrate:
            img = image.image
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, self._grid_shape, None)
            if ret is True:
                corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)

            # Draw and display the corners
            if self.display_results:
                img = cv2.drawChessboardCorners(img, self._grid_shape, corners, ret)
                cv2.imshow(self.name, img)

            return ImageWithFeatures(self, gray, (ret, corners), 'corners')
        else:
            mapped = cv2.remap(image.image, self._mapx, self._mapy, cv2.INTER_NEAREST)

            if self.display_results:
                cv2.imshow(self.name, mapped)

            return image._replace(image=mapped)

    def calibrate(self):
        if not self._calibrate:
            raise ValueError("calibrate parameter must be set")

        if self.calibration_samples >= self._max_samples:
            return self._camera

        frame = self.capture()

        ret, corners = frame.images[0].features
        img = frame.images[0].image

        # If found, add object points, image points (after refining them)
        if ret is True:
            self.objpoints.append(self.objp)
            self.imgpoints.append(corners)

            self.calibration_samples += 1

        if self.calibration_samples >= self._max_samples:
            shape = img.shape[::-1]
            self._camera = self._finish_calibration(self.objpoints, self.imgpoints, shape)
            return self._camera

    def _finish_calibration(self, objpoints, imgpoints, shape):
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, shape, None, None)

            return PinholeCamera(shape, mtx, dist)
