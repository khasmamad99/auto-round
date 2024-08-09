# python3 main.py \
#     --model_name facebook/opt-125m \
#     --bits 4 \
#     --group_size 128 \
#     --lr 5e-4 \
#     --nsamples 512 \
#     --iters 1000 \
#     --isolation_experiment_v2 \
#     --fine_tune_block_idx 1 \
#     --observe_block_idx 4 \
#     --disable_eval


python3 main.py \
    --model_name facebook/opt-125m \
    --bits 4 \
    --group_size 128 \
    --lr 5e-4 \
    --nsamples 512 \
    --iters 1000 \
    --isolation_experiment_v2 \
    --fine_tune_block_idx 4 \
    --observe_block_idx 7 \
    --disable_eval


# python3 main.py \
#     --model_name facebook/opt-125m \
#     --bits 4 \
#     --group_size 128 \
#     --lr 5e-4 \
#     --nsamples 512 \
#     --iters 1000 \
#     --isolation_experiment_v2 \
#     --fine_tune_block_idx 7 \
#     --observe_block_idx 10 \
#     --disable_eval
