# python3 main.py \
#     --model_name meta-llama/llama-2-7b-hf  \
#     --bits 3 \
#     --group_size 128 \
#     --eval_bs 32 \
#     --lr 1e-3 \
#     --enable_lr_scheduler \
#     --nsamples 512 \
#     --iters 1000 \
#     --nblocks 1 \
#     --block_step_size 1 \
#     --num_lookahead_blocks 0 \
#     --wandb_project_name khas-thesis-main \
#     --seed 100

# python3 main.py \
#     --model_name meta-llama/llama-2-7b-hf  \
#     --bits 3 \
#     --group_size 128 \
#     --eval_bs 32 \
#     --enable_lr_scheduler \
#     --nsamples 512 \
#     --iters 1000 \
#     --nblocks 1 \
#     --block_step_size 1 \
#     --num_lookahead_blocks 1 \
#     --wandb_project_name khas-thesis-main \
#     --seed 100

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 3 \
    --group_size 128 \
    --eval_bs 32 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 2 \
    --wandb_project_name khas-thesis-main \
    --seed 100

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 3 \
    --group_size 128 \
    --eval_bs 32 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 3 \
    --wandb_project_name khas-thesis-main \
    --seed 100
