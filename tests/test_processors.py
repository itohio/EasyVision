#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pytest import raises, approx
from EasyVision.vision.base import *
from EasyVision.processors.base import *


class Subclass(VisionBase):

    def __init__(self, name="", *args, **kwargs):
        super(Subclass, self).__init__(*args, **kwargs)
        self.frame = 0
        self.frames = 10
        self._name = name
        self._camera_called = False

    def capture(self):
        from datetime import datetime
        self.frame += 1
        return Frame(datetime.now(), self.frame - 1, (Image(self, 'an image'),))

    def setup(self):
        pass

    def release(self):
        pass

    def camera(self):
        self._camera_called = True
        return True

    @property
    def camera_called(self):
        return self._camera_called

    @property
    def is_open(self):
        return self.frame < self.frames

    @property
    def name(self):
        return 'Test'

    @property
    def description(self):
        pass

    @property
    def path(self):
        pass

    @property
    def frame_size(self):
        pass

    @property
    def fps(self):
        pass

    @property
    def frame_count(self):
        return self.frames

    @property
    def devices(self):
        """
        :return: [{name:, description:, path:, etc:}]
        """
        pass


class ProcessorA(ProcessorBase):

    def __init__(self, vision, *args, **kwargs):
        super(ProcessorA, self).__init__(vision, *args, **kwargs)

    @property
    def description(self):
        return "Simple processor"

    def process(self, image):
        new_image = image.image.upper()
        return image._replace(source=self, image=new_image)


class ProcessorB(ProcessorBase):

    def __init__(self, vision, *args, **kwargs):
        super(ProcessorB, self).__init__(vision, *args, **kwargs)

    @property
    def description(self):
        return "Simple processor 2"

    def process(self, image):
        new_image = image.image.title()
        return image._replace(source=self, image=new_image)


@pytest.mark.main
def test_abstract():
    with raises(TypeError):
        ProcessorBase()


@pytest.mark.main
def test_implementation():
    source = Subclass()
    pr = ProcessorA(source)
    assert(pr.source is source)


@pytest.mark.main
def test_capture():
    vision = Subclass(0)

    with ProcessorA(vision) as processor:
        img = processor.capture()
        assert(isinstance(img, Frame))
        assert(img.images[0].source is processor)
        assert(img.images[0].image == "AN IMAGE")


@pytest.mark.main
def test_capture_incorrect():
    vision = Subclass(0)
    processor = ProcessorA(vision)

    with raises(AssertionError):
        processor.capture()


@pytest.mark.main
def test_capture_stacked_incorrect():
    vision = Subclass(0)
    processorA = ProcessorA(vision)
    processorB = ProcessorB(processorA)

    assert(processorB.name == "ProcessorB <- ProcessorA <- Test")

    with raises(AssertionError):
        processorB.capture()


@pytest.mark.main
def test_capture_stacked():
    vision = Subclass(0)
    processorA = ProcessorA(vision)
    processorB = ProcessorB(processorA)

    assert(processorB.name == "ProcessorB <- ProcessorA <- Test")

    with processorB as processor:
        img = processor.capture()
        assert(isinstance(img, Frame))
        assert(img.images[0].source is processorB)
        assert(img.images[0].image == "An Image")
        assert(processorB.get_source('Test') is vision)
        assert(processorB.get_source('ProcessorA') is processorA)
        assert(processorB.get_source('ProcessorB') is processorB)
        assert(processorB.get_source('Test no') is None)


@pytest.mark.main
def test_method_resolution():
    vision = Subclass(0)
    processorA = ProcessorA(vision)
    processorB = ProcessorB(processorA)

    assert(processorB.name == "ProcessorB <- ProcessorA <- Test")

    assert(not vision.camera_called)
    assert(processorB.camera())
    assert(processorB.camera_called)
    assert(vision.camera_called)