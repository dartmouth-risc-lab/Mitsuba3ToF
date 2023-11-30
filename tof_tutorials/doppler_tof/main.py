import sys
sys.path.append('../')

import mitsuba as mi
import drjit as dr
import numpy as np
variant = "cuda_rgb"
mi.set_variant(variant)
from tqdm import tqdm, trange
import matplotlib.pyplot as plt
import cv2
from utils.image_utils import *

def run_scene(
    scene_name="cornell-box",
    spp=1024,
    repeat = 1
):
    scene = mi.load_file("../../scenes/%s/scene_v3_doppler.xml" % (scene_name))
    image = None
    for i in trange(repeat):
        image_i = mi.render(scene, spp=spp, seed=i)    
        image_i = np.asarray(image_i)
        if image is None:
            image = image_i
        else:
            image += image_i
    image /= repeat
    image *= 0.0015 # exposure time
    
    output_folder = "../result/doppler/%s" % (scene_name)
    save_tof_image(image, output_folder, "doppler.png", vmin=-1e-6, vmax=1e-6)

if __name__ == "__main__":
    run_scene(
        scene_name="cornell-box"
    )

