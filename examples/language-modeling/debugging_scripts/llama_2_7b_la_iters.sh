python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 100 \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --seed 0


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 500 \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --seed 0


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 2000 \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --seed 0


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 100 \
    --nblocks 1 \
    --num_lookahead_blocks 2 \
    --tasks wikitext \
    --seed 0


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 500 \
    --nblocks 1 \
    --num_lookahead_blocks 2 \
    --tasks wikitext \
    --seed 0


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 2000 \
    --nblocks 1 \
    --num_lookahead_blocks 2 \
    --tasks wikitext \
    --seed 0