import sys
sys.path.append('../')

import mitsuba as mi
import drjit as dr
variant = "scalar_rgb"
mi.set_variant(variant)
from utils.image_utils import *
from tqdm import tqdm, trange
import os


def run_scene(
    scene_name="cornell-box",
    spp=1024,
    repeat = 1
):
    scene = mi.load_file("../../scenes/%s/scene_v3_transient.xml" % (scene_name))
    image = None
    for i in trange(repeat):
        image_i = mi.render(scene, spp=spp, seed=i)    
        image_i = np.asarray(image_i)
        if image is None:
            image = image_i
        else:
            image += image_i
    image /= repeat

    output_folder = "../result/transient/%s" % (scene_name)

    N = (image.shape[2]//3) - 1

    for i in range(N + 1):
        save_hdr_image(image[:,:,i*3:(i+1)*3] * N, os.path.join(output_folder, "images"), "%d.png" % i)
    
    images = []
    for i in range(N):
        image = cv2.imread(os.path.join(output_folder, "images", "%d.png" % i))
        images.append(image)
    export_video_from_images(images, os.path.join(output_folder, "video"), "transient", fps=60)

if __name__ == "__main__":
    run_scene(
        scene_name="cornell-box"
    )