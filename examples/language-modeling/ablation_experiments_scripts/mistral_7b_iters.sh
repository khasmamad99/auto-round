python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 3 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1500 \
    --nblocks 1 \
    --block_step_size 1 \
    --num_lookahead_blocks 3 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 3 \
    --block_step_size 3 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1500 \
    --nblocks 3 \
    --block_step_size 3 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 200 \
    --nblocks 3 \
    --block_step_size 1 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name mistralai/Mistral-7B-v0.1  \
    --bits 4 \
    --group_size 128 \
    --eval_bs 32 \
    --lr 1e-3 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1500 \
    --nblocks 3 \
    --block_step_size 1 \
    --num_lookahead_blocks 0 \
    --wandb_project_name khas-thesis-ablations