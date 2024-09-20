python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 6 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model &

python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 7 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model

wait

python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 8192 \
    --dataset allenai/c4 \
    --iters 1000 \
    --nblocks 8 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model &

python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 9 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model

wait

python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 10 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 11 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 8192 \
    --iters 1000 \
    --nblocks 12 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-autoround-complete-model

