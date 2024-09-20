python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --dataset allenai/c4 \
    --nsamples 8192 \
    --iters 10 --disable_wandb \
    --nblocks 1 \
    --num_lookahead_blocks 5 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model &

python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --dataset allenai/c4 \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 6 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model

wait

python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --dataset allenai/c4 \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 7 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model &

python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --dataset allenai/c4 \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 8 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model

wait

python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --dataset allenai/c4 \
    --nsamples 8192 \
    --iters 25 --disable_wandb \
    --nblocks 1 \
    --num_lookahead_blocks 9 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --dataset allenai/c4 \
    --nsamples 8192 \
    --iters 25 --disable_wandb \
    --nblocks 1 \
    --num_lookahead_blocks 10 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --dataset allenai/c4 \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 11 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model

