from specula.base_processing_obj import BaseProcessingObj
from specula.base_value import BaseValue
from specula.data_objects.slopes import Slopes
from specula.connections import InputValue

import plico_interferometer


class PlicoInterferometer(BaseProcessingObj):
    '''Interface to Plico Interferometer'''

    def __init__(self,
                 host: str,
                 port: int,
                 use_4sight_client: bool=False,
                 target_device_idx=None,
                 precision=None
                ):
        super().__init__(target_device_idx=target_device_idx, precision=precision)

        if use_4sight_client:
            self.interf = plico_interferometer.interferometer_4SightFocus_client(host, port)
        else:
            self.interf = plico_interferometer.interferometer(host, port)
        self.outputs['out_wavefront'] = BaseValue(description='wavefront', target_device_idx=target_device_idx)
        self.outputs['out_slopes'] = Slopes(2, target_device_idx=target_device_idx)
        self.inputs['in_trigger'] = InputValue(type=BaseValue)

    def trigger_code(self):
        trigger = self.local_inputs['in_trigger'].value
        if trigger:
            wf = self.interf.wavefront()
            self.outputs['out_wavefront'].value = wf

            data1d = wf.filled(0).ravel()
            self.outputs['out_slopes'].resize(len(data1d))
            print(wf.shape, data1d.shape)
            self.outputs['out_slopes'].slopes = data1d

    def post_trigger(self):
        trigger = self.local_inputs['in_trigger'].value
        if trigger:
            self.outputs['out_wavefront'].generation_time = self.current_time
            self.outputs['out_slopes'].generation_time = self.current_time

