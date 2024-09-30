python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 1411 \
    --iters 1000 \
    --nblocks 2 \
    --block_step_size 1 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-ablations \
    --low_gpu_mem_usage


# python3 main.py \
#     --model_name meta-llama/llama-2-7b-hf  \
#     --bits 4 \
#     --group_size 128 \
#     --eval_bs 32 \
#     --lr 1e-3 \
#     --enable_lr_scheduler \
#     --nsamples 1024 \
#     --iters 1000 \
#     --nblocks 2 \
#     --block_step_size 1 \
#     --num_lookahead_blocks 0 \
#     --wandb_project_name khas-thesis-ablations \
#     --low_gpu_mem_usage


# python3 main.py \
#     --model_name meta-llama/llama-2-7b-hf  \
#     --bits 4 \
#     --group_size 128 \
#     --eval_bs 32 \
#     --lr 1e-3 \
#     --enable_lr_scheduler \
#     --nsamples 768 \
#     --iters 1000 \
#     --nblocks 2 \
#     --block_step_size 1 \
#     --num_lookahead_blocks 0 \
#     --wandb_project_name khas-thesis-ablations \
#     --low_gpu_mem_usage



python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 256 \
    --iters 1000 \
    --nblocks 2 \
    --block_step_size 1 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-ablations


# python3 main.py \
#     --model_name meta-llama/llama-2-7b-hf  \
#     --bits 4 \
#     --group_size 128 \
#     --eval_bs 32 \
#     --lr 1e-3 \
#     --enable_lr_scheduler \
#     --nsamples 128 \
#     --iters 1000 \
#     --nblocks 2 \
#     --block_step_size 1 \
#     --num_lookahead_blocks 0 \
#     --wandb_project_name khas-thesis-ablations


# python3 main.py \
#     --model_name meta-llama/llama-2-7b-hf  \
#     --bits 4 \
#     --group_size 128 \
#     --eval_bs 32 \
#     --lr 1e-3 \
#     --enable_lr_scheduler \
#     --nsamples 1024 \
#     --iters 1000 \
#     --nblocks 2 \
#     --block_step_size 1 \
#     --num_lookahead_blocks 0 \
#     --wandb_project_name khas-thesis-ablations


# python3 main.py \
#     --model_name meta-llama/llama-2-7b-hf  \
#     --bits 4 \
#     --group_size 128 \
#     --eval_bs 32 \
#     --lr 1e-3 \
#     --enable_lr_scheduler \
#     --nsamples 512 \
#     --iters 1000 \
#     --nblocks 2 \
#     --block_step_size 1 \
#     --num_lookahead_blocks 0 \
#     --wandb_project_name khas-thesis-ablations