#!/usr/bin/env python

import os.path
import unittest

from PIL import Image


class TestNFrames(unittest.TestCase):
    pass


def make_test_hasattr(path):
    def test(self):
        im = Image.open(path)
        if hasattr(im,'n_frames'):
            print("has attribute")
        else:
            print("no such attribute")
    return test


def make_test_try(path):
    def test(self):
        im = Image.open(path)
        try:
            result = im.n_frames
        except AttributeError:
            print("no such attribute")
    return test


def make_test_getattr(path):
    def test(self):
        im = Image.open(path)
        n = getattr(im, 'n_frames', None)
        if n is not None:
            result = n
        else:
            print("no such attribute")
    return test


if __name__ == '__main__':
    for path in ["0b2511096875ee38aea8b0b7e0b16652.gif",
                 "2fd17a9d5e4e9bfc5fb5ce6e44aa7815.gif"]:
        (basename, extension) = os.path.splitext(path)
        setattr(TestNFrames,
                "test_{0}_hasattr".format(basename),
                make_test_hasattr(path))
        setattr(TestNFrames,
                "test_{0}_try".format(basename),
                make_test_try(path))
        setattr(TestNFrames,
                "test_{0}_getattr".format(basename),
                make_test_getattr(path))
    unittest.main()