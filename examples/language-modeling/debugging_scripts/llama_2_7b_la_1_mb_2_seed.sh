# python3 main.py \
#     --model_name meta-llama/llama-2-7b-hf  \
#     --bits 4 \
#     --group_size 128 \
#     --enable_lr_scheduler \
#     --nsamples 512 \
#     --iters 1000 \
#     --nblocks 1 \
#     --num_lookahead_blocks 0 \
#     --tasks wikitext \
#     --seed 0 \
#     --wandb_project_name khas-thesis-autoround-debug

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --tasks wikitext \
    --seed 0 \
    --wandb_project_name khas-thesis-autoround-debug


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --tasks wikitext \
    --seed 1 \
    --wandb_project_name khas-thesis-autoround-debug

python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --tasks wikitext \
    --seed 2 \
    --wandb_project_name khas-thesis-autoround-debug


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --tasks wikitext \
    --seed 3 \
    --wandb_project_name khas-thesis-autoround-debug


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 2 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --seed 0 \
    --wandb_project_name khas-thesis-autoround-debug


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 2 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --seed 1 \
    --wandb_project_name khas-thesis-autoround-debug


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 2 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --seed 2 \
    --wandb_project_name khas-thesis-autoround-debug


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 2 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --seed 3 \
    --wandb_project_name khas-thesis-autoround-debug
    