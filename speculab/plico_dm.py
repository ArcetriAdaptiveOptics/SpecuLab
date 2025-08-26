from specula.base_processing_obj import BaseProcessingObj
from specula.base_value import BaseValue
from specula.connections import InputValue
from specula.data_objects.m2c import M2C

import plico_dm


class PlicoDM(BaseProcessingObj):
    '''Interface to Plico DM'''

    def __init__(self,
                 host: str,
                 port: int,
                 m2c= None,
                 target_device_idx=None,
                 precision=None
                ):
        super().__init__(target_device_idx=target_device_idx, precision=precision)

        self.dm = plico_dm.deformableMirror(host, port)
        self.m2c = m2c
        self.inputs['in_commands'] = InputValue(type=BaseValue)

    def trigger_code(self):
        commands = self.local_inputs['in_commands'].value
        if self.m2c is not None:
            commands = self.m2c @ commands
        self.dm.set_shape(commands)


