# Copyright 2023 Huawei Technologies Co., Ltd
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

import mindspore as ms
from mindspore import Tensor, nn
import mindspore.ops.function as F


class Net(nn.Cell):
    def construct(self, x, y, z):
        return F.movedim(x, source=y, destination=z)


@arg_mark(plat_marks=['platform_ascend', 'platform_gpu', 'cpu_linux', 'cpu_windows', 'cpu_macos'], level_mark='level2', card_mark='onecard', essential_mark='unessential')
@pytest.mark.parametrize('mode', [ms.GRAPH_MODE, ms.PYNATIVE_MODE])
def test_net(mode):
    """
    Feature: test movdim op
    Description: verify the result of movdim
    Expectation: assertion success
    """
    ms.set_context(mode=mode)
    x = Tensor(np.array([[[-0.3362], [-0.8437]], [[-0.9627], [0.1727]], [[0.5173], [-0.1398]]]), ms.float32)
    movedim = Net()
    output = movedim(x, 1, 0)
    np_out = np.array([[[-0.3362], [-0.9627], [0.5173]], [[-0.8437], [0.1727], [-0.1398]]])
    assert np.allclose(output.asnumpy(), np_out)
