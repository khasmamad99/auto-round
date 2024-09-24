python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-main 

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --wandb_project_name khas-thesis-main \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 2 \
    --wandb_project_name khas-thesis-main \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 3 \
    --wandb_project_name khas-thesis-main \
    --low_gpu_mem_usage

# python3 main.py \
#     --model_name facebook/opt-6.7b  \
#     --bits 4 \
#     --group_size 128 \
#     --enable_lr_scheduler \
#     --nsamples 512 \
#     --iters 1000 \
#     --nblocks 1 \
#     --num_lookahead_blocks 4 \
#     --wandb_project_name khas-thesis-main \
#     --low_gpu_mem_usage
