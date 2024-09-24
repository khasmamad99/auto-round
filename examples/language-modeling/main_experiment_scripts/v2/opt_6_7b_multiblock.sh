python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 2 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-main \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 3 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-main \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 4 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-main \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 5 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-main \
    --low_gpu_mem_usage
