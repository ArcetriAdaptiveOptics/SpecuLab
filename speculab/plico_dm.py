from specula.base_processing_obj import BaseProcessingObj
from specula.base_value import BaseValue
from specula.data_objects.ifunc import IFunc
from specula.data_objects.ifunc_inv import IFuncInv
from specula.data_objects.electric_field import ElectricField
from specula.connections import InputValue
from specula.data_objects.m2c import M2C
from specula import cpuArray

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
                 m2c= None,
                 ifunc: IFunc=None,
                 ifunc_inv: IFuncInv=None,
                 target_device_idx=None,
                 precision=None
                ):
        super().__init__(target_device_idx=target_device_idx, precision=precision)

        self.dm = plico_dm.deformableMirror(host, port)
        self.m2c = m2c
        self.ifunc = ifunc
        self.ifunc_inv = ifunc_inv
        self.inputs['in_commands'] = InputValue(type=BaseValue, optional=True)
        self.inputs['in_ef'] = InputValue(type=BaseValue, optional=True)

    def trigger_code(self):
        in_commands = self.local_inputs['in_commands']
        if in_commands:
            commands = in_commands.value
            if self.m2c is not None:
                commands = self.m2c @ commands
            self.dm.set_shape(cpuArray(commands))
        else:
            ef = self.local_inputs['in_ef']
            commands = ef.phaseInNm @ self.ifunc_ivn
            self.dm.set_shape(commands)

    def setup(self):
        cmd = self.inputs['in_commands'].get(self.target_device_idx)
        ef = self.inputs['in_ef'].get(self.target_device_idx)
        if cmd and ef:
            raise ValueError('Only one of the two inputs "in_commands" and "in_ef" can be connected')

        if ef:
            if self.ifunc is None and self.ifunc_inv is None:
                raise ValueError('One of "ifunc" and "ifunc_inv" parameters is mandatory when the EF input is connected')
            if self.ifunc_inv is None:
                self.ifunc_inv = self.ifunv.inverse()
