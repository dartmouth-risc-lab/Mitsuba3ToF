import numpy as np
import matplotlib.pyplot as plt
import os
import cv2

def ToneMap(c, limit):
    luminance = 0.3*c[:,:,0] + 0.6*c[:,:,1] + 0.1*c[:,:,2]
    luminance = np.dstack([luminance]*3)
    col = c * 1.0 / (1.0 + luminance / limit)
    return col


def LinearToSrgb(c):
    kInvGamma = 1.0 / 2.2
    return np.power(c, kInvGamma)

def to_ldr_image(img):
    return LinearToSrgb(ToneMap(img, 1.5))

def to_png_image(image):
    image = np.asarray(image)
    image = to_ldr_image(image)
    image = image[:, :, 0:3]
    image = (image * 255.0)
    image = np.clip(image, 0, 255)
    image = image.astype(np.uint8)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return image

def rgb2luminance(img):
    return (0.2126 * img[...,0]) + (0.7152 * img[...,1]) + (0.0722 * img[...,2])

def save_tof_image(image, output_path, filename, 
    vmin_percentile=5, vmax_percentaile=95, 
    vmin=None, vmax=None, colorbar_also=False, resize=1, **kwargs):
    cm = plt.get_cmap('viridis')

    if vmin is None:
        vmin = np.percentile(image, vmin_percentile)
    if vmax is None:
        vmax = np.percentile(image, vmax_percentaile)
    norm = plt.Normalize(vmin, vmax)

    if len(image.shape) == 3:
        if image.shape[2] == 1:
            image = image[:,:,0]
        else:
            image = rgb2luminance(image)
        
    image = cm(norm(image))
    image = image[:, :, 0:3]
    image = (image * 255.0).astype(np.uint8)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    if resize != 1:
        image = cv2.resize(image, (0,0), fx=resize, fy=resize) 
    
    cv2.imwrite(os.path.join(output_path, filename), image)

def save_hdr_image(image, output_path, filename, colorbar_also=False, resize=1, **kwargs):
    image = np.asarray(image)
    if image.shape[2] == 1:
        image = np.concatenate([image, image, image], axis=-1)
    image = to_ldr_image(image)
    image = image[:, :, 0:3]
    image = (image * 255.0)
    image = np.clip(image, 0, 255)
    image = image.astype(np.uint8)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    if resize != 1:
        image = cv2.resize(image, (0,0), fx=resize, fy=resize) 
    cv2.imwrite(os.path.join(output_path, filename), image)

def export_video_from_images(images, outputdir, output_file_name, fps=24):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    image_0 = images[0]
    height = image_0.shape[0]
    width = image_0.shape[1]
    size = (width, height)
    out  = cv2.VideoWriter(os.path.join(outputdir, "%s.mp4" % output_file_name),  cv2.VideoWriter_fourcc(*'mp4v'), fps, size)

    for image in images:
        out.write(image)
    
    out.release()