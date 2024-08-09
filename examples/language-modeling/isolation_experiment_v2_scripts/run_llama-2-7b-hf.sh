python3 main.py \
    --model_name meta-llama/llama-2-7b-hf \
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
    --model_name meta-llama/llama-2-7b-hf \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --isolation_experiment_v2 \
    --fine_tune_block_idx 14 \
    --observe_block_idx 17 \
    --disable_eval \
    --low_gpu_mem_usage


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --isolation_experiment_v2 \
    --fine_tune_block_idx 27 \
    --observe_block_idx 30 \
    --disable_eval \
    --low_gpu_mem_usage
