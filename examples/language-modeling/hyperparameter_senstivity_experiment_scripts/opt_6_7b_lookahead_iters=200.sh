python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 1 \
    --num_lookahead_blocks 2 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 1 \
    --num_lookahead_blocks 3 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-6.7b  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 1 \
    --num_lookahead_blocks 4 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity \
    --low_gpu_mem_usage
