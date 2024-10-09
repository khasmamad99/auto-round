# Copyright (c) 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import copy
import time
from typing import Optional, Union
import os
import glob
import io
import shutil

import torch
import transformers
from torch import autocast
import pandas as pd

import wandb
import lm_eval

from .calib_dataset import get_dataloader
from .quantizer import WrapperMultiblock, wrapper_block, unwrapper_block, WrapperLinear, unwrapper_layer
from .special_model_handler import check_hidden_state_dim, check_share_attention_mask, check_not_share_position_ids
from .utils import (
    CpuInfo,
    block_forward,
    check_is_cpu,
    check_to_quantized,
    collect_minmax_scale,
    collect_round_v,
    convert_dtype_str2torch,
    detect_device,
    get_block_names,
    get_module,
    htcore,
    is_optimum_habana_available,
    logger,
    sampling_inputs,
    to_device,
    to_dtype,
    get_layer_names_in_block,
    mv_module_from_gpu,
    format_layer_name,
)

from .low_cpu_mem.utils import get_layers_before_block
from .learning_curve_stats_utils import (
    calculate_convergence_iter, 
    calculate_average_absolute_change, 
    calculate_slope, 
    plot_learning_curve,
    make_pandas_dataframe_from_lm_eval_results,
)

from auto_round import evaluate_all


def get_block_indices(
    nblocks: int, 
    num_lookahead_blocks: int,
    num_observe_blocks: int, 
    block_step_size: int, 
    total_num_blocks: int
):
    # Input validation
    assert 1 <= nblocks <= total_num_blocks, "nblocks must be between 1 and total_num_blocks."
    assert 1 <= block_step_size <= nblocks, "block_step_size must be between 1 and nblocks."
    assert 0 <= num_lookahead_blocks <= total_num_blocks - 1, "num_lookahead_blocks must be between 0 and total_num_blocks - 1."
    
    def _get_block_indices(start_block_idx, num_fine_tune_blocks, num_lookahead_blocks, num_observe_blocks, total_num_blocks):
        fine_tune_block_start_idx = start_block_idx
        fine_tune_block_end_idx = min(start_block_idx + num_fine_tune_blocks, total_num_blocks)
        fine_tune_block_indices = slice(fine_tune_block_start_idx, fine_tune_block_end_idx)
        attach_loss_block_start_idx = fine_tune_block_end_idx
        attach_loss_block_end_idx = min(fine_tune_block_end_idx + num_lookahead_blocks, total_num_blocks)
        attach_loss_block_indices = slice(attach_loss_block_start_idx, attach_loss_block_end_idx)
        observe_block_start_idx = attach_loss_block_end_idx
        observe_block_end_idx = min(attach_loss_block_end_idx + num_observe_blocks, total_num_blocks)
        observe_block_indices = slice(observe_block_start_idx, observe_block_end_idx)
        return fine_tune_block_indices, attach_loss_block_indices, observe_block_indices
    
    for start_block_idx in range(0, total_num_blocks, block_step_size):
        if start_block_idx == 0:
            for num_fine_tune_blocks in range(block_step_size, nblocks + 1, block_step_size):
                yield _get_block_indices(start_block_idx, num_fine_tune_blocks, num_lookahead_blocks, num_observe_blocks, total_num_blocks)
        else:
            num_fine_tune_blocks = nblocks
            yield _get_block_indices(start_block_idx, num_fine_tune_blocks, num_lookahead_blocks, num_observe_blocks, total_num_blocks)



