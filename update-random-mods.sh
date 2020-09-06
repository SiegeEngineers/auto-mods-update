#! /bin/bash

cd "$(dirname "$(realpath "$0")")";

rm -rf mods
mkdir -p mods/random-costs/resources/_common/dat
mkdir -p mods/random-tech-costs/resources/_common/dat
mkdir -p mods/random-unit-costs/resources/_common/dat

./create-data-mod random-costs empires2_x2_p1.dat ./mods/random-costs/resources/_common/dat/empires2_x2_p1.dat
./create-data-mod random-tech-costs empires2_x2_p1.dat ./mods/random-tech-costs/resources/_common/dat/empires2_x2_p1.dat
./create-data-mod random-unit-costs empires2_x2_p1.dat ./mods/random-unit-costs/resources/_common/dat/empires2_x2_p1.dat

rm -f random-costs.zip
rm -f random-tech-costs.zip
rm -f random-unit-costs.zip

cd mods/random-costs
zip -r ../../random-costs.zip *
cd ../..

cd mods/random-tech-costs
zip -r ../../random-tech-costs.zip *
cd ../..

cd mods/random-unit-costs
zip -r ../../random-unit-costs.zip *
cd ../..

source ./venv/bin/activate
./updateMods.py
