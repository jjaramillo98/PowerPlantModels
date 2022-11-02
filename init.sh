#!/usr/bin/env sh

cd ./DTDL-Validator/DTDLValidator-Sample
dotnet pack
cd ./DTDLValidator
dotnet tool install --global --add-source ./nupkg DTDLValidator

cd ../../..

echo "Installing dependencies for pre-commit."

pip install pre-commit

pre-commit install

echo "Finished Configuration pre-commit hooks."
