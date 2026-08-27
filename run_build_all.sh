set -euox pipefail

. .venv/bin/activate

python -m antennenvergleich.run_0_s1p
python -m antennen.mazzoni_baby_loop_HB0SM.h_field.h_field_data
python -m antennen.mazzoni_midi_loop_HB0SM.h_field.h_field_data
python -m antennen.mazzoni_midi_loop_HB9BPO.h_field.h_field_data
python -m antennenvergleich.run_2_html

uv build --wheel
