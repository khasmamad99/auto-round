python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --tasks wikitext 

python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --tasks wikitext

python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 2 \
    --tasks wikitext

python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 10 --disable_wandb \
    --nblocks 1 \
    --num_lookahead_blocks 3 \
    --tasks wikitext

python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 4 \
    --tasks wikitext
