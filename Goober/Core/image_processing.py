import itertools
import logging

import numpy as np
from line_profiler import profile
from PIL import Image as PImage
from PIL import ImageMath

logger = logging.getLogger("Core.ImageOps")


def get_histogram(image: PImage.Image):
    return [a for a in itertools.batched(image.histogram(), n=256)]


def add(image, dx):
    image = ImageMath.lambda_eval(
        lambda args: args["image"] + args["val"], image=image, val=dx
    )
    return image.convert("L")


@profile
def colour_balance(
    img: PImage.Image,
    shadows: tuple[float, float, float],
    midtones: tuple[float, float, float],
    highlights: tuple[float, float, float],
    preserve_luminance: bool = False,
) -> PImage.Image:
    # inspired by GIMP's algorithm but uses luminance instead of lightness
    # https://gitlab.gnome.org/GNOME/gimp/-/blob/master/app/operations/gimpoperationcolorbalance.c

    arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    image_YCbCr = img.convert("YCbCr")
    luminance = np.asarray(image_YCbCr.split()[0], dtype=np.float32) / 255.0

    # Convert input corrections from [-100,100] to [-1,1]
    s = np.array(shadows) / 100.0
    m = np.array(midtones) / 100.0
    h = np.array(highlights) / 100.0

    a = 0.25
    b = 0.333
    scale = 0.7

    # Compute masks
    mask_shadows = np.clip((luminance - b) / -a + 0.5, 0, 1) * scale
    mask_midtones = (
        np.clip((luminance - b) / a + 0.5, 0, 1)
        * np.clip((luminance + b - 1) / -a + 0.5, 0, 1)
        * scale
    )
    mask_highlights = np.clip((luminance + b - 1) / a + 0.5, 0, 1) * scale

    shadows_adjustment = mask_shadows[..., np.newaxis] * s
    midtones_adjustment = mask_midtones[..., np.newaxis] * m
    highlights_adjustment = mask_highlights[..., np.newaxis] * h

    arr = arr + shadows_adjustment + midtones_adjustment + highlights_adjustment
    arr = np.clip(arr, 0, 1)
    arr *= 255
    out = PImage.fromarray(arr.astype(np.uint8), "RGB")

    if preserve_luminance:
        out_y, out_cb, out_cr = out.convert("YCbCr").split()
        in_y = image_YCbCr.split()[0]
        out = PImage.merge("YCbCr", [in_y, out_cb, out_cr])
        out = out.convert("RGB")

    return out


def exposure(img: PImage.Image):
    return img
