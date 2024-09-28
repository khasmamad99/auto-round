python3 main.py \
    --model_name facebook/opt-6.7b  \
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
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name facebook/opt-6.7b  \
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
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name facebook/opt-6.7b  \
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
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name facebook/opt-6.7b  \
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
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name facebook/opt-6.7b  \
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
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-ablations


python3 main.py \
    --model_name facebook/opt-6.7b  \
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
    --low_gpu_mem_usage \
    --wandb_project_name khas-thesis-ablations