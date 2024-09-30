python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 50 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 2 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 100 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 2 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 2 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 500 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 2 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 750 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 2 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name meta-llama/llama-2-7b-hf  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1500 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 2 \
    --wandb_project_name khas-thesis-ablations