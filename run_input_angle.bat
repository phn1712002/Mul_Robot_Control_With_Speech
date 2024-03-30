@echo off
if exist .conda (
  conda activate ./.conda
  python -m other
)


