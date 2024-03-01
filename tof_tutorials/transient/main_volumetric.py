import sys
sys.path.append('../')

import mitsuba as mi
import drjit as dr
variant = "scalar_rgb"
mi.set_variant(variant)
from utils.image_utils import *
from tqdm import tqdm, trange
import os
import matplotlib.pyplot as plt


def run_scene(
    scene_name="cornell-box",
    spp=1024,
    repeat = 1
):
    scene = mi.load_file("../../scenes/%s/scene_v3.xml" % (scene_name))
    image = mi.render(scene, spp=spp)
    
    image_hdr = to_ldr_image(image)
    plt.imshow(image_hdr)
    plt.show()

if __name__ == "__main__":
    run_scene(
        scene_name="cornell-box_volumetric", spp=64
    )