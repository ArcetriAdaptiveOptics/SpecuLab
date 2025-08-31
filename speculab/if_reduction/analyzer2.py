


from pipeline import list_all_files, cube_diff, smooth_image, apply_mask, crop_and_resize, threshold, stack_images


from pipeline_lib import run_pipeline

funcs = [list_all_files, cube_diff, apply_mask, smooth_image, threshold, crop_and_resize, stack_images]
params_lists = [['/home/puglisi/cascading/alpao820if/20250829_150620*/wavefront.fits'], [], [], [], [], [512, 512], []]

run_pipeline(funcs, params_lists, preview=True)