# Copyright 2020-2022 Huawei Technologies Co., Ltd
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

"""train bert network without lossscale"""

import os
import time
import numpy as np
import mindspore.common.dtype as mstype
import mindspore.dataset as ds
import mindspore.dataset.transforms as C
import mindspore
from mindspore import log as logger
from mindspore.ops import operations as P
from mindspore.common.tensor import Tensor
from mindspore.nn.optim import Lamb
from mindspore.train.loss_scale_manager import DynamicLossScaleManager
from mindspore.train import Model, Callback
import mindspore.nn.learning_rate_schedule as lr_schedules
from tests.st.networks import utils

head_path = os.path.dirname(os.path.abspath(__file__)) + "/../../../../../../"
utils.replace_check_param(head_path)

from tests.mark_utils import arg_mark
from tests.models.official.nlp.bert.src.bert_for_pre_training import BertNetworkWithLoss
from tests.models.official.nlp.bert.src.bert_for_pre_training import BertTrainOneStepWithLossScaleCell
from tests.models.official.nlp.bert.src.bert_model import BertConfig

_current_dir = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = ["/home/workspace/mindspore_dataset/bert/example/examples.tfrecord"]
SCHEMA_DIR = "/home/workspace/mindspore_dataset/bert/example/datasetSchema.json"

def get_config(version='base'):
    """get config"""
    if version == 'base':
        bert_config = BertConfig(
            seq_length=128,
            vocab_size=21136,
            hidden_size=768,
            num_hidden_layers=2,
            num_attention_heads=12,
            intermediate_size=3072,
            hidden_act="gelu",
            hidden_dropout_prob=0.1,
            attention_probs_dropout_prob=0.1,
            max_position_embeddings=512,
            type_vocab_size=2,
            initializer_range=0.02,
            use_relative_positions=True,
            dtype=mstype.float32,
            compute_type=mstype.float32)
    elif version == 'large':
        bert_config = BertConfig(
            seq_length=128,
            vocab_size=21136,
            hidden_size=1024,
            num_hidden_layers=2,
            num_attention_heads=16,
            intermediate_size=4096,
            hidden_act="gelu",
            hidden_dropout_prob=0.0,
            attention_probs_dropout_prob=0.0,
            max_position_embeddings=512,
            type_vocab_size=2,
            initializer_range=0.02,
            use_relative_positions=False,
            dtype=mstype.float32,
            compute_type=mstype.float16)
    else:
        bert_config = BertConfig()
    return bert_config


def me_de_train_dataset(sink_mode=False):
    """test me de train dataset"""
    # apply repeat operations
    repeat_count = 1
    sink_size = -1
    batch_size = 16
    data_set = ds.TFRecordDataset(DATA_DIR, SCHEMA_DIR, columns_list=["input_ids", "input_mask", "segment_ids",
                                                                      "next_sentence_labels", "masked_lm_positions",
                                                                      "masked_lm_ids", "masked_lm_weights"],
                                  shuffle=False)
    type_cast_op = C.TypeCast(mstype.int32)
    new_repeat_count = repeat_count
    if sink_mode:
        sink_size = 100
        new_repeat_count = 3
    data_set = data_set.map(operations=type_cast_op, input_columns="masked_lm_ids")
    data_set = data_set.map(operations=type_cast_op, input_columns="masked_lm_positions")
    data_set = data_set.map(operations=type_cast_op, input_columns="next_sentence_labels")
    data_set = data_set.map(operations=type_cast_op, input_columns="segment_ids")
    data_set = data_set.map(operations=type_cast_op, input_columns="input_mask")
    data_set = data_set.map(operations=type_cast_op, input_columns="input_ids")
    # apply batch operations
    data_set = data_set.batch(batch_size, drop_remainder=True)
    logger.info("data size: {}".format(data_set.get_dataset_size()))
    logger.info("repeat_count: {}".format(data_set.get_repeat_count()))
    return data_set, new_repeat_count, sink_size


def weight_variable(shape):
    """weight variable"""
    np.random.seed(1)
    ones = np.random.uniform(-0.1, 0.1, size=shape).astype(np.float32)
    return Tensor(ones)


class BertLearningRate(lr_schedules.LearningRateSchedule):
    def __init__(self, learning_rate, end_learning_rate, warmup_steps, decay_steps, power):
        super(BertLearningRate, self).__init__()
        self.warmup_flag = False
        if warmup_steps > 0:
            self.warmup_flag = True
            self.warmup_lr = lr_schedules.WarmUpLR(learning_rate, warmup_steps)
        self.decay_lr = lr_schedules.PolynomialDecayLR(learning_rate, end_learning_rate, decay_steps, power)
        self.warmup_steps = Tensor(np.array([warmup_steps]).astype(np.float32))

        self.greater = P.Greater()
        self.one = Tensor(np.array([1.0]).astype(np.float32))
        self.cast = P.Cast()

    def construct(self, global_step):
        decay_lr = self.decay_lr(global_step)
        if self.warmup_flag:
            is_warmup = self.cast(self.greater(self.warmup_steps, global_step), mstype.float32)
            warmup_lr = self.warmup_lr(global_step)
            lr = (self.one - is_warmup) * decay_lr + is_warmup * warmup_lr
        else:
            lr = decay_lr
        return lr


