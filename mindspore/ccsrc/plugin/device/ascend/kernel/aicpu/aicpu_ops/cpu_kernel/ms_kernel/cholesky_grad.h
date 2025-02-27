/**
 * Copyright 2021 Huawei Technologies Co., Ltd
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

#ifndef AICPU_KERNELS_NORMALIZED_CHOLESKY_GRAD_H_
#define AICPU_KERNELS_NORMALIZED_CHOLESKY_GRAD_H_

#include <Eigen/Dense>
#include <unsupported/Eigen/MatrixFunctions>

#include "inc/ms_cpu_kernel.h"
#include "cpu_types.h"
#include "utils/bcast.h"
#include "utils/eigen_tensor.h"
#include "utils/kernel_util.h"

namespace aicpu {
class CholeskyGradCpuKernel : public CpuKernel {
 public:
  CholeskyGradCpuKernel() = default;
  ~CholeskyGradCpuKernel() override = default;

 protected:
  uint32_t Compute(CpuKernelContext &ctx) override;

 private:
  template <typename T>
  uint32_t ComputeKernel(CpuKernelContext &ctx, const bool &reverse);

  template <typename T>
  void ComputeMatrix(T *lptr, T *gradptr, T *outputptr, int64_t n);

  template <typename T>
  void CholeskyGradUnblocked(
    const Eigen::Ref<const Eigen::Matrix<T, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>> &l_block,
    Eigen::Ref<Eigen::Matrix<T, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>> grad_block);
};
}  // namespace aicpu
#endif
