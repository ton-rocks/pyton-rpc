#!/bin/bash


docker build -t ton-rocks-api-image . --build-arg core_count=$((`grep processor /proc/cpuinfo | wc -l` * 2 + 1 ))
