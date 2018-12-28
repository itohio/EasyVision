#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pytest import raises, approx, mark
from EasyVision.vision import *
from EasyVision.processors import *
import cv2
import json
import numpy as np


images_left = ["test_data/left{:02d}.jpg".format(i + 1) for i in range(14) if i != 9]
images_right = ["test_data/right{:02d}.jpg".format(i + 1) for i in range(14) if i != 9]

M_left =  [[535.5289137817749, 0.0, 333.9556024187135], [0.0, 535.3112518132406, 241.22736353333593], [0.0, 0.0, 1.0]]
d_left =  [[-0.29426670830681295, 0.11409183502487143, 0.0, 0.0, -0.023222122638183858]]
R_left =  [[0.9999334874229316, -0.009219753439929899, 0.0069294210956562], [0.009157022199168523, 0.999917293960849, 0.009030735432780011], [-0.007012109144755233, -0.008966681912493231, 0.9999352123716928]]
P_left =  [[535.3112518132406, 0.0, 325.9803276062012, 0.0], [0.0, 535.3112518132406, 242.73220443725586, 0.0], [0.0, 0.0, 1.0, 0.0]]
M_right =  [[535.5289137817749, 0.0, 332.7230162362328], [0.0, 535.3112518132406, 242.4827739733023], [0.0, 0.0, 1.0]]
d_right =  [[-0.27749259192017467, 0.07216678433491759, 0.0, 0.0, 0.013253845495251491]]
R_right =  [[0.9995094832757231, -0.013756342476967146, 0.02813460295709637], [0.014014659519211728, 0.9998612402293957, -0.009004976707086302], [-0.028006823462464206, 0.009394856496561677, 0.9995635820251514]]
P_right =  [[535.3112518132406, 0.0, 325.9803276062012, -1788.358792054079], [0.0, 535.3112518132406, 242.73220443725586, 0.0], [0.0, 0.0, 1.0, 0.0]]
R =  [[0.9997677227754339, 0.005049397702926733, -0.02095242418578015], [-0.004665553693462927, 0.9998211350625704, 0.018328406666336908], [0.021041223946258476, -0.018226394734858757, 0.9996124576203582]]
T =  [[-3.3391444063671307], [0.04595695668988882], [-0.0939916065445002]]
E =  [[0.0005284677305322451, 0.09313716510823399, 0.04766186280950206], [-0.023710089191732425, -0.06133516502932313, 3.339819698408143], [-0.030367324417407148, -3.3387792054633607, -0.06023828694666684]]
F =  [[-2.553919926621576e-08, -4.502859227625763e-06, -0.00013876836512866469], [1.14630066075936e-06, 2.966548445441988e-06, -0.0875695893199186], [0.0005164591622158981, 0.08722309177066455, 1.0]]
Q =  [[1.0, 0.0, 0.0, -325.9803276062012], [0.0, 1.0, 0.0, -242.73220443725586], [0.0, 0.0, 0.0, 535.3112518132406], [0.0, 0.0, 0.29933101466646467, -0.0]]

left_camera = PinholeCamera((640, 480), M_left, d_left, R_left, P_left)
right_camera = PinholeCamera((640, 480), M_right, d_right, R_right, P_right)

as_dict = {
    "left": left_camera.todict(),
    "right": right_camera.todict(),
    "R": R,
    "T": T,
    "E": E,
    "F": F,
    "Q": Q
}


def _assert_camera(camera):
    assert(isinstance(camera.left, PinholeCamera))
    assert(isinstance(camera.right, PinholeCamera))
    assert(isinstance(camera.R, np.ndarray))
    assert(isinstance(camera.T, np.ndarray))
    assert(isinstance(camera.E, np.ndarray))
    assert(isinstance(camera.F, np.ndarray))
    assert(isinstance(camera.Q, np.ndarray))


def test_stereo_camera():
    camera = StereoCamera(
        left_camera,
        right_camera,
        R,
        T,
        E,
        F,
        Q)
    _assert_camera(camera)


def test_stereo_camera_todict():
    camera = StereoCamera(
        left_camera,
        right_camera,
        R,
        T,
        E,
        F,
        Q)
    assert(as_dict == camera.todict())


def test_stereo_camera_fromdict():
    camera = StereoCamera.fromdict(as_dict)
    _assert_camera(camera)


@mark.slow
def test_stereo_calibrate():
    left = CalibratedCamera(ImagesReader(images_left), None)
    right = CalibratedCamera(ImagesReader(images_right), None)
    with CalibratedStereoCamera(left, right, None, max_samples=8) as vision:

        for i in range(15):
            cam = vision.calibrate()
            if cam:
                print 'M_left = ', cam.left.matrix.tolist()
                print 'd_left = ', cam.left.distortion.tolist()
                print 'R_left = ', cam.left.rectify.tolist()
                print 'P_left = ', cam.left.projection.tolist()

                print 'M_right = ', cam.right.matrix.tolist()
                print 'd_right = ', cam.right.distortion.tolist()
                print 'R_right = ', cam.right.rectify.tolist()
                print 'P_right = ', cam.right.projection.tolist()

                print 'R = ', cam.R.tolist()
                print 'T = ', cam.T.tolist()
                print 'E = ', cam.E.tolist()
                print 'F = ', cam.F.tolist()
                print 'Q = ', cam.Q.tolist()

                assert(isinstance(cam, StereoCamera))
                assert(isinstance(cam.left, PinholeCamera))
                assert(isinstance(cam.right, PinholeCamera))

                assert(cam.left.size == (640, 480))
                assert(cam.left.focal_point[0] == approx(left_camera.focal_point[0], rel=2))
                assert(cam.left.focal_point[1] == approx(left_camera.focal_point[1], rel=2))
                assert(cam.left.center[0] == approx(left_camera.center[0], rel=2))
                assert(cam.left.center[1] == approx(left_camera.center[1], rel=2))
                for i in range(5):
                    assert(cam.left.distortion[0][i] == approx(left_camera.distortion[0][i], rel=5e-1, abs=5e-1))

                assert(cam.right.size == (640, 480))
                assert(cam.right.focal_point[0] == approx(right_camera.focal_point[0], rel=2))
                assert(cam.right.focal_point[1] == approx(right_camera.focal_point[1], rel=2))
                assert(cam.right.center[0] == approx(right_camera.center[0], rel=2))
                assert(cam.right.center[1] == approx(right_camera.center[1], rel=2))
                for i in range(5):
                    assert(cam.right.distortion[0][i] == approx(right_camera.distortion[0][i], rel=5e-1, abs=5e-1))

                assert(True)
                break
        else:
            assert(False)


@mark.complex
def test_stereo_calibrated():
    from datetime import datetime

    camera = StereoCamera(left_camera, right_camera, R, T, E, F, Q)

    #left = CalibratedCamera(ImagesReader(images_left), None)
    #right = CalibratedCamera(ImagesReader(images_right), None)
    #with CalibratedStereoCamera(left, right, None, max_samples=8, display_results=False) as vision:

    #    for i in range(15):
    #        cam = vision.calibrate()
    #        if cam:
    #            camera = cam
    #            break
    #        if vision.display_results:
    #            cv2.waitKey(0)

    left = CalibratedCamera(ImagesReader(images_left), camera.left)
    right = CalibratedCamera(ImagesReader(images_right), camera.right)
    with CalibratedStereoCamera(left, right, camera, display_results=True) as vision:

        for frame in vision:
            print (datetime.now() - frame.timestamp).total_seconds()
            cv2.waitKey(0)
