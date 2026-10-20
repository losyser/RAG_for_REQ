@echo off
set PYTHONPATH=
set PYTHONIOENCODING=utf-8
rem faiss-cpu 1.13 + torch 2.11 crash (access violation) when OpenMP thread count is left at default
set OMP_NUM_THREADS=8
cd /d D:\cooling_rag_multigranular\cooling_rag_multigranular
D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe %*
