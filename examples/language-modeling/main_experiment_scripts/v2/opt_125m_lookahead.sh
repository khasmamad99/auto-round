# python3 main.py \
#     --model_name facebook/opt-125m  \
#     --bits 4 \
#     --group_size 128 \
#     --enable_lr_scheduler \
#     --nsamples 512 \
#     --iters 1000 \
#     --wandb_project_name khas-thesis-main \
#     --nblocks 1 \
#     --num_lookahead_blocks 0 &

# python3 main.py \
#     --model_name facebook/opt-125m  \
#     --bits 4 \
#     --group_size 128 \
#     --enable_lr_scheduler \
#     --nsamples 512 \
#     --iters 1000 \
#     --wandb_project_name khas-thesis-main \
#     --nblocks 1 \
#     --num_lookahead_blocks 1

# wait


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 2 &

python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 3

wait


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 4


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 5


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 6


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 7


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 8


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 9


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 10


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 1000 \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 10


python3 main.py \
    --model_name facebook/opt-125m  \
    --bits 4 \
    --group_size 128 \
    --enable_lr_scheduler \
    --nsamples 512 \
    --iters 10 --disable_wandb \
    --wandb_project_name khas-thesis-main \
    --nblocks 1 \
    --num_lookahead_blocks 11
