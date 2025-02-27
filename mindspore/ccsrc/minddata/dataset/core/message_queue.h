/**
 * Copyright 2024 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef MINDSPORE_CCSRC_MINDDATA_DATASET_CORE_MESSAGE_QUEUE_H_
#define MINDSPORE_CCSRC_MINDDATA_DATASET_CORE_MESSAGE_QUEUE_H_

#include <memory>
#include <utility>
#include <vector>
#if !defined(BUILD_LITE) && !defined(_WIN32) && !defined(_WIN64) && !defined(__ANDROID__) && !defined(ANDROID)
#include <unistd.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>
#include <sys/ipc.h>
#include <sys/msg.h>
#include <stdlib.h>
#include <sys/shm.h>
#endif

#include "include/api/status.h"
#include "minddata/dataset/include/dataset/constants.h"
#include "minddata/dataset/core/data_type.h"
#include "minddata/dataset/util/status.h"

namespace mindspore {
namespace dataset {
#if !defined(BUILD_LITE) && !defined(_WIN32) && !defined(_WIN64) && !defined(__ANDROID__) && !defined(ANDROID)

const int kMsgQueuePermission = 0600;
const int kMsgQueueClosed = 2;

const int kWorkerSendDataMsg = 777;
const int kMasterSendDataMsg = 999;

class DATASET_API MessageQueue {
 public:
  enum State {
    kInit = 0,
    kRunning = 1,
    kReleased,
  };

  MessageQueue(key_t key, int msg_queue_id);

  ~MessageQueue();

  void SetReleaseFlag(bool flag);

  Status GetOrCreateMessageQueueID();

  Status MsgSnd(int64_t mtype, int shm_id = 0, uint64_t shm_size = 0);

  Status MsgRcv(int64_t mtype);

  // the below is the message content
  int64_t mtype_;      // the message type
  int shm_id_;         // the shm id
  uint64_t shm_size_;  // the shm size

  key_t key_;          // message key
  int msg_queue_id_;   // the msg queue id
  bool release_flag_;  // whether release the msg_queue_id_ when ~MessageQueue
  State state_;        // whether the msg_queue_id_ had been released
};
#endif
}  // namespace dataset
}  // namespace mindspore
#endif  // MINDSPORE_CCSRC_MINDDATA_DATASET_CORE_MESSAGE_QUEUE_H_
