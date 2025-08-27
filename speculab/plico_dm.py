from specula.base_processing_obj import BaseProcessingObj
from specula.base_value import BaseValue
from specula.data_objects.ifunc import IFunc
from specula.data_objects.ifunc_inv import IFuncInv
from specula.data_objects.electric_field import ElectricField
from specula.connections import InputValue

import plico_dm


class PlicoDM(BaseProcessingObj):
    '''Interface to Plico DM

    If the "in_commands" input is used, commands are sent directly to plico.
    Otherwise, the "in_ef" wavefront input is multiplied by the inverse ifunc
    to obtain the commands.
    The inverse ifunc can be passed directly, or if an ifunc is provided,
    it will be inverted during setup().
    '''
    def __init__(self,
                 host: str,
                 port: int,
                 ifunc: IFunc=None,
                 ifunc_inv: IFuncInv=None,
                 target_device_idx=None,
                 precision=None
                ):
        super().__init__(target_device_idx=target_device_idx, precision=precision)

        self.dm = plico_dm.deformableMirror(host, port)
        self.ifunc = ifunc
        self.ifunc_inv = ifunc_inv
        self.inputs['in_commands'] = InputValue(type=BaseValue)
        self.inputs['in_ef'] = InputValue(type=BaseValue)

    def trigger_code(self):
        commands = self.local_inputs['in_commands']
        ef = self.local_inputs['in_ef']
        if commands:
            self.dm.set_shape(commands)
        else:
            commands = ef.phaseInNm @ self.ifunc_ivn
            self.dm.set_shape(commands)

    def setup(self):
        if self.local_inputs['in_commands'] and self.local_inputs['in_ef']:
            raise ValueError('Only one of the two inputs "in_commands" and "in_ef" can be connected')

        if self.local_inputs['in_ef']:
            if self.ifunc is None and self.ifunc_inv is None:
                raise ValueError('One of "ifunc" and "ifunc_inv" parameters is mandatory when the EF input is connected')
            if self.ifunc_inv is None:
                self.ifunc_inv = self.ifunv.inverse()
