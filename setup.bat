@echo off
set ver_py=3.8
set print_ouput=Installed successfully

if exist .conda (
  conda activate ./.conda
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  cls
  echo %print_ouput%
) else (
  conda create --yes --prefix ./.conda python=%ver_py%
  conda activate ./.conda
  pip install -r requirements.txt
  cls
  echo %print_ouput%
)


