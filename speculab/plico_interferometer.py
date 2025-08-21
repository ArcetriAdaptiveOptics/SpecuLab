from specula.base_processing_obj import BaseProcessingObj
from specula.base_value import BaseValue

import plico_interferometer


class PlicoInterferometer(BaseProcessingObj):
    '''Interface to Plico Interferometer'''

    def __init__(self,
                 host: str,
                 port: int,
                 target_device_idx=None,
                 precision=None
                ):
        super().__init__(target_device_idx=target_device_idx, precision=precision)

        self.interf = plico_interferometer.interferometer(host, port)
        self.outputs['out_wavefront'] = BaseValue(desc='wavefront', target_device_idx=target_device_idx)

    def trigger_code(self):
        wf = self.interf.wavefront()
        self.outputs.value = wf

    def post_trigger(self):
        self.outputs.generation_time = self.current_time