class ModelCallback(Callback):
    def __init__(self):
        super(ModelCallback, self).__init__()
        self.loss_list = []
        self.overflow_list = []
        self.lossscale_list = []

    def step_end(self, run_context):
        cb_params = run_context.original_args()
        self.loss_list.append(cb_params.net_outputs[0].asnumpy()[0])
        self.overflow_list.append(cb_params.net_outputs[1].asnumpy())
        self.lossscale_list.append(cb_params.net_outputs[2].asnumpy())
        print("epoch: {}, outputs are: {}".format(cb_params.cur_epoch_num, str(cb_params.net_outputs)))


class TimeMonitor(Callback):
    """Time Monitor."""

    def __init__(self, data_size):
        super(TimeMonitor, self).__init__()
        self.data_size = data_size
        self.epoch_mseconds_list = []
        self.per_step_mseconds_list = []

    def epoch_begin(self, run_context):
        self.epoch_time = time.time()

    def epoch_end(self, run_context):
        epoch_mseconds = (time.time() - self.epoch_time) * 1000
        self.epoch_mseconds_list.append(epoch_mseconds)
        self.per_step_mseconds_list.append(epoch_mseconds / self.data_size)


def test_bert_precision(enable_graph_kernel=False):
    """test bert precision"""
    mindspore.set_context(mode=mindspore.GRAPH_MODE, device_target="Ascend",
                          reserve_class_name_in_scope=False, deterministic='ON')
    mindspore.set_context(jit_level="O2")
    if enable_graph_kernel:
        mindspore.set_context(enable_graph_kernel=True)
    data_set, new_repeat_count, _ = me_de_train_dataset()
    version = os.getenv('VERSION', 'large')
    config = get_config(version=version)
    netwithloss = BertNetworkWithLoss(config, True)
    lr = BertLearningRate(decay_steps=data_set.get_dataset_size() * new_repeat_count,
                          learning_rate=5e-5, end_learning_rate=1e-9,
                          power=10.0, warmup_steps=0)
    decay_filter = lambda x: 'layernorm' not in x.name.lower() and 'bias' not in x.name.lower()
    no_decay_filter = lambda x: 'layernorm' in x.name.lower() or 'bias' in x.name.lower()
    decay_params = list(filter(decay_filter, netwithloss.trainable_params()))
    other_params = list(filter(no_decay_filter, netwithloss.trainable_params()))
    group_params = [{'params': decay_params, 'weight_decay': 0.01},
                    {'params': other_params},
                    {'order_params': netwithloss.trainable_params()}]
    optimizer = Lamb(group_params, lr)
    scale_window = 3
    scale_manager = DynamicLossScaleManager(2 ** 16, 2, scale_window)
    netwithgrads = BertTrainOneStepWithLossScaleCell(netwithloss, optimizer=optimizer,
                                                     scale_update_cell=scale_manager.get_update_cell())
    netwithgrads.set_train(True)
    model = Model(netwithgrads)
    callback = ModelCallback()
    params = netwithloss.trainable_params()
    for param in params:
        value = param.data
        name = param.name
        if isinstance(value, Tensor):
            if name.split('.')[-1] in ['weight']:
                if name.split('.')[-3] in ['cls2']:
                    logger.info("***************** BERT param name is 1 {}".format(name))
                    param.set_data(weight_variable(value.asnumpy().shape))
                else:
                    logger.info("***************** BERT param name is 2 {}".format(name))
                    tempshape = value.asnumpy().shape
                    shape = (tempshape[1], tempshape[0])
                    weight_value = weight_variable(shape).asnumpy()
                    param.set_data(Tensor(np.transpose(weight_value, [1, 0])))
            else:
                logger.info("***************** BERT param name is 3 {}".format(name))
                param.set_data(weight_variable(value.asnumpy().shape))
    model.train(new_repeat_count, data_set, callbacks=callback, dataset_sink_mode=False)

    # assertion occurs while the loss value, overflow state or loss_scale value is wrong
    loss_value = np.array(callback.loss_list)

    if enable_graph_kernel:
        expect_loss_value = [12.206627, 11.840489, 11.798470, 11.796345, 11.790964, 12.366766, 11.971539, 12.576565,
                             12.185522, 12.386192]
    else:
        assert np.allclose(loss_value[0], 12.2072, 0, 0.0005)
        expect_loss_value = [12.2072, 11.941728, 11.931803, 11.93857, 11.931982, 12.556978, 12.131189, 12.784796,
                             12.360739, 12.57966]
    print("loss value: {}".format(loss_value))
    assert np.allclose(loss_value, expect_loss_value, 0, 0.0005)


@arg_mark(plat_marks=['platform_ascend'], level_mark='level1', card_mark='onecard', essential_mark='unessential')
def test_bert_precision_graph_kernel_off():
    test_bert_precision(enable_graph_kernel=False)


if __name__ == '__main__':
    test_bert_precision(enable_graph_kernel=False)
