
from specula.base_value import BaseValue
from specula.base_processing_obj import BaseProcessingObj
from specula.data_objects.pixels import Pixels
from specula.connections import InputValue

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
        self.outputs['out_pixels'] = Pixels(100, 100, target_device_idx=target_device_idx)
        self.inputs['in_trigger'] = InputValue(type=BaseValue, optional=True)
        self.has_trigger = False
        self.triggered = False
        # frame = self.camera.getFutureFrames(1).toNumpyArray()
        # self.outputs['out_pixels'] = Pixels(frame.shape[1], frame.shape[0],
        #                                     target_device_idx=target_device_idx)

    def prepare_trigger(self):
        super().prepare_trigger()
        self.triggered = False

    def trigger_code(self):
        if self.has_trigger:
            trigger = self.local_inputs['in_trigger'].value
            trigger_time = self.local_inputs['in_trigger'].generation_time
            if trigger and trigger_time == self.current_time:
                frame = self.camera.getFutureFrames(1)
                self.outputs['out_pixels'].pixels[:] = frame.toNumpyArray()
                self.triggered = True
            return
        frame = self.camera.getFutureFrames(1)
        self.outputs['out_pixels'].pixels[:] = frame.toNumpyArray()

    def post_trigger(self):
        super().post_trigger()
        if self.triggered or not self.has_trigger:
            self.outputs['out_pixels'].generation_time = self.current_time

    def setup(self):
        super().setup()
        self.has_trigger = self.local_inputs['in_trigger'] is not None