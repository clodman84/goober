import itertools
import logging

import numpy as np
from line_profiler import profile
from PIL import Image as PImage
from PIL import ImageMath

from Core import utils

logger = logging.getLogger("Core.ImageOps")


def get_histogram(image: PImage.Image):
    return [a for a in itertools.batched(image.histogram(), n=256)]


def add(image, dx):
    image = ImageMath.lambda_eval(
        lambda args: args["image"] + args["val"], image=image, val=dx
    )
    return image.convert("L")


def colour_balance(image: PImage.Image, dr, dg, db):
    # TODO: try out numpy and see if its faster
    r, g, b, a = image.split()
    r = add(r, dr)
    g = add(g, dg)
    b = add(b, db)
    out = PImage.merge("RGBA", [r, g, b, a])
    return out
