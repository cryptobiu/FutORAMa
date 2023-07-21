# FutORAMa

Welcome to the FutORAMa repository! This project allows you to test the functionality of the novel implementaion of Oblivious RAM - FutORAMa, on your Windows 11 machine using Python version 3.10.5. To ensure the smooth execution of the test, please follow the instructions below.

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installations)
- [Run Instructions](#run-instructions)
- [Usage](#usage)
- [License](#license)

## Introduction
Oblivious RAM (ORAM) is a general-purpose technique for hiding memory access patterns. This
is a fundamental task underlying many secure computation applications.

This project is an implementation of FutORAMa, a groundbreaking Oblivious RAM protocol that was published in ACM CCS 2023. FutORAMa introduces novel optimizations to the Oblivious RAM construction, making it more efficient.

## Prerequisites
- Windows 11 operating system.
- Python version 3.10.5 installed on your machine.

## Installations
1. Clone this repository to your local machine using the following command:

    `git clone https://github.com/cryptobiu/FutORAMa`

2. Install the necessary libraries by executing the following command:

    `pip install pycryptodomex==3.15.0`

    `pip install numpy==1.23.1`

## Run Instructions
Now that you have installed the required dependencies, you are all set to run the Oblivious RAM test. To execute the test, use the following command:

    python main.py

You will see the two types of tests available:

    Enter test type:
    1) Real ORAM accesses
    2) Simulated accesses to calculate the approximate bandwidth and round-trips


1. **Real ORAM accesses**: This test executes accesses to an Oblivious RAM implementation. However, please note the following considerations:
- The test uses the local RAM as the server, but you can implement the `local_RAM` model differently to suit your needs.
- Some Python functions are used for research purposes, and you can replace them with more efficient code (e.g., utilizing the `numpy` library) to boost performance.

2. **Simulated accesses**: This test only simulates accesses and calculates the approximate bandwidth and round-trips without using all the memory. It provides faster performance results without executing real accesses. Please note that this test is an upper-bound approximation.

## Acknowledgments
The implementation of FutORAMa in this repository is based on the groundbreaking research work of Dr. Gilad Ashrov, Dr. Ilan Komargodski, and Yehuda Michelson. Their contributions to the field of Oblivious RAM and the publication of the FutORAMa protocol in ACM CCS 2023 have significantly advanced the state-of-the-art in secure memory access. This implementation leverages their innovative optimizations, demonstrating the practical realization of the FutORAMa protocol.