set -euox pipefail

. .venv/bin/activate

python -m antennenvergleich.run_0_s1p
python -m antennenvergleich.run_1_h_field
python -m antennenvergleich.run_2_html

uv build --wheel
