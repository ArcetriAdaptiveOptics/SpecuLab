from specula.base_processing_obj import BaseProcessingObj
from specula.base_value import BaseValue
from specula.connections import InputValue

import plico_dm


class PlicoDM(BaseProcessingObj):
    '''Interface to Plico DM'''

    def __init__(self,
                 host: str,
                 port: int,
                 target_device_idx=None,
                 precision=None
                ):
        super().__init__(target_device_idx=target_device_idx, precision=precision)

        self.dm = plico_dm.deformableMirror(host, port)
        self.inputs['in_commands'] = InputValue(type=BaseValue)

    def trigger_code(self):
        commands = self.local_inputs['in_commands']
        self.dm.set_shape(commands)


