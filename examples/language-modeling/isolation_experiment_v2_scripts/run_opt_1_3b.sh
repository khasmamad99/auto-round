python3 main.py \
    --model_name facebook/opt-1.3b \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --isolation_experiment_v2 \
    --fine_tune_block_idx 1 \
    --observe_block_idx 4 \
    --disable_eval \
    --low_gpu_mem_usage

python3 main.py \
    --model_name facebook/opt-1.3b \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --isolation_experiment_v2 \
    --fine_tune_block_idx 10 \
    --observe_block_idx 13 \
    --disable_eval \
    --low_gpu_mem_usage


python3 main.py \
    --model_name facebook/opt-1.3b \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --isolation_experiment_v2 \
    --fine_tune_block_idx 19 \
    --observe_block_idx 22 \
    --disable_eval \
    --low_gpu_mem_usage
