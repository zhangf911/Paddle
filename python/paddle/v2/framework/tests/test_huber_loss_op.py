import unittest
import numpy as np
from op_test import OpTest


def huber_loss_forward(val, delta):
    abs_val = abs(val)
    if abs_val <= delta:
        return 0.5 * val * val
    else:
        return delta * (abs_val - 0.5 * delta)


class TestHuberLossOp(OpTest):
    def setUp(self):
        self.op_type = 'huber_loss'
        samples_num = 64
        delta = 1.0
        self.inputs = {
            'X': np.random.uniform(0, 1., (samples_num, 1)).astype('float32'),
            'Y': np.random.uniform(0, 1., (samples_num, 1)).astype('float32'),
        }
        residual = self.inputs['Y'] - self.inputs['X']
        loss = np.vectorize(huber_loss_forward)(residual, delta)
        self.attrs = {'delta': delta}
        self.outputs = {
            'Residual': residual,
            'Out': loss.reshape((samples_num, 1))
        }

    def test_check_output(self):
        self.check_output()

    def test_check_grad_normal(self):
        self.check_grad(['X', 'Y'], 'Out', max_relative_error=0.008)

    def test_check_grad_ingore_x(self):
        self.check_grad(
            ['Y'], 'Out', max_relative_error=0.008, no_grad_set=set("residual"))

    def test_check_grad_ingore_y(self):
        self.check_grad(
            ['X'], 'Out', max_relative_error=0.008, no_grad_set=set('residual'))


# TODO(typhoonzero): should add this back till we fix it
#if __name__ == '__main__':
#    unittest.main()
