#!/bin/sh
echo *** INT64 ***
.
1
d
a
echo *** SINGLE CPU - INT64 ***
stress-ng --cpu 1 --cpu-method int64 -t 10s --metrics-brief
echo *** ALL CPUs - INT64 ***
stress-ng --cpu 0 --cpu-method int64 -t 10s --metrics-brief
echo *** SINGLE CPU - MATRIX MULT ***
stress-ng --cpu 1 --cpu-method matrix -t 10s --metrics-brief
echo *** ALL CPUs - MATRIX MULT ***
stress-ng --cpu 0 --cpu-method matrix -t 10s --metrics-brief
echo *** SINGLE CPU - FFT ***
stress-ng --cpu 1 --cpu-method fft -t 10s --metrics-brief
echo *** ALL CPUs - FFT ***
stress-ng --cpu 0 --cpu-method fft -t 10s --metrics-brief
