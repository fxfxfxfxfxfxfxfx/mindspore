# Copyright 2022 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
from tests.mark_utils import arg_mark

import numpy as np
import pytest
import mindspore.context as context
import mindspore.nn as nn
import mindspore.ops.operations as P
from mindspore import Tensor


class SoftsignNet(nn.Cell):
    def __init__(self):
        super(SoftsignNet, self).__init__()
        self.softsign = P.Softsign()

    def construct(self, x):
        return self.softsign(x)


def softsign_compute(x):
    return x / (np.abs(x) + 1.)


@arg_mark(plat_marks=['platform_gpu'], level_mark='level1', card_mark='onecard', essential_mark='unessential')
@pytest.mark.parametrize('dtype, tol', [(np.float16, 1e-3), (np.float32, 1e-4), (np.float64, 1e-5)])
def test_softsign_net(dtype, tol):
    """
    Feature: Softsign
    Description:  test cases for Softsign operator.
    Expectation: match to np benchmark.
    """
    context.set_context(mode=context.PYNATIVE_MODE, device_target='GPU')
    x = np.array([[[[1.7641, 0.4002, 0.9787],
                    [2.2409, 1.8676, -0.9773]],
                   [[0.9501, -0.1514, -0.1032],
                    [0.4106, 0.1440, 1.4543]]],
                  [[[0.7610, 0.1217, 0.4439],
                    [0.3337, 1.4941, -0.2052]],
                   [[0.3131, -0.8541, -2.5530],
                    [0.6536, 0.8644, -0.7422]]]]).astype(dtype)
    net = SoftsignNet()
    ms_result = net(Tensor(x))
    np_result = softsign_compute(x)
    assert np.allclose(ms_result.asnumpy(), np_result, atol=tol, rtol=tol)
