python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-2 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 2 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-2 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 3 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-2 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 4 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-2 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 5 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity \
    --low_gpu_mem_usage
