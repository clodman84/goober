import itertools

from PIL import Image as PImage


def get_histogram(image: PImage.Image):
    return [a for a in itertools.batched(image.histogram(), n=256)]
