import pytest
import mitsuba as mi
import drjit as dr

from mitsuba.scalar_rgb.test.util import fresolver_append_path

###
### Reference images are generated using the `optixDenoiser` example provided
### with the OptiX 7.4 SDK. The example will always output float16 EXRs with an
### alpha channel. The script to generate the reference images is located at
### `mitsuba3/resources/data/tests/denoiser/denoiser_ref.py`.
###


def fix_normals(normals):
    # Normals are already in correct frame for OptiX, so we need to rotate them
    # by 180 degrees first as the OptixDenoiser always does that
    new_normals = dr.zeros(mi.Normal3f, normals.shape[0] * normals.shape[1])
    for i in range(3):
        new_normals[i] = dr.ravel(normals)[i::3]
    new_normals[0] = -new_normals[0]
    new_normals[2] = -new_normals[2]
    for i in range(3):
        normals[..., i] = new_normals[i]

    return normals


def test01_denoiser_construct(variants_any_cuda):
    input_res = [33, 18]

    assert (
        "OptixDenoiser[\n  input_size = [33, 18],\n  albedo = 0,\n  " +
        "normals = 0,\n  temporal = 0\n]" == str(mi.OptixDenoiser(input_res))
    )

    with pytest.raises(Exception) as e:
        mi.OptixDenoiser(input_res, albedo=False, normals=True)
    e.match("The denoiser cannot use normals to guide its process without " +
            "also providing albedo information!")


@fresolver_append_path
def test02_denoiser_denoise(variant_cuda_ad_rgb):
    noisy = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/noisy.exr"))
    ref = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/ref.exr"))[...,:3]

    denoiser = mi.OptixDenoiser(noisy.shape[:2])
    denoised = mi.util.convert_to_bitmap(
        denoiser(noisy), uint8_srgb=False
    )
    denoised = mi.TensorXf(denoised.convert(component_format=mi.Struct.Type.Float16))

    ref_array = ref.array
    denoised_array = denoised.array

    assert dr.allclose(denoised_array, ref_array)


@fresolver_append_path
def test03_denoiser_denoise_albedo(variant_cuda_ad_rgb):
    noisy = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/noisy.exr"))
    albedo = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/albedo.exr"))
    ref = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/ref_albedo.exr"))

    denoiser = mi.OptixDenoiser(noisy.shape[:2], True)
    denoised = mi.util.convert_to_bitmap(
        denoiser(noisy, False, albedo), uint8_srgb=False
    )
    denoised = mi.TensorXf(denoised.convert(component_format=mi.Struct.Type.Float16))

    ref_tensor = mi.TensorXf(ref)[...,:3]
    denoised_tensor = mi.TensorXf(denoised)

    ref_array = ref_tensor.array
    denoised_array = denoised_tensor.array

    assert dr.allclose(denoised_array, ref_array)


@fresolver_append_path
def test04_denoiser_denoise_normals(variant_cuda_ad_rgb):
    noisy = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/noisy.exr"))
    albedo = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/albedo.exr"))
    normals = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/normals.exr"))
    ref = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/ref_normals.exr"))

    normals = fix_normals(normals)

    denoiser = mi.OptixDenoiser(noisy.shape[:2], True, True)
    denoised = mi.util.convert_to_bitmap(
        denoiser(noisy, False, albedo, normals), uint8_srgb=False
    )
    denoised = mi.TensorXf(denoised.convert(component_format=mi.Struct.Type.Float16))

    ref_tensor = mi.TensorXf(ref)[...,:3]
    denoised_tensor = mi.TensorXf(denoised)

    ref_array = ref_tensor.array
    denoised_array = denoised_tensor.array

    assert dr.allclose(denoised_array, ref_array)

@fresolver_append_path
def test05_denoiser_denoise_temporal(variant_cuda_ad_rgb):
    noisy = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/noisy.exr"))
    albedo = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/albedo.exr"))
    normals = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/normals.exr"))
    flow = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/flow.exr"))
    previous_denoised = noisy
    ref = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/ref_temporal.exr"))

    normals = fix_normals(mi.TensorXf(normals))

    denoiser = mi.OptixDenoiser(noisy.shape[:2], True, True, True)
    denoised = mi.util.convert_to_bitmap(
        denoiser(noisy, False, albedo, normals, flow=flow, previous_denoised=previous_denoised),
        uint8_srgb=False
    )
    denoised = mi.TensorXf(denoised.convert(component_format=mi.Struct.Type.Float16))

    ref_tensor = mi.TensorXf(ref)[...,:3]
    denoised_tensor = mi.TensorXf(denoised)

    ref_array = ref_tensor.array
    denoised_array = denoised_tensor.array

    assert dr.allclose(denoised_array, ref_array)

@fresolver_append_path
def test05_denoiser_denoise_multichannel_bitmap(variant_cuda_ad_rgb):
    ref = mi.TensorXf(mi.Bitmap("resources/data/tests/denoiser/ref_normals.exr"))

    scene = mi.load_file("resources/data/scenes/cbox/cbox-rgb.xml", res=64)
    sensor = scene.sensors()[0]
    integrator = mi.load_dict({
        'type': 'aov',
        'aovs': 'albedo:albedo,sh_normal:sh_normal',
        'img': {
            'type': 'path',
            'max_depth' : 6,
        }
    })
    mi.render(scene, spp=2, integrator=integrator, sensor=sensor)
    multichannel = sensor.film().bitmap()

    denoiser = mi.OptixDenoiser(multichannel.size(), True, True)
    denoised = denoiser(multichannel, False, "albedo", "sh_normal", sensor.world_transform().inverse())
    denoised = mi.TensorXf(denoised.convert(component_format=mi.Struct.Type.Float16))

    ref_tensor = mi.TensorXf(ref)[...,:3]
    denoised_tensor = mi.TensorXf(denoised)

    ref_array = ref_tensor.array
    denoised_array = denoised_tensor.array

    assert dr.allclose(denoised_array, ref_array)
