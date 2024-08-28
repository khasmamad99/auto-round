python3 main.py \
    --model_name facebook/opt-1.3b  \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --adam \
    --tasks wikitext

python3 main.py \
    --model_name facebook/opt-1.3b  \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --adam \
    --tasks wikitext

python3 main.py \
    --model_name facebook/opt-1.3b  \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 2 \
    --adam \
    --tasks wikitext

python3 main.py \
    --model_name facebook/opt-1.3b  \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 3 \
    --adam \
    --tasks wikitext