class AutoRound(object):
    """This is Signround+ which is an advanced version of Signround. For more information,
     please refer to Cheng, Wenhua, et al. "Optimize weight rounding via signed gradient descent
     for the quantization of llms." arXiv preprint arXiv:2309.05516 (2023).

    Args:
        model: The PyTorch model to be quantized.
        tokenizer: An optional tokenizer for processing input data. If none is provided, a dataloader must be supplied.
        bits (int): Number of bits for quantization (default is 4).
        group_size (int): Size of the quantization group (default is 128).
        sym (bool): Whether symmetric quantization is to be used (default is False).
        layer_config (dict): Configuration for weight quantization (default is an empty dictionary).
        layer_config={
                   'layer1':##layer_name
                   {
                       'data_type': 'int',
                       'bits': 4,
                       'group_size': 128,
                       'sym': False
                       'act_data_type': None,
                       'act_bits': 32,
                       'group_size': None,
                       'sym': None,

                   }
                   ...
               }
        enable_full_range (bool): Whether to enable full range quantization (default is False).
        batch_size (int): Batch size for training (default is 8).
        amp (bool): Whether to use automatic mixed precision (default is True).
        device: The device to be used for tuning (default is "auto").
        lr_scheduler: The learning rate scheduler to be used.
        dataset (str): The default dataset name (default is "NeelNanda/pile-10k").
        enable_quanted_input (bool): Whether to use the output of the previous quantized block as
                                the input for the current block (default is True).
        enable_minmax_tuning (bool): Whether to enable weight min-max tuning (default is True).
        lr (float): The learning rate (default is None, will be set to 1.0/iters).
        minmax_lr (float): The learning rate for min-max tuning (default is None, it will be set to lr automatically).
        low_gpu_mem_usage (bool): Whether to use low GPU memory (default is True).
        low_cpu_mem_usage (bool): Whether to use low CPU memory (default is False).
        iters (int): Number of iterations (default is 200).
        seqlen (int): Data length of the sequence for tuning (default is 2048).
        nsamples (int): Number of samples (default is 128).
        sampler (str): The sampling method (default is "rand").
        seed (int): The random seed (default is 42).
        nblocks (int): Number of blocks (default is 1).
        num_lookahead_blocks (int): Number of lookahead blocks (default is 0).
        gradient_accumulate_steps (int): Number of gradient accumulation steps (default is 1).
        not_use_best_mse (bool): Whether to use mean squared error (default is False).
        dynamic_max_gap (int): The dynamic maximum gap (default is -1).
        data_type (str): The data type to be used (default is "int").
        scale_dtype (str): The data type of quantization scale to be used (default is "float16"), different kernels
                           have different choices.
        multimodal(bool): Enable multimodal model quantization, (default is "False").
        act_bits (int): Number of bits for activation quantization. Default is 32.
        act_group_size (int): Group size for activation quantization. Default is None.
        act_sym (bool): Whether to use symmetric activation quantization. Default is None.
        act_dynamic (bool): Whether to use dynamic activation quantization. Default is True.

    Returns:
        The quantized model.
    """

    def __init__(
            self,
            model,
            tokenizer,
            model_name: Optional[str] = None,
            bits: int = 4,
            group_size: int = 128,
            sym: bool = False,
            layer_config: dict = {},
            enable_full_range: bool = False,  ##for symmetric, TODO support later
            batch_size: int = 8,
            eval_batch_size: int = 4,
            amp: bool = True,
            device: str = None,
            lr_scheduler=None,
            dataset: Union[str, list, tuple, torch.utils.data.DataLoader] = "NeelNanda/pile-10k",
            round_to_nearest: bool = False,
            enable_quanted_input: bool = True,
            enable_minmax_tuning: bool = True,
            lr: float = None,
            minmax_lr: float = None,
            enable_lr_scheduler: bool = False,
            low_gpu_mem_usage: bool = False,
            low_cpu_mem_usage: bool = False,
            iters: int = 200,
            seqlen: int = 2048,
            nsamples: int = 128,
            sampler: str = "rand",
            seed: int = 42,
            lm_eval_random_seed: int = 0,
            lm_eval_numpy_random_seed: int = 1234,
            lm_eval_torch_random_seed: int = 1234,
            nblocks: int = 1,
            block_step_size: int = 1,
            num_lookahead_blocks: int = 0,
            num_observe_blocks: int = 0,
            eval_after_each_optimization: bool = False,
            eval_tasks: str = "",
            eval_seed: int = 0,
            model_save_dir: str = None,
            isolation_experiment_v2: bool = False,
            cleanly_separated_lookahead: bool = False,
            fine_tune_block_idx: int = 0,
            observe_block_idx: int = 0,
            attach_loss_block_indices: list[int] = [-1],
            gradient_accumulate_steps: int = 1,
            not_use_best_mse: bool = False,
            dynamic_max_gap: int = -1,
            data_type: str = "int",
            scale_dtype: str = "fp16",
            multimodal:bool = False,
            act_bits: int = 32,
            act_group_size: int = None,
            act_sym: bool = None,
            act_dynamic: bool = True,
            disable_wandb: bool = False,
            **kwargs,
    ):
        self.quantized = False
        self.model_orig_dtype = model.dtype
        self.low_cpu_mem_usage = low_cpu_mem_usage
        self.model = model.eval()
        self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
        self.model_name = model_name
        self.amp = amp
        self.round_to_nearest = round_to_nearest
        self.enable_quanted_input = enable_quanted_input
        self.enable_minmax_tuning = enable_minmax_tuning
        self.nsamples = nsamples
        self.nblocks = nblocks
        self.block_step_size = block_step_size
        self.num_lookahead_blocks = num_lookahead_blocks
        self.num_observe_blocks = num_observe_blocks
        self.eval_after_each_optimization = eval_after_each_optimization
        self.model_save_dir = model_save_dir
        self.eval_tasks = eval_tasks
        self.eval_seed = eval_seed
        self.cleanly_separated_lookahead = cleanly_separated_lookahead
        self.isolation_experiment_v2 = isolation_experiment_v2
        self.fine_tune_block_idx = fine_tune_block_idx
        self.observe_block_idx = observe_block_idx
        self.attach_loss_block_indices = attach_loss_block_indices
        self.bits = bits
        self.group_size = group_size
        self.sym = sym
        self.low_gpu_mem_usage = low_gpu_mem_usage
        self.data_type = data_type
        self.supported_types = [torch.nn.Linear, transformers.modeling_utils.Conv1D]
        self.layer_config = layer_config
        self.seed = seed
        self.lm_eval_random_seed = lm_eval_random_seed
        self.lm_eval_numpy_random_seed = lm_eval_numpy_random_seed
        self.lm_eval_torch_random_seed = lm_eval_torch_random_seed
        self.tokenizer = tokenizer
        self.seqlen = seqlen
        self.train_bs = batch_size
        self.eval_batch_size = eval_batch_size
        self.device = detect_device(device)
        self.scale_dtype = convert_dtype_str2torch(scale_dtype)
        self.set_amp_dtype()
        self.cache_device = torch.device("cpu") if self.low_gpu_mem_usage else self.device
        self.dataset = dataset

        self.iters = iters
        self.multimodal = multimodal
        if self.iters <= 0:
            logger.warning("iters must be positive, reset it to 200")
            self.iters = 200
        self.lr = lr or (1.0 / self.iters)
        self.minmax_lr = minmax_lr or self.lr
        self.enable_lr_scheduler = enable_lr_scheduler

        self.sampler = sampler
        self.gradient_accumulate_steps = gradient_accumulate_steps
        self.not_use_best_mse = not_use_best_mse
        self.dynamic_max_gap = dynamic_max_gap
        self.enable_full_range = enable_full_range
        self.lr_scheduler = lr_scheduler
        self.optimizer = self.get_optimizer(None)
        self.share_attention_mask_flag = None
        self.hidden_dim_flag = None
        self.infer_bs_coeff = 1
        self.act_group_size = act_group_size if not (act_group_size is None) else self.group_size
        self.act_bits = act_bits if not (act_bits is None) else self.bits
        self.act_sym = act_sym if not (act_sym is None) else self.sym
        self.act_dynamic = act_dynamic
        self.disable_wandb = disable_wandb
        
        self.set_layerwise_config(self.layer_config)
        torch.set_printoptions(precision=3, sci_mode=True)
        self.check_configs()
        logger.info(f"using {self.model.dtype} for quantization tuning")
        if is_optimum_habana_available():
            logger.info("Optimum Habana is available, import htcore explicitly.")
            import habana_frameworks.torch.core as htcore  # pylint: disable=E0401
            import habana_frameworks.torch.hpu as hthpu  # pylint: disable=E0401

    def check_configs(self):
        """Checks if the configurations are valid.

        Raises:
        AssertionError: If any of the configurations are invalid.
        """
        assert isinstance(self.model, torch.nn.Module)
        assert self.bits > 0, "bits must be positive"
        assert self.act_bits > 0, "bits must be positive"
        assert self.group_size == -1 or self.group_size >= 1, "only supports positive group_size or -1(per channel)"
        assert self.act_group_size == -1 or self.act_group_size >= 1,\
            "only supports positive group_size or -1(per channel)"
        if self.cleanly_separated_lookahead:
            assert self.num_lookahead_blocks > 0, "num_lookahead_blocks must be > 0 when cleanly_separated_lookahead is True"
        assert self.num_lookahead_blocks >= 0, "num_lookahead_blocks must be non-negative"
        assert self.num_observe_blocks >= 0, "num_observe_blocks must be non-negative"
        if self.eval_after_each_optimization:
            assert self.model_save_dir is not None, "model_save_dir must be provided when eval_after_each_optimization is True"
            assert self.eval_tasks != "", "eval_tasks must be provided when eval_after_each_optimization is True"
        assert self.fine_tune_block_idx <= self.observe_block_idx, (
            f"fine_tune_block_idx {self.fine_tune_block_idx} should be less than observe_block_idx {self.observe_block_idx}"
        )
        
        if -1 in self.attach_loss_block_indices:
            assert len(self.attach_loss_block_indices) == 1, "-1 should be the only element or should not be included in attach_loss_block_indices"
        elif any([i < 0 for i in self.attach_loss_block_indices]):
            assert False, "attach_loss_block_indices should be non-negative"
        elif any([i < self.fine_tune_block_idx or i > self.observe_block_idx for i in self.attach_loss_block_indices]):
            assert False, (
                f"attach_loss_block_indices should be in the range of fine_tune_block_idx {self.fine_tune_block_idx}"
                f" and observe_block_idx {self.observe_block_idx} (inclusive). Received {self.attach_loss_block_indices}."
            )
        
        assert self.train_bs > 0, "batch size must be positive"
        assert self.eval_batch_size > 0, "eval batch size must be positive"
        assert self.iters > 0, "iters must be positive"
        assert self.seqlen > 0, "seqlen must be positive"
        assert self.nblocks > 0, "nblocks must be positive"
        assert self.gradient_accumulate_steps > 0, "gradient accumulate step must be positive"
        assert self.enable_full_range is False, "only support enable_full_range=False currently"
        assert self.act_dynamic is True, "only support dynamic quantization for activation currently"
        # assert self.tokenizer != None or self.dataloader != None

    def quantize(self):
        """Quantize the model and return the quantized model along with layer configurations.
        the entry of AutoRound.

        Returns:
        The quantized model and layer configurations.
        """
        # logger.info("cache block input")
        all_blocks = get_block_names(self.model, self.multimodal)
                    
        if len(all_blocks) == 0:
            logger.warning("could not find blocks, exit with original model")
            return self.model, self.layer_config

        if self.amp:
            self.model = self.model.to(self.amp_dtype)

        layer_names = self.get_quantized_layer_names_outside_blocks()
        self.start_time = time.time()
        
        if self.round_to_nearest:
            logger.info("Round To Nearest - Quantizing the model using Round To Nearest")
            for block_name in all_blocks[0]:
                block = get_module(self.model, block_name)
                quantized_layer_names, unquantized_layer_names = wrapper_block(
                    block=block, 
                    enable_minmax_tuning=self.enable_minmax_tuning,
                    device=self.device,
                )
                
                dump_info = (
                    f"{block_name}: quantized {len(quantized_layer_names)}/{(len(quantized_layer_names) + len(unquantized_layer_names))} "
                    f"layers in the block with RTE."
                )
                logger.info(dump_info)
                if len(unquantized_layer_names) != 0:
                    logger.info(f"{unquantized_layer_names} have not been quantized")
                
                unwrapper_block(
                    block=block,
                    vs=0,
                    min_scales=torch.tensor(1.0, device=self.device, dtype=torch.float32),
                    max_scales=torch.tensor(1.0, device=self.device, dtype=torch.float32),
                )
                self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
                torch.cuda.empty_cache()
        else:
            all_first_block_names = [block[0] for block in all_blocks]
            all_inputs = self.try_cache_inter_data_gpucpu(all_first_block_names, self.nsamples, layer_names=layer_names)
            for block_names in all_blocks:
                inputs = all_inputs[block_names[0]]
                all_inputs.pop(block_names[0])
                self.inputs = None
                del self.inputs
                if "input_ids" in inputs.keys():
                    total_samples = len(inputs["input_ids"])
                    self.n_samples = total_samples
                    if total_samples < self.train_bs:
                        self.train_bs = total_samples
                        logger.warning(f"force the train batch size to {total_samples} ")

            self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
            torch.cuda.empty_cache()
            
            if not self.isolation_experiment_v2:
                self.quant_blocks(
                    self.model,
                    inputs,
                    block_names,
                    nblocks=self.nblocks,
                    block_step_size=self.block_step_size,
                    num_lookahead_blocks=self.num_lookahead_blocks,
                    num_observe_blocks=self.num_observe_blocks,
                    device=self.device,
                )
            else:
                self.quant_blocks_isolation_experiment_v2(
                    self.model,
                    inputs,
                    block_names,
                    fine_tune_block_idx=self.fine_tune_block_idx,
                    observe_block_idx=self.observe_block_idx,
                    attach_loss_block_indices=self.attach_loss_block_indices,
                    device=self.device,
            )

            self.quant_layers(layer_names, all_inputs)

        self.dump_qinfo_to_layer_config()

        end_time = time.time()
        cost_time = end_time - self.start_time
        logger.info(f"quantization tuning time {cost_time}")

        ## dump a summary
        quantized_layers = []
        unquantized_layers = []
        for n, m in self.model.named_modules():
            if isinstance(m, tuple(self.supported_types)):
                if m.bits > 8:
                    unquantized_layers.append(n)
                else:
                    quantized_layers.append(n)
        summary_info = (
            f"Summary: quantized {len(quantized_layers)}/{len(quantized_layers) + len(unquantized_layers)} in the model"
        )
        if len(unquantized_layers) > 0:
            summary_info += f",  {unquantized_layers} have not been quantized"
        logger.info(summary_info)

        self.quantized = True
        ##self.model = self.model.to(self.model_orig_dtype)##keep it as amp dtype
        return self.model, self.layer_config

    def dump_qinfo_to_layer_config(self):
        """
        dump quantization scale and zp to layer configuration
        Args:

        Returns:
            None
        """
        # load scale and zp if use low_cpu_memory
        self.model = self.model.to('cpu')

        for n, m in self.model.named_modules():
            if n not in self.layer_config.keys():
                continue
            if hasattr(m, "scale"):
                self.layer_config[n]["scale"] = m.scale
                self.layer_config[n]["zp"] = m.zp
                delattr(m, "scale")
                delattr(m, "zp")
            else:
                self.layer_config[n]["data_type"] = "float"
                if self.amp_dtype == torch.bfloat16:
                    self.layer_config[n]["data_type"] = "bfloat"
                self.layer_config[n]["bits"] = 32
                self.layer_config[n]["group_size"] = None
                self.layer_config[n]["sym"] = None

    def quant_layers(self, layer_names, layer_inputs):
        """Quantizes specified layers based on inputs and configuration.

        Args:
            layer_names (list): List of layer names to quantize.
            layer_inputs (dict): Dictionary mapping layer names to input data.

        Returns:
            None
        """
        ##TODO currently we take all the layers outside blocks as post block layers which is not optimal
        if len(layer_names) == 0:
            return
        q_layer_inputs = None
        if self.enable_quanted_input:
            q_layer_inputs = self.try_cache_inter_data_gpucpu([], self.nsamples, layer_names=layer_names)

        self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
        torch.cuda.empty_cache()
        for layer_name in layer_names:
            layer_input = layer_inputs[layer_name]
            layer_input = to_device(layer_input, self.cache_device)
            q_layer_input = q_layer_inputs[layer_name] if self.enable_quanted_input else None
            q_layer_input = to_device(q_layer_input, self.cache_device)
            self.quant_layer(layer_name, layer_input, q_layer_input, device=self.device)
            for i in range(len(layer_input)):
                layer_input[i] = None
                if q_layer_input is not None:
                    q_layer_input[i] = None
            torch.cuda.empty_cache()

    def set_layerwise_config(self, layer_config):
        """Sets the layer-wise configuration based on the provided layer_config.
           By default, only quantize layers in blocks.

        Args:
        layer_config: The layer configuration.

        Returns:
        None
        """
        layers_in_blocks = get_layer_names_in_block(self.model, self.supported_types, self.multimodal)
        keys = ["data_type", "bits", "group_size", "sym", "scale_dtype", "act_bits", "act_group_size", "act_sym",
                "act_dynamic"]
        for n, m in self.model.named_modules():
            if not isinstance(m, tuple(self.supported_types)):
                continue
            ##not set in layer config, so use the default values
            if n not in layer_config.keys() and n in layers_in_blocks:
                layer_config[n] = {}
                for key in keys:
                    layer_config[n][key] = getattr(self, key)
            elif n in layer_config.keys():  ## partly set
                for key in keys:
                    if key not in layer_config[n].keys():
                        layer_config[n][key] = getattr(self, key)
            else:  ##not in layer_config and layers in block,
                layer_config[n] = {}
                for key in keys:
                    layer_config[n][key] = getattr(self, key)
                layer_config[n]["bits"] = 32
                layer_config[n]["act_bits"] = 32

            for key in keys:
                setattr(m, key, layer_config[n][key])


    @torch.no_grad()
    def get_block_outputs(self, block, input_ids, input_others, bs, device, cache_device):
        """Compute the output of a given block of the model for a given input.

        Args:
        block: The block of the model.
        input_ids: The input tensor containing tokenized input ids.
        input_others: A dictionary containing additional input data.
        bs: The batch size for computing the output.
        device: The device for computation.
        cache_device: The device for storing the output.
        batch_dim: The batch dimension of the output tensor.

        Returns:
        The output tensor of the block.
        """

        output = []
        nsamples = len(input_ids)
        for i in range(0, nsamples, bs):
            end_index = min(nsamples, i + bs)
            indices = torch.arange(i, end_index).to(torch.long)
            tmp_input_ids, tmp_input_others = sampling_inputs(
                input_ids,
                input_others,
                indices,
                self.seqlen,
                self.share_attention_mask_flag,
                self.not_share_position_ids_flag,
                self.input_dim
            )
            tmp_output = block_forward(block, tmp_input_ids, tmp_input_others, self.amp, self.amp_dtype, device).to(
                cache_device
            )
            output.extend(list(torch.split(tmp_output, 1, dim=self.input_dim)))
        torch.cuda.empty_cache()

        return output

    @torch.no_grad()
    def calib(self, nsamples, bs):
        """Perform calibration for quantization.

        This method calibrates the model for quantization by processing a specified
        number of samples from the calibration dataset. It ensures that the data is
        properly formatted and feeds it to the model. If the number of samples processed
        is less than the specified number, it logs a warning. If no samples are processed,
        it logs an error and exits.
        Args:
            nsamples (int): The number of samples to use for calibration.
            bs (int): The number of samples to use for calibration
        """
        if isinstance(self.dataset, str):
            dataset = self.dataset.replace(" ", "")  ##remove all whitespaces
            # slow here
            self.dataloader = get_dataloader(
                self.tokenizer,
                self.seqlen,
                dataset,
                self.seed,
                bs,
                self.nsamples,
            )
        else:
            self.dataloader = self.dataset
        total_cnt = 0

        # load embed weight if use low_cpu_mem_usage
        if self.low_cpu_mem_usage:
            embed_layers = get_layers_before_block(self.model)
            for n, m in embed_layers:
                m = m.to(self.device)
        
        for data in self.dataloader:
            if data is None:
                continue
            if isinstance(data, torch.Tensor):
                input_ids = data.to(self.device)
                data_new = input_ids
            elif isinstance(data, str):
                if self.tokenizer is None:
                    logger.error("please provide tokenizer for string input")
                    exit()
                data = self.tokenizer(data, truncation=True, max_length=self.seqlen, return_tensors="pt").data
                data_new = {}
                for key in data.keys():
                    data_new[key] = data[key].to(self.device)
                input_ids = data_new["input_ids"]
            elif isinstance(data, tuple) or isinstance(data, list):
                    data_new = data
                    input_ids = data_new[0]
            else:
                data_new = {}
                for key in data.keys():
                    data_new[key] = to_device(data[key], self.model.device)
                    if key == 'images':
                        data_new[key] = to_dtype(data[key], self.model.dtype)
                input_ids = data_new["input_ids"]
            if input_ids.shape[-1] < self.seqlen:
                continue
            
            try:
                if isinstance(data_new, torch.Tensor):
                    self.model(data_new)
                elif isinstance(data_new, tuple) or isinstance(data_new, list):
                    self.model(*data_new)
                else:
                    self.model(**data_new)
            except NotImplementedError:
                pass
            except Exception as error:
                logger.error(error)
            total_cnt += input_ids.shape[0] if len(input_ids.shape) > 1 else 1
            if total_cnt >= nsamples:
                break
        if total_cnt == 0:
            logger.error(
                f"no data has been cached, please provide more data with sequence length >={self.seqlen} in the "
                f"dataset or decease the sequence length"
            )
            exit()
        elif total_cnt < nsamples:
            logger.warning(
                f"Insufficient number of samples collected may affect the quantification. "
                f"Valid samples size:{total_cnt}, Target sample size:{nsamples}"
            )
        
        # clean embed weight to save memory
        if self.low_cpu_mem_usage:
            for n, m in embed_layers:
                m = m.to("meta")
        torch.cuda.empty_cache()

    @torch.no_grad()
    def try_cache_inter_data_gpucpu(self, block_names, nsamples, layer_names=[], last_cache_name=None):
        """Attempts to cache intermediate data on GPU, if failed, then using CPU.

        Args:
            block_names (list): List of block names to cache data for.
            nsamples (int): Number of samples to use for caching.
            layer_names (list, optional): List of layer names to cache data for. Defaults to [].
            last_cache_name (str, optional): Name of the last cache. Defaults to None.

        Returns:
            all_inputs: Cached intermediate data.

        Raises:
            Exception: If caching on GPU fails, switches to CPU and caches there.
        """
        try:
            if not self.model.device.type == "meta":
                self.model = self.model.to(self.device)
            all_inputs = self.cache_inter_data(
                block_names, nsamples, layer_names=layer_names, last_cache_name=last_cache_name
            )
            self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
            torch.cuda.empty_cache()
        except:
            logger.info("switch to cpu to cache inputs")
            self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
            torch.cuda.empty_cache()
            all_inputs = self.cache_inter_data(
                block_names, nsamples, layer_names=layer_names, last_cache_name=last_cache_name
            )
        return all_inputs

    @torch.no_grad()
    def cache_inter_data(self, block_names, nsamples, layer_names=[], last_cache_name=None):
        """Save the inputs of block_name for calibration. For layers, we cache both of inputs and output.

        This method temporarily replaces the forward method of the model to capture
        the inputs passing through the specified block. It then calibrates the model
        using a specified number of samples. Finally, it restores the original forward
        method and returns the inputs for the specified block.
        Args:
            block_names (list): The names of the blocks for which inputs are to be saved.
            layer_names (list):The names of the layers for which inputs are to be saved.
            nsamples (int): The number of samples to use for calibration.
            last_cache_name (str, optional): The name of the last layer to be cached,
                                       we could break the forward in this layer to save time

        Returns:
            dict: A dictionary containing the inputs for the specified block.
        """
        self.inputs = {}
        self.to_cached_layers = block_names + layer_names
        tmp_dtype = None
        ## have bug if block name is not the first block
        if (len(block_names) > 1 or len(layer_names) > 0) and self.low_gpu_mem_usage:
            tmp_dtype = self.model.dtype
            self.model = self.model.to(torch.bfloat16) if self.amp else self.model.to(torch.float32)

        self.last_cache_name = last_cache_name
        if last_cache_name is None and len(block_names) + len(layer_names) == 1:
            self.last_cache_name = block_names[0] if len(block_names) == 1 else layer_names[0]
        # do not set last_cache_name for multimodal models
        calib_bs = self.train_bs
        self.hook_handles = []
        self._replace_forward()
        self.calib(nsamples, calib_bs)
        self._recover_forward()
        res = self.inputs
        del self.last_cache_name
        del self.to_cached_layers
        if tmp_dtype is not None:
            self.model = self.model.to(tmp_dtype)

        return res

    @torch.no_grad()
    def get_block_forward_func(self, name):
        """Gets the forward function.

        Args:
            name (str): The name of the function.
        Returns:
            function: The forward function.
        """

        def forward(m, hidden_states, *positional_args, **kwargs):
            """Rewrite forward function, process and collect input data.

            Args:
                hidden_states (torch.Tensor): The hidden states tensor.
                *positional_args: Variable number of positional arguments.
                **kwargs: Variable number of keyword arguments.

            Returns:
                NotImplementedError: Getting the first layer inputs and then raise the error to save runtime.
            """
            if self.share_attention_mask_flag is None:
                self.input_dim = check_hidden_state_dim(self.model, positional_args)
                self.share_attention_mask_flag = check_share_attention_mask(self.model, hidden_states, **kwargs)
                self.not_share_position_ids_flag = check_not_share_position_ids(self.model, **kwargs)
            if name in self.inputs:
                self.inputs[name]["input_ids"].extend(list(torch.split(hidden_states.to("cpu"), 1, dim=self.input_dim)))
            else:
                self.inputs[name] = {}
                self.inputs[name]["input_ids"] = list(torch.split(hidden_states.to("cpu"), 1, dim=self.input_dim))

            if "positional_inputs" not in self.inputs[name]:
                self.inputs[name]["positional_inputs"] = []
            for idx, item in enumerate(positional_args):
                self.inputs[name]["positional_inputs"] = to_device(positional_args)

            for key in kwargs.keys():
                if isinstance(kwargs[key], torch.Tensor) or isinstance(kwargs[key], list) \
                        or (key == "alibi") or (key == "attention_mask"):
                    if "attention_mask" in key:
                        if key not in self.inputs[name].keys():
                            self.inputs[name][key] = None
                        if kwargs[key] is not None:
                            if (not self.share_attention_mask_flag) and self.inputs[name][key] is not None:
                                self.inputs[name][key].extend(list(torch.split(kwargs[key].to("cpu"), 1, dim=0)))
                            else:
                                self.inputs[name][key] = list(torch.split(kwargs[key].to("cpu"), 1, dim=0))
                    elif "alibi" in key:
                        if key not in self.inputs[name].keys():
                            self.inputs[name][key] = None
                        if isinstance(kwargs[key], torch.Tensor):
                            alibi = kwargs[key]
                            batch = kwargs["attention_mask"].shape[0]
                            alibi = alibi.reshape(batch, -1, alibi.shape[1], alibi.shape[2])
                            if (not self.share_attention_mask_flag) and self.inputs[name][key] is not None:
                                self.inputs[name][key].extend(list(torch.split(alibi.to("cpu"), 1, dim=0)))
                            else:
                                self.inputs[name][key] = list(torch.split(alibi.to("cpu"), 1, dim=0))
                    elif "position_ids" in key:
                        if key not in self.inputs[name].keys():
                            self.inputs[name][key] = list(torch.split(kwargs[key].to("cpu"), 1, dim=0)) \
                                                    if self.not_share_position_ids_flag \
                                                    else to_device(kwargs[key], device=torch.device("cpu"))
                        elif kwargs[key] is not None and self.not_share_position_ids_flag:
                            self.inputs[name][key].extend(list(torch.split(kwargs[key].to("cpu"), 1, dim=0)))
                    elif key not in self.inputs[name].keys():
                        self.inputs[name][key] = to_device(kwargs[key], device=torch.device("cpu"))
            if name == self.last_cache_name:
                raise NotImplementedError
            else:
                return m.orig_forward(hidden_states, *positional_args, **kwargs)

        return forward

    @torch.no_grad()
    def _get_cache_data_hook_for_layer(self, name):
        """A forward hook to save input max of a module
        :param name: the module name
        :return: A hook function."""

        def cache_input_hook(module, inputs, outputs):
            input = inputs
            if isinstance(inputs, tuple) or isinstance(input, list):
                input = inputs[0]
            if name in self.inputs:
                self.inputs[name].extend(list(torch.split(input.to("cpu"), 1, dim=0)))
            else:
                self.inputs[name] = list(torch.split(input.to("cpu"), 1, dim=0))

        return cache_input_hook

    def _recover_forward(self):
        """Recovers the forward function."""
        for n, m in self.model.named_modules():
            if hasattr(m, "orig_forward"):
                m.forward = m.orig_forward
                delattr(m, "orig_forward")
        for hook_handle in self.hook_handles:
            hook_handle.remove()
        self.hook_handles = []

    def _replace_forward(self):
        """Replaces the forward function."""
        from functools import partial

        for n, m in self.model.named_modules():
            if n in self.to_cached_layers and not isinstance(m, tuple(self.supported_types)):  ##block
                m.orig_forward = m.forward
                m.forward = partial(self.get_block_forward_func(n), m)
            elif n in self.to_cached_layers:  ##linear layer or conv1d layer
                hook_func = self._get_cache_data_hook_for_layer(n)
                hook_handle = m.register_forward_hook(hook_func)
                self.hook_handles.append(hook_handle)

    def quant_layer(self, layer_name, inputs, q_inputs=None, device=torch.device("cpu")):
        """Quantize a specific layer of the model using the provided inputs.

        Args:
            layer_name (str): The name of the layer to quantize.
            inputs (torch.Tensor): Input data for quantization.
            q_inputs (torch.Tensor, optional): Quantized input data. Defaults to None.
            device (torch.device, optional): The device to use for quantization. Defaults to torch.device("cpu").

        Returns:
            None
        """
        logger.info(f"quantizing layer {layer_name}")
        layer = get_module(self.model, layer_name)
        layer = layer.to(device)
        for i in range(len(inputs)):
            inputs[i] = inputs[i].to(layer.weight.dtype)
            if q_inputs is not None:
                q_inputs[i] = q_inputs[i].to(layer.weight.dtype)

        wrapper_linear = WrapperLinear(layer, self.enable_minmax_tuning, device).to(device)
        round_params = []
        minmax_params = []
        round_params.append(wrapper_linear.value)
        minmax_params.append(wrapper_linear.min_scale)
        minmax_params.append(wrapper_linear.max_scale)
        if self.enable_minmax_tuning:
            optimizer = self.optimizer(
                [{"params": round_params}, {"params": minmax_params, "lr": self.minmax_lr}], lr=self.lr, weight_decay=0
            )
        else:
            optimizer = self.optimizer(round_params, lr=self.lr, weight_decay=0)

        if self.enable_lr_scheduler:
            if self.lr_scheduler is None:
                lr_schedule = torch.optim.lr_scheduler.LinearLR(
                    optimizer, start_factor=1.0, end_factor=0.0, total_iters=self.iters, verbose=False
                )
            else:
                lr_schedule = copy.deepcopy(self.lr_scheduler)
        else:
            lr_schedule = None
            
        nsamples = len(inputs)
        last_best_iter = 0
        best_loss = torch.finfo(torch.float).max
        mse_loss = torch.nn.MSELoss().to(device)
        scaler = self.get_scaler()  # pylint: disable=assignment-from-none
        init_loss = None
        best_v, best_min_scale, best_max_scale = torch.tensor(0), torch.tensor(1.0), torch.tensor(1.0)
        gradient_accumulate_steps = self.train_bs  ##Force to low gpu
        train_bs = 1  ##Force to low gpu
        pick_samples = train_bs * gradient_accumulate_steps

        if self.sampler != "rand":
            whole_indices = torch.randperm(nsamples)[:pick_samples]
        for i in range(self.iters):
            total_loss = 0
            if self.sampler == "rand":
                whole_indices = torch.randperm(nsamples)[:pick_samples]
            for tmp_step in range(gradient_accumulate_steps):
                indices = whole_indices[tmp_step * train_bs: (tmp_step + 1) * train_bs]
                if q_inputs is not None:
                    current_input = [q_inputs[i] for i in indices]
                    current_input = torch.cat(current_input, dim=0).to(device)
                    org_input = [inputs[i] for i in indices]
                    org_input = torch.cat(org_input, dim=0).to(device)
                else:
                    current_input = [inputs[i] for i in indices]
                    current_input = torch.cat(current_input, dim=0).to(device)
                    org_input = current_input
                with torch.no_grad():
                    current_output = layer(org_input)

                if self.amp:
                    with autocast(device_type=device.split(":")[0], dtype=self.amp_dtype):
                        output_q = wrapper_linear(current_input)  # pylint: disable=not-callable
                        loss = mse_loss(output_q, current_output)  # pylint: disable=not-callable
                else:
                    output_q = wrapper_linear(current_input)  # pylint: disable=not-callable
                    loss = mse_loss(  # pylint: disable=not-callable
                        output_q.to(torch.float32), current_output.to(torch.float32)
                    )
                total_loss += loss.item() / gradient_accumulate_steps

                self.scale_loss_and_backward(scaler, loss)
            if i == 0:
                init_loss = total_loss

            if total_loss < best_loss:
                best_loss = total_loss
                if not self.not_use_best_mse:
                    best_v = copy.deepcopy(wrapper_linear.value.data)
                    best_min_scale = copy.deepcopy(torch.clamp(wrapper_linear.min_scale.data, 0, 1.0))
                    best_max_scale = copy.deepcopy(torch.clamp(wrapper_linear.max_scale.data, 0, 1.0))

                    last_best_iter = i
            if self.not_use_best_mse and i == self.iters - 1:
                best_v = copy.deepcopy(wrapper_linear.value.data)
                best_min_scale = copy.deepcopy(torch.clamp(wrapper_linear.min_scale.data, 0, 1.0))
                best_max_scale = copy.deepcopy(torch.clamp(wrapper_linear.max_scale.data, 0, 1.0))

            if not self.not_use_best_mse:
                if self.dynamic_max_gap > 0 and i - last_best_iter >= self.dynamic_max_gap:
                    break
            self.step(scaler, optimizer, lr_schedule)

        last_loss = total_loss
        best_iter = self.iters
        if not self.not_use_best_mse:
            last_loss = best_loss
            best_iter = last_best_iter
        with torch.no_grad():
            unwrapper_layer(self.model, wrapper_linear, layer_name, best_v, best_min_scale, best_max_scale)
        dump_info = f"quantized {layer_name},  loss iter 0: {init_loss:.6f} -> iter {best_iter}: {last_loss:.6f}"
        logger.info(dump_info)

    def quant_block(self, block, input_ids, input_others, q_input=None, device=torch.device("cpu")):
        """Quantize the weights of a given block of the model.

        Args:
        block: The block of the model to be quantized.
        input_ids: The input tensor containing tokenized input ids.
        input_others: A dictionary containing additional input data.
        q_input: The quantized input tensor.
        device: The device for quantization.

        Returns:
        Tuple: (q_outputs, output) if self.enable_quanted_input is True, else (None, output)
        """

        output = self.get_block_outputs(block, input_ids, input_others, self.train_bs * self.infer_bs_coeff, device,
                                        self.cache_device)

        if q_input is not None:
            input_ids = q_input

        quantized_layer_names, unquantized_layer_names = wrapper_block(
            block, self.enable_minmax_tuning, device=self.device)

        round_params = []
        minmax_params = []
        for n, m in block.named_modules():
            if hasattr(m, "orig_layer"):
                round_params.append(m.value)
                minmax_params.append(m.min_scale)
                minmax_params.append(m.max_scale)

        if self.enable_minmax_tuning:
            optimizer = self.optimizer(
                [{"params": round_params}, {"params": minmax_params, "lr": self.minmax_lr}], lr=self.lr, weight_decay=0
            )
        else:
            optimizer = self.optimizer(round_params, lr=self.lr, weight_decay=0)

        if len(round_params) + len(minmax_params) <= 0:
            dump_info = (
                f"quantized {len(quantized_layer_names)}/{(len(quantized_layer_names) + len(unquantized_layer_names))} "
                f"layers in the block"
            )
            logger.info(dump_info)
            return output, output

        if self.lr_scheduler is None:
            lr_schedule = torch.optim.lr_scheduler.LinearLR(
                optimizer, start_factor=1.0, end_factor=0.0, total_iters=self.iters, verbose=False
            )
        else:
            lr_schedule = copy.deepcopy(self.lr_scheduler)

        pick_samples = self.train_bs * self.gradient_accumulate_steps
        nsamples = len(input_ids)
        if self.sampler != "rand":
            whole_indices = torch.randperm(nsamples)[:pick_samples]
        last_best_iter = 0
        best_loss = torch.finfo(torch.float).max
        mse_loss = torch.nn.MSELoss().to(device)
        scaler = self.get_scaler()  # pylint: disable=assignment-from-none
        init_loss = None
        best_v, best_min_scale, best_max_scale = torch.tensor(0), torch.tensor(1.0), torch.tensor(1.0)
        for i in range(self.iters):
            total_loss = 0
            if self.sampler == "rand":
                whole_indices = torch.randperm(nsamples)[:pick_samples]
            for tmp_step in range(self.gradient_accumulate_steps):
                indices = whole_indices[tmp_step * self.train_bs: (tmp_step + 1) * self.train_bs]
                current_input_ids, current_input_others = sampling_inputs(
                    input_ids,
                    input_others,
                    indices,
                    seqlen=self.seqlen,
                    share_attention_mask_flag=self.share_attention_mask_flag,
                    not_share_position_ids_flag=self.not_share_position_ids_flag,
                    input_dim=self.input_dim,
                )

                current_output = [output[i] for i in indices]
                current_output = torch.cat(current_output, dim=self.input_dim)

                current_output = to_device(current_output, device)

                output_q = block_forward(
                    block, current_input_ids, current_input_others, self.amp, self.amp_dtype, device
                )
                if self.amp:
                    with autocast(device_type=device.split(":")[0], dtype=self.amp_dtype):
                        loss = mse_loss(output_q, current_output)  # pylint: disable=not-callable
                else:
                    loss = mse_loss(  # pylint: disable=not-callable
                        output_q.to(torch.float32), current_output.to(torch.float32)
                    )

                total_loss += loss.item() / self.gradient_accumulate_steps
                self.scale_loss_and_backward(scaler, loss)
            if i == 0:
                init_loss = total_loss

            if total_loss < best_loss:
                best_loss = total_loss
                if not self.not_use_best_mse:
                    # print(f"get better result at iter {i}, the loss is {total_loss}", flush=True)
                    best_v = collect_round_v(block)
                    best_min_scale, best_max_scale = collect_minmax_scale(block)
                    last_best_iter = i
            if self.not_use_best_mse and i == self.iters - 1:
                best_v = collect_round_v(block)
                best_min_scale, best_max_scale = collect_minmax_scale(block)

            if not self.not_use_best_mse:
                if self.dynamic_max_gap > 0 and i - last_best_iter >= self.dynamic_max_gap:
                    break
            self.step(scaler, optimizer, lr_schedule)

        last_loss = total_loss
        best_iter = self.iters
        if not self.not_use_best_mse:
            last_loss = best_loss
            best_iter = last_best_iter
        dump_info = (
            f"quantized {len(quantized_layer_names)}/{(len(quantized_layer_names) + len(unquantized_layer_names))} "
            f"layers in the block, loss iter 0: {init_loss:.6f} -> iter {best_iter}: {last_loss:.6f}"
        )
        logger.info(dump_info)
        if len(unquantized_layer_names) != 0:
            logger.info(f"{unquantized_layer_names} have not been quantized")
        with torch.no_grad():
            unwrapper_block(block, best_v, best_min_scale, best_max_scale)
        if self.enable_quanted_input:
            block = block.to(device)
            q_outputs = self.get_block_outputs(
                block, input_ids, input_others, self.train_bs * self.infer_bs_coeff, device,
                cache_device=self.cache_device
            )
            block = mv_module_from_gpu(block, self.low_cpu_mem_usage)
            for i in range(len(input_ids)):
                input_ids[i] = None
            torch.cuda.empty_cache()

            return q_outputs, output

        else:
            for i in range(len(input_ids)):
                input_ids[i] = None
            torch.cuda.empty_cache()
            return None, output
        

    def quant_block_with_lookahead(
        self, 
        combined_block: WrapperMultiblock, 
        input_ids, 
        input_others, 
        q_input=None, 
        device=torch.device("cpu"),
        fine_tune_block_name: str = "unk_layer",
        attach_loss_block_name: str = "unk_layer",
        observe_block_name: str = "unk_layer",
    ):
        """Quantize the weights of a given block of the model.

        Args:
        block: The block of the model to be quantized.
        input_ids: The input tensor containing tokenized input ids.
        input_others: A dictionary containing additional input data.
        q_input: The quantized input tensor.
        device: The device for quantization.

        Returns:
        Tuple: (q_outputs, output) if self.enable_quanted_input is True, else (None, output)
        """
        fine_tune_block, attach_loss_block, observe_block = combined_block.layers
        fine_tune_block_outputs = self.get_block_outputs(
            fine_tune_block, 
            input_ids, 
            input_others, 
            self.train_bs * self.infer_bs_coeff, 
            device, 
            self.cache_device
        )

        attach_loss_block_outputs = self.get_block_outputs(
            attach_loss_block, 
            fine_tune_block_outputs, 
            input_others, 
            self.train_bs * self.infer_bs_coeff, 
            device,
            self.cache_device
        )
        
        observe_block_outputs = self.get_block_outputs(
            observe_block, 
            attach_loss_block_outputs,
            input_others, 
            self.train_bs * self.infer_bs_coeff, 
            device,
            self.cache_device
        )

        if q_input is not None:
            input_ids = q_input

        quantized_layer_names, unquantized_layer_names = wrapper_block(
            fine_tune_block, self.enable_minmax_tuning, device=self.device)

        round_params = []
        minmax_params = []
        for n, m in fine_tune_block.named_modules():
            if hasattr(m, "orig_layer"):
                round_params.append(m.value)
                minmax_params.append(m.min_scale)
                minmax_params.append(m.max_scale)

        if self.enable_minmax_tuning:
            optimizer = self.optimizer(
                [{"params": round_params}, {"params": minmax_params, "lr": self.minmax_lr}], lr=self.lr, weight_decay=0
            )
        else:
            optimizer = self.optimizer(round_params, lr=self.lr, weight_decay=0)

        if len(round_params) + len(minmax_params) <= 0:
            dump_info = (
                f"quantized {len(quantized_layer_names)}/{(len(quantized_layer_names) + len(unquantized_layer_names))} "
                f"layers in the block"
            )
            logger.info(dump_info)
            return fine_tune_block_outputs, fine_tune_block_outputs

        if self.enable_lr_scheduler:
            if self.lr_scheduler is None:
                lr_schedule = torch.optim.lr_scheduler.LinearLR(
                    optimizer, start_factor=1.0, end_factor=0.0, total_iters=self.iters, verbose=False
                )
            else:
                lr_schedule = copy.deepcopy(self.lr_scheduler)
        else:
            lr_schedule = None

        pick_samples = self.train_bs * self.gradient_accumulate_steps
        nsamples = len(input_ids)
        if self.sampler != "rand":
            whole_indices = torch.randperm(nsamples)[:pick_samples]
        last_best_iter = 0
        best_loss = torch.finfo(torch.float).max
        mse_loss = torch.nn.MSELoss().to(device)
        scaler = self.get_scaler()  # pylint: disable=assignment-from-none
        init_loss = None
        best_v, best_min_scale, best_max_scale = torch.tensor(0), torch.tensor(1.0), torch.tensor(1.0)
        
        if not self.disable_wandb:
            wandb.define_metric(f"iter_count/{fine_tune_block_name}->{observe_block_name}")
            wandb.define_metric(
                f"attach_loss_block_mse/{fine_tune_block_name}->{observe_block_name}/{attach_loss_block_name}", 
                step_metric=f"iter_count/{fine_tune_block_name}->{observe_block_name}"
            )
            wandb.define_metric(
                f"observe_block_mse/{fine_tune_block_name}->{observe_block_name}/{attach_loss_block_name}", 
                step_metric=f"iter_count/{fine_tune_block_name}->{observe_block_name}"
            )
            wandb.define_metric(
                f"lr/{fine_tune_block_name}->{observe_block_name}/{attach_loss_block_name}", 
                step_metric=f"iter_count/{fine_tune_block_name}->{observe_block_name}"
            )
        
        mses_observe_block = []
        for i in range(self.iters):
            total_attach_loss_block_mse = 0
            total_observe_block_mse = 0
            if self.sampler == "rand":
                whole_indices = torch.randperm(nsamples)[:pick_samples]
            for tmp_step in range(self.gradient_accumulate_steps):
                indices = whole_indices[tmp_step * self.train_bs: (tmp_step + 1) * self.train_bs]
                current_input_ids, current_input_others = sampling_inputs(
                    input_ids,
                    input_others,
                    indices,
                    seqlen=self.seqlen,
                    share_attention_mask_flag=self.share_attention_mask_flag,
                    not_share_position_ids_flag=self.not_share_position_ids_flag,
                    input_dim=self.input_dim,
                )

                high_precision_attach_loss_block_output = [attach_loss_block_outputs[i] for i in indices]
                high_precision_attach_loss_block_output = torch.cat(high_precision_attach_loss_block_output, dim=self.input_dim)
                high_precision_attach_loss_block_output = to_device(high_precision_attach_loss_block_output, device)

                quantized_fine_tune_block_output = block_forward(
                    fine_tune_block, current_input_ids, copy.deepcopy(current_input_others), self.amp, self.amp_dtype, device
                )
                quantized_attach_loss_block_output = block_forward(
                    attach_loss_block, quantized_fine_tune_block_output, copy.deepcopy(current_input_others), self.amp, self.amp_dtype, device
                )
                quantized_fine_tune_block_output = None
                del quantized_fine_tune_block_output
                torch.cuda.empty_cache()
                
                if self.amp:
                    with autocast(device_type=device.split(":")[0], dtype=self.amp_dtype):
                        attach_loss_block_mse = mse_loss(
                            quantized_attach_loss_block_output, 
                            high_precision_attach_loss_block_output,
                        )  # pylint: disable=not-callable
                else:
                    attach_loss_block_mse = mse_loss(  # pylint: disable=not-callable
                        quantized_attach_loss_block_output.to(torch.float32), 
                        high_precision_attach_loss_block_output.to(torch.float32)
                    )
                    
                current_input_ids = None
                high_precision_attach_loss_block_output = None
                del current_input_ids
                del high_precision_attach_loss_block_output
                torch.cuda.empty_cache()
                
                # Observe
                high_precision_observe_block_output = [observe_block_outputs[i] for i in indices]
                high_precision_observe_block_output = torch.cat(high_precision_observe_block_output, dim=self.input_dim)
                high_precision_observe_block_output = to_device(high_precision_observe_block_output, device)
                
                quantized_observe_block_output = block_forward(
                    observe_block, quantized_attach_loss_block_output, copy.deepcopy(current_input_others), self.amp, self.amp_dtype, device
                )
                
                quantized_attach_loss_block_output = None
                del quantized_attach_loss_block_output
                torch.cuda.empty_cache()
                
                if self.amp:
                    with autocast(device_type=device.split(":")[0], dtype=self.amp_dtype):
                        observe_block_mse = mse_loss(
                            quantized_observe_block_output, 
                            high_precision_observe_block_output,
                        )  # pylint: disable=not-callable
                else:
                    observe_block_mse = mse_loss(  # pylint: disable=not-callable
                        quantized_observe_block_output.to(torch.float32), 
                        high_precision_observe_block_output.to(torch.float32)
                    )
                
                high_precision_observe_block_output = None
                quantized_observe_block_output = None
                del high_precision_observe_block_output
                del quantized_observe_block_output
                torch.cuda.empty_cache()

                total_attach_loss_block_mse += attach_loss_block_mse.item() / self.gradient_accumulate_steps
                self.scale_loss_and_backward(scaler, attach_loss_block_mse)
                total_observe_block_mse += observe_block_mse.item() / self.gradient_accumulate_steps

            mses_observe_block.append(total_observe_block_mse)
            
            if i == 0:
                init_loss = total_attach_loss_block_mse

            if total_attach_loss_block_mse < best_loss:
                best_loss = total_attach_loss_block_mse
                if not self.not_use_best_mse:
                    # print(f"get better result at iter {i}, the loss is {total_attach_loss_block_mse}", flush=True)
                    best_v = collect_round_v(fine_tune_block)
                    best_min_scale, best_max_scale = collect_minmax_scale(fine_tune_block)
                    last_best_iter = i
            if self.not_use_best_mse and i == self.iters - 1:
                best_v = collect_round_v(fine_tune_block)
                best_min_scale, best_max_scale = collect_minmax_scale(fine_tune_block)

            if not self.not_use_best_mse:
                if self.dynamic_max_gap > 0 and i - last_best_iter >= self.dynamic_max_gap:
                    break
            self.step(scaler, optimizer, lr_schedule)
            if not self.disable_wandb:
                learning_rate = lr_schedule.get_last_lr()[0] if lr_schedule is not None else self.lr
                wandb.log(
                    data={
                        f"iter_count/{fine_tune_block_name}->{observe_block_name}": i,
                        f"attach_loss_block_mse/{fine_tune_block_name}->{observe_block_name}/{attach_loss_block_name}": total_attach_loss_block_mse,
                        f"observe_block_mse/{fine_tune_block_name}->{observe_block_name}/{attach_loss_block_name}": total_observe_block_mse,
                        f"lr/{fine_tune_block_name}->{observe_block_name}/{attach_loss_block_name}": learning_rate,
                    }, 
                )

        last_loss = total_attach_loss_block_mse
        best_iter = self.iters
        if not self.not_use_best_mse:
            last_loss = best_loss
            best_iter = last_best_iter
        dump_info = (
            f"quantized {len(quantized_layer_names)}/{(len(quantized_layer_names) + len(unquantized_layer_names))} "
            f"layers in the block, loss iter 0: {init_loss:.6f} -> iter {best_iter}: {last_loss:.6f}"
            f", observe block mse: {total_observe_block_mse:.6f}"
        )
        logger.info(dump_info)
        if len(unquantized_layer_names) != 0:
            logger.info(f"{unquantized_layer_names} have not been quantized")
        with torch.no_grad():
            unwrapper_block(fine_tune_block, best_v, best_min_scale, best_max_scale)
        if self.enable_quanted_input:
            fine_tune_block = fine_tune_block.to(device)
            q_outputs = self.get_block_outputs(
                fine_tune_block, input_ids, input_others, self.train_bs * self.infer_bs_coeff, device,
                cache_device=self.cache_device
            )
            fine_tune_block = mv_module_from_gpu(fine_tune_block, self.low_cpu_mem_usage)
            # for i in range(len(input_ids)):
            #     input_ids[i] = None
            # torch.cuda.empty_cache()

            return q_outputs, fine_tune_block_outputs, mses_observe_block

        else:
            # for i in range(len(input_ids)):
                # input_ids[i] = None
            # torch.cuda.empty_cache()
            return None, fine_tune_block_outputs, mses_observe_block


    def quant_blocks(
            self,
            model: torch.nn.Module,
            inputs,
            block_names,
            nblocks=1,
            block_step_size: int = 1,
            num_lookahead_blocks: int = 0,
            num_observe_blocks: int = 0,
            device=torch.device("cpu"),
    ):
        """Quantize and dequantize the weights of the specified blocks in the model.

        Args:
        model: The PyTorch model to be quantized.
        inputs: The input data for quantization.
        block_names: The names of the blocks to be quantized and dequantized.
        nblocks: The number of blocks to quantize and dequantize.
        device: The device for quantization and dequantization.

        Returns:
        None
        """
        q_input = None
        torch.cuda.empty_cache()
        for n, m in model.named_parameters():
            m.requires_grad_(False)
        input_ids = inputs["input_ids"]
        inputs.pop("input_ids", None)
        input_others = inputs
        torch.cuda.empty_cache()
        input_ids = to_device(input_ids, self.cache_device)
        input_others = to_device(input_others, self.cache_device)
        ## as in calibration phase, we may use bf16 for calibration due to low_gpu_memory usage
        tmp_dtype = self.amp_dtype if self.amp else torch.float32
        for i in range(len(input_ids)):
            input_ids[i] = input_ids[i].to(tmp_dtype)

        for key in input_others.keys():
            if isinstance(input_others[key], torch.Tensor) and (
                    input_others[key].dtype == torch.float16 or input_others[key].dtype == torch.bfloat16
            ):
                input_others[key] = input_others[key].to(tmp_dtype)
            elif isinstance(input_others[key], list):
                for i in range(len(input_others[key])):
                    input_others[key][i].to(tmp_dtype)
                    
        if self.eval_after_each_optimization and not self.disable_wandb:
            local_evals_df = None
                    
        if self.cleanly_separated_lookahead: 
            for substructure_first_block_idx in range(0, len(block_names), self.num_lookahead_blocks + 1):
                attach_loss_block_idx = min(substructure_first_block_idx + self.num_lookahead_blocks, len(block_names) - 1)
                attach_loss_block_name = block_names[attach_loss_block_idx]
                attach_loss_block = get_module(model, attach_loss_block_name)
                attach_loss_block = attach_loss_block.to(device)
                
                # observe_block is the same as attach_loss_block
                observe_block_name = attach_loss_block_name
                observe_block = WrapperMultiblock([])  # observe_block should not change the output of the attach_loss_block
                observe_block = observe_block.to(device)
                
                for fine_tune_block_idx in range(substructure_first_block_idx, attach_loss_block_idx + 1):
                    if fine_tune_block_idx == attach_loss_block_idx:
                        fine_tune_block_name = attach_loss_block_name
                        fine_tune_block = attach_loss_block
                        attach_loss_block = WrapperMultiblock([])  # attach_loss_block should not change the output of the fine_tune_block
                        attach_loss_block = attach_loss_block.to(device)
                    else:
                        fine_tune_block_name = block_names[fine_tune_block_idx]
                        fine_tune_block = get_module(model, fine_tune_block_name)
                        fine_tune_block = fine_tune_block.to(device)
                        
                    logger.info(f"fine tune block {fine_tune_block_name}")
                    logger.info(f"attach loss block {attach_loss_block_name}")
                    logger.info(f"observe block {observe_block_name}")

                    combined_block = WrapperMultiblock([fine_tune_block, attach_loss_block, observe_block])
                    combined_block = combined_block.to(device)

                    q_input, input_ids, _ = self.quant_block_with_lookahead(
                        combined_block,
                        input_ids,
                        input_others,
                        q_input=q_input,
                        device=device,
                        fine_tune_block_name=fine_tune_block_name,
                        attach_loss_block_name=attach_loss_block_name,
                        observe_block_name=observe_block_name,
                    )

                    self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
                    torch.cuda.empty_cache()
        else:
            
            last_fully_fine_tuned_block_idx = -1
            unquantized_last_fully_fine_tuned_block_output = input_ids
            quantized_last_fully_fine_tuned_block_output = None
            for fine_tune_block_indices, attach_loss_block_indices, observe_block_indices in get_block_indices(
                nblocks=nblocks, 
                block_step_size=block_step_size, 
                num_lookahead_blocks=num_lookahead_blocks, 
                num_observe_blocks=num_observe_blocks,
                total_num_blocks=len(block_names),
            ): 
                    if fine_tune_block_indices.start > 0 and fine_tune_block_indices.start - 1 > last_fully_fine_tuned_block_idx:
                        assert fine_tune_block_indices.start - last_fully_fine_tuned_block_idx == block_step_size + 1
                        last_fully_fine_tuned_block_idx = fine_tune_block_indices.start - 1
                        last_fine_tuned_multiblock_start_idx = fine_tune_block_indices.start - block_step_size
                        last_fine_tuned_block_names = block_names[last_fine_tuned_multiblock_start_idx: fine_tune_block_indices.start]
                        last_fine_tuned_multiblock = WrapperMultiblock(
                            [get_module(model, block_name) for block_name in last_fine_tuned_block_names]
                        )
                        last_fine_tuned_multiblock.to(device)
                        logger.info(f"last fine tuned multiblock {last_fine_tuned_block_names}")
                        if self.enable_quanted_input:
                            input_ids = unquantized_last_fully_fine_tuned_block_output if last_fine_tuned_multiblock_start_idx == 0 else quantized_last_fully_fine_tuned_block_output
                            quantized_last_fully_fine_tuned_block_output = self.get_block_outputs(
                                block=last_fine_tuned_multiblock,
                                input_ids=input_ids,
                                input_others=input_others,
                                bs=self.train_bs * self.infer_bs_coeff,
                                device=device,
                                cache_device=self.cache_device,
                            )
                        unquantized_last_fully_fine_tuned_block_output = self.get_block_outputs(
                            block=last_fine_tuned_multiblock,
                            input_ids=unquantized_last_fully_fine_tuned_block_output,
                            input_others=input_others,
                            bs=self.train_bs * self.infer_bs_coeff,
                            device=device,
                            cache_device=self.cache_device,
                        )
                            
                    logger.info(f"last fully fine tuned block {last_fully_fine_tuned_block_idx}")
                    fine_tune_block_names = block_names[fine_tune_block_indices]
                    logger.info(f"fine tune block {fine_tune_block_names}")
                    fine_tune_block = WrapperMultiblock(
                        [get_module(model, fine_tune_block_name) for fine_tune_block_name in fine_tune_block_names]
                    )
                
                    attach_loss_block_names = block_names[attach_loss_block_indices]
                    attach_loss_block = WrapperMultiblock(
                        [get_module(model, attach_loss_block_name) for attach_loss_block_name in attach_loss_block_names]
                    )
                    if len(attach_loss_block_names) == 0:
                        attach_loss_block_names = fine_tune_block_names
                    logger.info(f"attach loss block {attach_loss_block_names}") 
                                
                    observe_block_names = block_names[observe_block_indices]
                    observe_block = WrapperMultiblock(
                        [get_module(model, observe_block_name) for observe_block_name in observe_block_names]
                    )
                    if len(observe_block_names) == 0:
                        observe_block_names = attach_loss_block_names
                    logger.info(f"observe block {observe_block_names}") 
                    
                    combined_block = WrapperMultiblock([fine_tune_block, attach_loss_block, observe_block])
                    combined_block = combined_block.to(device)

                    q_input, input_ids, _ = self.quant_block_with_lookahead(
                        combined_block,
                        unquantized_last_fully_fine_tuned_block_output,
                        input_others,
                        q_input=quantized_last_fully_fine_tuned_block_output,
                        device=device,
                        fine_tune_block_name=format_layer_name(fine_tune_block_names if isinstance(fine_tune_block_names, str) else fine_tune_block_names[-1]),
                        attach_loss_block_name=format_layer_name(attach_loss_block_names if isinstance(attach_loss_block_names, str) else attach_loss_block_names[-1]),
                        observe_block_name=format_layer_name(observe_block_names if isinstance(observe_block_names, str) else observe_block_names[-1]),
                    )
                    
                    if nblocks == block_step_size:
                        last_fully_fine_tuned_block_idx = fine_tune_block_indices.stop - 1
                        for i in range(len(input_ids)):
                            if self.enable_quanted_input and quantized_last_fully_fine_tuned_block_output is not None:
                                quantized_last_fully_fine_tuned_block_output[i] = None
                            unquantized_last_fully_fine_tuned_block_output[i] = None
                        del quantized_last_fully_fine_tuned_block_output
                        del unquantized_last_fully_fine_tuned_block_output
                        
                        quantized_last_fully_fine_tuned_block_output = q_input
                        unquantized_last_fully_fine_tuned_block_output = input_ids
                    else:
                        for i in range(len(input_ids)):
                            if self.enable_quanted_input:
                                q_input[i] = None
                            input_ids[i] = None
                        if q_input is not None:
                            del q_input
                        del input_ids
                    
                    self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
                    torch.cuda.empty_cache()
                    
                    if self.eval_after_each_optimization:
                        results_file_suffix = (
                            f"_num-quantized-blocks::{fine_tune_block_indices.stop}"
                            f"_fine-tune-block-indices::{fine_tune_block_indices.start}:{fine_tune_block_indices.stop}"
                        )
                        model = model.to("cpu")
                        model.save_pretrained(self.model_save_dir)
                        self.tokenizer.save_pretrained(self.model_save_dir)
                        
                        eval_results = evaluate_all.evaluate(
                            model_path=self.model_save_dir,
                            batch_size=self.eval_batch_size,
                            results_file_name_suffix=results_file_suffix,
                            tasks=self.eval_tasks,
                            seed=self.eval_seed,
                        )    
                        print(eval_results)
                        
                        if not self.disable_wandb:
                            if local_evals_df is None:
                                local_evals_df = pd.DataFrame(eval_results)
                                local_evals_df.insert(0, "num_quantized_blocks", fine_tune_block_indices.stop)
                                local_evals_df.insert(1, "fine_tune_block_indices", f"{fine_tune_block_indices.start}:{fine_tune_block_indices.stop}")
                            else:
                                eval_results["num_quantized_blocks"] = fine_tune_block_indices.stop
                                eval_results["fine_tune_block_indices"] = f"{fine_tune_block_indices.start}:{fine_tune_block_indices.stop}"
                                local_evals_df = pd.concat([local_evals_df, pd.DataFrame(eval_results)], ignore_index=True)
                            wandb.log({"local_eval_results": wandb.Table(dataframe=local_evals_df)})
                        
                        # delete model weights
                        for file_path in glob.glob(os.path.join(self.model_save_dir, "*.safetensors")):
                            os.remove(file_path)
                            
                        self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
                        
                        

        # del q_input
        # del input_ids
        del input_others
        del inputs

        torch.cuda.empty_cache()

    def quant_blocks_isolation_experiment_v2(
            self,
            model: torch.nn.Module,
            inputs,
            block_names,
            fine_tune_block_idx: int = 0,
            observe_block_idx: int = 0,
            attach_loss_block_indices: list[int] = [-1],
            device=torch.device("cpu"),
    ):
        """Quantize and dequantize the weights of the specified blocks in the model.

        Args:
        model: The PyTorch model to be quantized.
        inputs: The input data for quantization.
        block_names: The names of the blocks to be quantized and dequantized.
        nblocks: The number of blocks to quantize and dequantize.
        device: The device for quantization and dequantization.

        Returns:
        None
        """
        assert self.observe_block_idx < len(block_names), (
            f"observe_block_idx {self.observe_block_idx} should be less than the number of blocks {len(block_names)}"   
        )
        
        logger.info("Quantizing blocks with lookahead ablation")
        
        q_input = None
        torch.cuda.empty_cache()
        for n, m in model.named_parameters():
            m.requires_grad_(False)
        input_ids = inputs["input_ids"]
        inputs.pop("input_ids", None)
        input_others = inputs
        torch.cuda.empty_cache()
        input_ids = to_device(input_ids, self.cache_device)
        input_others = to_device(input_others, self.cache_device)
        ## as in calibration phase, we may use bf16 for calibration due to low_gpu_memory usage
        tmp_dtype = self.amp_dtype if self.amp else torch.float32
        for i in range(len(input_ids)):
            input_ids[i] = input_ids[i].to(tmp_dtype)

        for key in input_others.keys():
            if isinstance(input_others[key], torch.Tensor) and (
                    input_others[key].dtype == torch.float16 or input_others[key].dtype == torch.bfloat16
            ):
                input_others[key] = input_others[key].to(tmp_dtype)
            elif isinstance(input_others[key], list):
                for i in range(len(input_others[key])):
                    input_others[key][i].to(tmp_dtype)
                    
        preceding_block_names = block_names[:fine_tune_block_idx]
        preceding_block = WrapperMultiblock(
            [get_module(model, preceding_block_name) for preceding_block_name in preceding_block_names]
        )
        preceding_block = preceding_block.to(device)
        logger.info(f"preceding block {preceding_block_names}")

        preceding_block_outputs = self.get_block_outputs(
            preceding_block, input_ids, input_others, self.train_bs * self.infer_bs_coeff, device, self.cache_device
        )
        
        for i in range(len(input_ids)):
            input_ids[i] = None
        del input_ids
        torch.cuda.empty_cache()
        
        fine_tune_block_name = block_names[fine_tune_block_idx]
        if attach_loss_block_indices[0] == -1:
            attach_loss_block_indices = list(range(fine_tune_block_idx, observe_block_idx + 1))
        
        log_data = []
        for attach_loss_block_idx in attach_loss_block_indices:
            fine_tune_block = copy.deepcopy(get_module(model, fine_tune_block_name))  # copy.deepcopy since quantization will change the block
            logger.info(f"fine tune block {fine_tune_block_name}")
            
            if attach_loss_block_idx == fine_tune_block_idx:
                attach_loss_block_names = fine_tune_block_name
                attach_loss_block = WrapperMultiblock([])  # empty block
            else:
                attach_loss_block_names = block_names[fine_tune_block_idx + 1: attach_loss_block_idx + 1]
                attach_loss_block =  WrapperMultiblock(
                    [get_module(model, attach_loss_block_name) for attach_loss_block_name in attach_loss_block_names]
                )
            logger.info(f"attach loss block {attach_loss_block_names}")
            
            if attach_loss_block_idx == observe_block_idx:
                observe_block_names = attach_loss_block_names
                observe_block = WrapperMultiblock([])
            else:
                observe_block_names = block_names[attach_loss_block_idx + 1: observe_block_idx + 1]
                observe_block = WrapperMultiblock(
                    [get_module(model, observe_block_name) for observe_block_name in observe_block_names]
                )
            logger.info(f"observe block {observe_block_names}") 
            
            combined_block = WrapperMultiblock([fine_tune_block, attach_loss_block, observe_block])
            combined_block = combined_block.to(device)

            fine_tune_block_name = fine_tune_block_name if isinstance(fine_tune_block_name, str) else fine_tune_block_name[-1]
            attach_loss_block_name = attach_loss_block_names if isinstance(attach_loss_block_names, str) else attach_loss_block_names[-1]
            observe_block_name = observe_block_names if isinstance(observe_block_names, str) else observe_block_names[-1]
            
            _, _, mses_observe_block = self.quant_block_with_lookahead(
                combined_block,
                copy.deepcopy(preceding_block_outputs),
                input_others,
                q_input=q_input,
                device=device,
                fine_tune_block_name=format_layer_name(fine_tune_block_name),
                attach_loss_block_name=format_layer_name(attach_loss_block_name),
                observe_block_name=format_layer_name(observe_block_name),
            )

            self.model = mv_module_from_gpu(self.model, self.low_cpu_mem_usage)
            torch.cuda.empty_cache()
            
            if not self.disable_wandb:
                convergence_iter = calculate_convergence_iter(mses_observe_block)
                slope_first_tenth = calculate_slope(mses_observe_block, last_iter=len(mses_observe_block) // 10)
                slope = calculate_slope(mses_observe_block)
                average_absolute_change = calculate_average_absolute_change(mses_observe_block, window=1)
                
                learning_curve_plot_title = f"Learning Curve: {observe_block_name}: {fine_tune_block_name} -> {attach_loss_block_name}"
                learning_curve_plot = plot_learning_curve(
                    mses_observe_block, 
                    title=learning_curve_plot_title, 
                    convergence_iter=convergence_iter,
                )
                buffer = io.StringIO()
                learning_curve_plot.write_html(buffer, auto_play=False)
                learning_curve_plot_wandb_html = wandb.Html(buffer)
                buffer.close()
                
                last_mse = mses_observe_block[-1]
                min_mse = min(mses_observe_block)
                min_mse_iter = mses_observe_block.index(min_mse)
                
                logger.info("Evaluating the model on the Wikitext 2 dataset")
                output_dir = os.path.join("tmp_autoround", f"{self.model_name}", f"{fine_tune_block_name}_{observe_block_name}")
                
                original_fine_tune_block = get_module(model, fine_tune_block_name)
                setattr(model, fine_tune_block_name, fine_tune_block)
                self.model.save_pretrained(output_dir)
                self.tokenizer.save_pretrained(output_dir)
                setattr(model, fine_tune_block_name, original_fine_tune_block)
                
                model_args = f"pretrained={output_dir}"
                
                lm_eval_results = lm_eval.simple_evaluate(
                    model="hf", 
                    model_args=model_args,
                    device=device, 
                    tasks="wikitext", 
                    batch_size=self.eval_batch_size,
                    random_seed=self.lm_eval_random_seed,
                    numpy_random_seed=self.lm_eval_numpy_random_seed,
                    torch_random_seed=self.lm_eval_torch_random_seed,
                )
                
                lm_eval_results_df = make_pandas_dataframe_from_lm_eval_results(lm_eval_results)
                wikitext_perplexity = lm_eval_results_df.loc[
                    lm_eval_results_df["Metric"] == "word_perplexity", "Value"
                ].values[0]
                                
                lr_scheduler = "none" if not self.enable_lr_scheduler else "linear_decay"
                log_data.append(
                    [
                        self.model_name, self.bits, self.group_size, 
                        format_layer_name(fine_tune_block_name), format_layer_name(attach_loss_block_name), 
                        format_layer_name(observe_block_name), 
                        self.iters, self.lr, lr_scheduler, self.nsamples, "signed_sgd",
                        wikitext_perplexity, last_mse, min_mse, min_mse_iter, convergence_iter,
                        slope_first_tenth, slope, average_absolute_change, learning_curve_plot_wandb_html
                    ]
                )
        
                # delete the checkpoint
                shutil.rmtree(output_dir)
                
        if not self.disable_wandb:
            table_columns = [
                "model_name", "num_bits", "group_size", "fine_tune_block", "attach_loss_block", "observe_block",
                "num_iters", "learning_rate", "lr_scheduler", "num_fine_tuning_samples", "optimizer", 
                "wikitext_2_perplexity", "last_mse", "min_mse", "min_mse_iter", "convergence_iter",
                "slope_first_tenth", "slope", "avg_abs_change_mse", "leraning_curve_plot"
            ]

            wandb_table = wandb.Table(data=log_data, columns=table_columns)
            wandb.log({"stats_table": wandb_table})

        del q_input
        del input_others
        del inputs

        torch.cuda.empty_cache()

    def save_quantized(self, output_dir=None, format="auto_gptq", inplace=True, **kwargs):
        """Save the quantized model to the specified output directory in the specified format.

        Args:
            output_dir (str, optional): The directory to save the quantized model. Defaults to None.
            format (str, optional): The format in which to save the model. Defaults to "auto_gptq".
            inplace (bool, optional): Whether to modify the model in place. Defaults to True.
            **kwargs: Additional keyword arguments specific to the export format.

        Returns:
            object: The compressed model object.
        """
        if self.low_cpu_mem_usage:
            self.model = self.model.to('cpu')

        if not self.quantized:
            logger.warning("please run autoround.quantize first")
            return
        if format == "fake" or format == "qdq" or self.act_bits <= 8:  ##TODO fix act quantizaiton later
            self.model = self.model.to("cpu")
            self.model.save_pretrained(output_dir)
            if self.tokenizer is not None:
                self.tokenizer.save_pretrained(output_dir)
            return

        from auto_round.export import EXPORT_FORMAT
        backend = format
        format = format.split(":")[0]
        if format not in EXPORT_FORMAT:
            logger.error(f"export format only supports {EXPORT_FORMAT.keys()}")
            exit()
        save_quantized_as_format = EXPORT_FORMAT.get(format)
        serialization_keys = [
            "bits",
            "group_size",
            "sym",
            "data_type",
            "enable_quanted_input",
            "enable_minmax_tuning",
            "data_type",
            "seqlen",
            "train_bs",
            "scale_dtype",
            "lr",
            "minmax_lr",
            "gradient_accumulate_steps",
            "iters",
            "amp",
            "nsamples",
            "low_gpu_mem_usage",
        ]
        if isinstance(self.dataset, str):
            serialization_keys.append("dataset")
        serialization_dict = {}
        for key in serialization_keys:
            serialization_dict[key] = getattr(self, key)
        from .version import __version__

        serialization_dict["autoround_version"] = __version__
        if "scale_dtype" in serialization_dict.keys():
            serialization_dict["scale_dtype"] = str(serialization_dict["scale_dtype"])

        compressed_model = save_quantized_as_format(  ##TODO refine the code
            output_dir,
            model=self.model,
            layer_config=self.layer_config,
            inplace=inplace,
            bits=self.bits,
            group_size=self.group_size,
            sym=self.sym,
            iters=self.iters,
            lr=self.lr,
            minmax_lr=self.minmax_lr,
            enable_minmax_tuning=self.enable_minmax_tuning,
            enable_quanted_input=self.enable_quanted_input,
            scale_dtype=self.scale_dtype,
            tokenizer=self.tokenizer,
            supported_types=self.supported_types,
            data_type=self.data_type,
            serialization_dict=serialization_dict,
            backend=backend,
            multimodal=self.multimodal,
            **kwargs
        )
        return compressed_model

    def get_quantized_layer_names_outside_blocks(self):
        """Gets the names of quantized layers outside blocks in the model.

        Returns:
            list: List of layer names outside blocks.
        """
        if self.layer_config is None or len(self.layer_config) == 0:
            return []

        layer_names = []
        all_layers_in_block = get_layer_names_in_block(self.model, self.supported_types, self.multimodal)

        for key in self.layer_config.keys():
            if key in all_layers_in_block:
                continue
            layer = get_module(self.model, key)
            if layer is None:
                logger.error(f"could not find layer {key} in the model, exit...")
                exit()
            if isinstance(layer, tuple(self.supported_types)) and check_to_quantized(self.layer_config[key]):
                layer_names.append(key)

        return layer_names

    def set_amp_dtype(self):
        self.amp_dtype = torch.float16
        if self.model.dtype != torch.float32:
            self.amp_dtype = self.model.dtype
        if self.device == "cpu" or "hpu" in self.device:
            self.amp_dtype = torch.bfloat16
        if self.amp:
            if self.device == "cpu" and not CpuInfo().bf16:
                self.amp = False
                self.amp_dtype = torch.float32
                self.model = self.model.to(torch.float32)
                logger.warning(
                    f"amp is set to FALSE as the current {self.device} device does not support the 'bf16' data type."
                )
            else:
                self.model = self.model.to(self.amp_dtype)
        else:
            self.amp_dtype = torch.float32
            self.model = self.model.to(torch.float32)

    def get_optimizer(self, optimizer):
        """Returns the specified optimizer. In SignRound, we fix the optimizer.

        Args:
        optimizer: The optimizer to be used.

        Returns:
        The specified optimizer.
        """
        from auto_round.sign_sgd import SignSGD

        return SignSGD

    def get_scaler(self):
        """Returns scaler, in SignRound, no need to use scaler."""
        return None

    def scale_loss_and_backward(self, scaler, loss):
        """Scales the loss and performs backward pass.

        Args:
        scaler: The scaler to be used.
        loss: The loss to be scaled.

        Returns:
        The scaled loss.
        """
        scale_loss = loss * 1000
        scale_loss.backward()
        if is_optimum_habana_available():
            htcore.mark_step()
        return scale_loss

    def step(self, scaler, optimizer, lr_schedule):
        """Performs a step in the optimization process.

        Args:
        scaler: The scaler to be used.
        optimizer: The optimizer for the step.
        lr_schedule: The learning rate schedule.

        Returns:
        None
        """
        optimizer.step()
        # for hpu
        if is_optimum_habana_available():
            htcore.mark_step()
        optimizer.zero_grad()
        if lr_schedule is not None:
            lr_schedule.step()


class AutoOPTRound(AutoRound):
    """Class for automatic rounding-based quantization with optimizers like adamw of a PyTorch model.

    Args:
        model: The PyTorch model to be quantized.
        tokenizer: An optional tokenizer for processing input data.
        bits (int): Number of bits for quantization (default is 4).
        group_size (int): Size of the quantization group (default is 128).
        sym (bool): Whether sym to be used (default is False).
        layer_config (dict): Configuration for weight quantization (default is an empty dictionary).
        enable_full_range (bool): Whether to enable full range quantization (default is False).
        batch_size (int): Batch size for training (default is 8).
        amp (bool): Whether to use automatic mixed precision (default is True).
        device: The device to be used for training (default is "auto").
        lr_scheduler: The learning rate scheduler to be used.
        dataset: The default dataset name (default is "NeelNanda/pile-10k").
        enable_quanted_input (bool): Whether to use quantized input data (default is True).
        enable_minmax_tuning (bool): Whether to enable min-max tuning (default is True).
        lr (float): The learning rate (default is 0.005).
        minmax_lr (float): The learning rate for min-max tuning (default is None).
        low_gpu_mem_usage (bool): Whether to use low GPU memory (default is False).
        low_cpu_mem_usage (bool): Whether to use low CPU memory (default is False).
        iters (int): Number of iterations (default is 200).
        seqlen (int): Length of the sequence.
        nsamples (int): Number of samples (default is 128).
        sampler (str): The sampling method (default is "rand").
        seed (int): The random seed (default is 42).
        nblocks (int): Number of blocks (default is 1).
        gradient_accumulate_steps (int): Number of gradient accumulation steps (default is 1).
        not_use_best_mse (bool): Whether to use mean squared error (default is False).
        dynamic_max_gap (int): The dynamic maximum gap (default is -1).
        data_type (str): The data type to be used (default is "int").
        scale_dtype (str): The data type of quantization scale to be used (default is "float16"), different kernels
                           have different choices.
        act_bits (int): Number of bits for activation quantization. Default is 32.
        act_group_size (int): Group size for activation quantization. Default is None.
        act_sym (bool): Whether to use symmetric activation quantization. Default is None.
        act_dynamic (bool): Whether to use dynamic activation quantization. Default is True.

        **kwargs: Additional keyword arguments.

    Returns:
        The quantized model.
    """

    def __init__(
            self,
            model,
            tokenizer=None,
            model_name: Optional[str] = None,
            bits: int = 4,
            group_size: int = 128,
            sym: bool = False,
            layer_config: dict = {},
            enable_full_range: bool = False,
            batch_size: int = 8,
            amp: bool = True,
            device=None,
            lr_scheduler=None,
            dataset: Union[str, list, tuple, torch.utils.data.DataLoader] = "NeelNanda/pile-10k",
            enable_quanted_input: bool = True,
            enable_minmax_tuning: bool = True,
            lr: float = None,
            minmax_lr: float = None,
            low_gpu_mem_usage: bool = False,
            low_cpu_mem_usage: bool = False,
            iters: int = 200,
            seqlen: int = 2048,
            nsamples: int = 128,
            sampler: str = "rand",
            seed: int = 42,
            nblocks: int = 1,
            gradient_accumulate_steps: int = 1,
            not_use_best_mse: bool = False,
            dynamic_max_gap: int = -1,
            data_type: str = "int",
            scale_dtype: str = "fp16",
            act_bits: int = 32,
            act_group_size: int = None,
            act_sym: bool = None,
            act_dynamic: bool = True,
            optimizer="AdamW",
            **kwargs,
    ):
        super(AutoOPTRound, self).__init__(
            model=model,
            tokenizer=tokenizer,
            model_name=model_name,
            bits=bits,
            group_size=group_size,
            sym=sym,
            layer_config=layer_config,
            enable_full_range=enable_full_range,
            batch_size=batch_size,
            amp=amp,
            device=device,
            lr_scheduler=lr_scheduler,
            dataset=dataset,
            enable_quanted_input=enable_quanted_input,
            enable_minmax_tuning=enable_minmax_tuning,
            lr=lr,
            minmax_lr=minmax_lr,
            low_gpu_mem_usage=low_gpu_mem_usage,
            low_cpu_mem_usage=low_cpu_mem_usage,
            iters=iters,
            seqlen=seqlen,
            nsamples=nsamples,
            sampler=sampler,
            seed=seed,
            nblocks=nblocks,
            gradient_accumulate_steps=gradient_accumulate_steps,
            not_use_best_mse=not_use_best_mse,
            dynamic_max_gap=dynamic_max_gap,
            data_type=data_type,
            scale_dtype=scale_dtype,
            act_bits=act_bits,
            act_group_size=act_group_size,
            act_sym=act_sym,
            act_dynamic=act_dynamic,
            **kwargs,
        )

        self.optimizer = self.get_optimizer(optimizer)

    def get_optimizer(self, optimizer):
        if optimizer is None:
            optimizer = torch.optim.AdamW
        elif isinstance(optimizer, str):
            optimizer = getattr(torch.optim, optimizer)
        else:
            optimizer = optimizer
        return optimizer

    def get_scaler(self):
        scaler = None
        if self.amp and not check_is_cpu(self.device):
            from torch.cuda.amp import GradScaler

            scaler = GradScaler(init_scale=1024, growth_interval=100000)
        return scaler

    def scale_loss_and_backward(self, scaler, loss):
        if scaler is not None:
            loss = scaler.scale(loss)

        loss.backward()
        if is_optimum_habana_available():
            htcore.mark_step()
        return loss

    def step(self, scaler, optimizer, lr_schedule):
        if scaler is not None:
            scaler.step(optimizer)
            optimizer.zero_grad()
            if lr_schedule is not None:
                lr_schedule.step()
            scaler.update()
        else:
            optimizer.step()
            optimizer.zero_grad()
            if lr_schedule is not None:
                lr_schedule.step()
        if is_optimum_habana_available():
            htcore.mark_step()


class AutoAdamRound(AutoOPTRound):
    """Class for automatic rounding-based quantization with optimizers like adamw of a PyTorch model.
    The default lr has been changed.

    Args:
        model: The PyTorch model to be quantized.
        tokenizer: An optional tokenizer for processing input data.
        bits (int): Number of bits for quantization (default is 4).
        group_size (int): Size of the quantization group (default is 128).
        sym (str): Whether symmetric quantization to be used (default is False).
        layer_config (dict): Configuration for weight quantization (default is an empty dictionary).
        enable_full_range (bool): Whether to enable full range quantization (default is False).
        batch_size (int): Batch size for training (default is 8).
        amp (bool): Whether to use automatic mixed precision (default is True).
        device: The device to be used for training (default is "auto").
        lr_scheduler: The learning rate scheduler to be used.
        dataset (Union[str, list, tuple, torch.utils.data.DataLoader]):
                The default dataset name (default is "NeelNanda/pile-10k").
        enable_quanted_input (bool): Whether to use quantized input data (default is True).
        enable_minmax_tuning (bool): Whether to enable min-max tuning (default is True).
        lr (float): The learning rate (default is 0.005).
        minmax_lr (float): The learning rate for min-max tuning (default is None).
        low_gpu_mem_usage (bool): Whether to use low GPU memory (default is False).
        low_cpu_mem_usage (bool): Whether to use low CPU memory (default is False).
        iters (int): Number of iterations (default is 200).
        seqlen (int): Length of the sequence.
        nsamples (int): Number of samples (default is 128).
        sampler (str): The sampling method (default is "rand").
        seed (int): The random seed (default is 42).
        nblocks (int): Number of blocks (default is 1).
        gradient_accumulate_steps (int): Number of gradient accumulation steps (default is 1).
        not_use_best_mse (bool): Whether to use mean squared error (default is False).
        dynamic_max_gap (int): The dynamic maximum gap (default is -1).
        data_type (str): The data type to be used (default is "int").
        optimizer: string or object
        scale_dtype (str): The data type of quantization scale to be used (default is "float16"), different kernels
                           have different choices.
        act_bits (int): Number of bits for activation quantization. Default is 32.
        act_group_size (int): Group size for activation quantization. Default is None.
        act_sym (bool): Whether to use symmetric activation quantization. Default is None.
        act_dynamic (bool): Whether to use dynamic activation quantization. Default is True.

    Returns:
        The quantized model.
    """

    def __init__(
            self,
            model,
            tokenizer=None,
            model_name: Optional[str] = None,
            bits: int = 4,
            group_size: int = 128,
            sym: bool = False,
            layer_config: dict = {},
            enable_full_range: bool = False,
            batch_size: int = 8,
            amp: bool = True,
            device=None,
            lr_scheduler=None,
            dataset: Union[str, list, tuple, torch.utils.data.DataLoader] = "NeelNanda/pile-10k",
            enable_quanted_input: bool = True,
            enable_minmax_tuning: bool = True,
            lr: float = None,
            minmax_lr: float = None,
            low_gpu_mem_usage: bool = False,
            low_cpu_mem_usage: bool = False,
            iters: int = 200,
            seqlen: int = 2048,
            nsamples: int = 128,
            sampler: str = "rand",
            seed: int = 42,
            nblocks: int = 1,
            gradient_accumulate_steps: int = 1,
            not_use_best_mse: bool = False,
            dynamic_max_gap: int = -1,
            data_type: str = "int",
            scale_dtype: str = "fp16",
            act_bits: int = 32,
            act_group_size: int = None,
            act_sym: bool = None,
            act_dynamic: bool = True,
            optimizer="AdamW",
            **kwargs,
    ):
        super(AutoAdamRound, self).__init__(
            model=model,
            tokenizer=tokenizer,
            model_name=model_name,
            bits=bits,
            group_size=group_size,
            sym=sym,
            layer_config=layer_config,
            enable_full_range=enable_full_range,
            batch_size=batch_size,
            amp=amp,
            device=device,
            lr_scheduler=lr_scheduler,
            dataset=dataset,
            enable_quanted_input=enable_quanted_input,
            enable_minmax_tuning=enable_minmax_tuning,
            lr=lr,
            minmax_lr=minmax_lr,
            low_gpu_mem_usage=low_gpu_mem_usage,
            low_cpu_mem_usage=low_cpu_mem_usage,
            iters=iters,
            seqlen=seqlen,
            nsamples=nsamples,
            samples=sampler,
            seed=seed,
            nblocks=nblocks,
            gradient_accumulate_steps=gradient_accumulate_steps,
            not_use_best_mse=not_use_best_mse,
            dynamic_max_gap=dynamic_max_gap,
            data_type=data_type,
            scale_dtype=scale_dtype,
            act_bits=act_bits,
            act_group_size=act_group_size,
            act_sym=act_sym,
            act_dynamic=act_dynamic,
            optimizer=optimizer,
            **kwargs,
        )


