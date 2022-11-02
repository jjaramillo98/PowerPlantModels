#!/usr/bin/env sh

echo "Installing dependencies for pre-commit."

pip install pre-commit

pre-commit install

echo "Finished Configuration pre-commit hooks."
