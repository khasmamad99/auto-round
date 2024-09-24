python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 256 \
    --iters 1000 \
    --nblocks 3 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 1024 \
    --iters 1000 \
    --nblocks 3 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity \
    --low_gpu_mem_usage
