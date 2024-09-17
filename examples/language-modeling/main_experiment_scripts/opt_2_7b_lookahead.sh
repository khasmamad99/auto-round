python3 main.py \
    --model_name facebook/opt-2.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --tasks wikitext \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-2.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 1 \
    --tasks wikitext \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-2.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 2 \
    --tasks wikitext \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-2.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 3 \
    --tasks wikitext \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-2.7b  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 4 \
    --tasks wikitext \
    --low_gpu_mem_usage
