from specula.base_processing_obj import BaseProcessingObj
from specula.data_objects.pixels import Pixels

import pysilico


class PysilicoCamera(BaseProcessingObj):
    '''
    Interface to a Pysilico camera
    '''
    def __init__(self,
                 host: str,
                 port: int,
                 target_device_idx=None,
                 precision=None
                ):
        super().__init__(target_device_idx=target_device_idx, precision=precision)

        self.camera = pysilico.camera(host, port)
        frame = self.camera.getFutureFrames(1).toNumpyArray()
        self.outputs['out_pixels'] = Pixels(frame.shape[1], frame.shape[0],
                                            target_device_idx=target_device_idx)

    def trigger_code(self):
        frame = self.camera.getFutureFrames(1)
        self.outputs['out_pixels'].pixels[:] = frame.toNumpyArray()

