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

#ifndef MINDSPORE_LITE_TOOLS_CONVERTER_MICRO_CODER_OPCODERS_NNACL_DYNAMIC_PARAMETER_SCALE_DYNAMIC_PARAMETER_H_
#define MINDSPORE_LITE_TOOLS_CONVERTER_MICRO_CODER_OPCODERS_NNACL_DYNAMIC_PARAMETER_SCALE_DYNAMIC_PARAMETER_H_
#include <string>

typedef struct ScaleDynamicParameter {
  std::string outer_size_;
  std::string axis_size_;
  std::string inner_size_;
} ScaleDynamicParameter;
#endif  // MINDSPORE_LITE_TOOLS_CONVERTER_MICRO_CODER_OPCODERS_NNACL_DYNAMIC_PARAMETER_SCALE_DYNAMIC_PARAMETER_H_
