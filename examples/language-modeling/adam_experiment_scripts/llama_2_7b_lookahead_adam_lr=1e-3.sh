python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --adam \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --adam \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --adam \
    --nblocks 1 \
    --num_lookahead_blocks 2 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --adam \
    --nblocks 1 \
    --num_lookahead_blocks 3 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --adam \
    --nblocks 1 \
    --num_lookahead_blocks 4 \
    --tasks wikitext \
    --wandb_project_name khas-thesis-autoround-hyperparam-sensitivity
