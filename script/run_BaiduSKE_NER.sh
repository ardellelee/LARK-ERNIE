#!/usr/bin/env bash

set -eux

export FLAGS_sync_nccl_allreduce=1
export CUDA_VISIBLE_DEVICES=0
export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

export MODEL_PATH="/home/liyue/Data/ERNIE_stable-1.0.1"
export TASK_DATA_PATH="/home/liyue/Data/ernie_processed/ner57"

python -u run_sequence_labeling.py \
                   --use_cuda true \
                   --do_train true \
                   --do_val true \
                   --do_test true \
                   --batch_size 16 \
                   --init_pretraining_params ${MODEL_PATH}/params \
                   --num_labels 65 \
                   --label_map_config ${TASK_DATA_PATH}/label_map_entities_57.json \
                   --train_set ${TASK_DATA_PATH}/train.tsv \
                   --dev_set ${TASK_DATA_PATH}/dev0.tsv \
                   --test_set ${TASK_DATA_PATH}/dev.tsv \
                   --vocab_path config/vocab.txt \
                   --ernie_config_path config/ernie_config.json \
                   --checkpoints ./checkpoints/baiduSKE_ner57 \
                   --save_steps 10000 \
                   --weight_decay  0.01 \
                   --warmup_proportion 0.0 \
                   --validation_steps 10000 \
                   --epoch  10 \
                   --max_seq_len 256 \
                   --learning_rate 5e-5 \
                   --skip_steps 1000 \
                   --num_iteration_per_drop_scope 1 \
                   --random_seed 1 \
                   --save_log true \
                   --log_path ./logs/baiduSKE_ner57.txt

