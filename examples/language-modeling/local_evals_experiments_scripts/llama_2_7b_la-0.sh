python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --nblocks 1 \
    --num_lookahead_blocks 0 \
    --block_step_size 1 \
    --eval_after_each_optimization \
    --disable_eval \
    --wandb_project_name khas-thesis-local-evals
    