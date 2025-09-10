from specula.base_processing_obj import BaseProcessingObj
from specula.base_value import BaseValue
from specula.connections import InputValue

import plico_motor


class PlicoMotor(BaseProcessingObj):
    '''
    Interface to Plico Motor.

    Can be used to drive a motor, or to read its position, or both
    '''

    def __init__(self,
                 host: str,
                 port: int,
                 axis: int,
                 target_device_idx=None,
                 precision=None
                ):
        super().__init__(target_device_idx=target_device_idx, precision=precision)

        self.motor = plico_motor.motor(host, port, axis)
        self.inputs['in_position'] = InputValue(type=BaseValue, optional=True)
        self.outputs['out_position'] = BaseValue(description='Motor position', target_device_idx=target_device_idx)

    def trigger_code(self):
        target_pos = self.local_inputs['in_position'].value
        if target_pos is not None:
            self.motor.move_to(target_pos)

        curpos = self.motor.position()
        self.outputs['out_position'].value = curpos

    def post_trigger(self):
        self.outputs['out_position'].generation_time = self.current_time


