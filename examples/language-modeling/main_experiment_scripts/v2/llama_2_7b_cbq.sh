python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 2 \
    --block_step_size 1 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-main

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 3 \
    --block_step_size 1 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-main

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 4 \
    --block_step_size 1 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-main

# python3 main.py \
#     --model_name meta-llama/llama-2-7b-hf  \
#     --bits 4 \
#     --group_size 128 \
#     --eval_bs 32 \
#     --enable_lr_scheduler \
#     --nsamples 512 \
#     --iters 1000 \
#     --nblocks 5 \
#     --block_step_size 1 \
#     --num_lookahead_blocks 0 \
#     --wandb_project_name khas-thesis-main