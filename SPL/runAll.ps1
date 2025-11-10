# PowerShell version of runAll.sh
# This script runs the same commands as runAll.sh but natively in PowerShell

# Uncomment the sections you want to run:

python generate_multiwave_yml.py 430 439 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 440 459 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 460 479 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 480 499 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 500 519 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 520 539 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 540 559 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 560 579 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 580 599 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 600 619 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 620 639 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 640 659 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 660 679 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 680 699 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 700 719 5
python main_simul.py params_spl_multiwave.yml
python generate_multiwave_yml.py 720 730 5
python main_simul.py params_spl_multiwave.yml

