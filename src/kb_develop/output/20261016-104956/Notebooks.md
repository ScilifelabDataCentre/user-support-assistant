https://serve.scilifelab.se/docs/notebooks/

## Introduction

SciLifeLab Serve allows to run web-browser based integrated development environments (IDEs). Currently, Jupyter Lab, RStudio, and VSCode are supported. These can be created in any *Project* that a user has created by selecting the corresponding card in the interface. Each IDE instance is automatically deleted after seven days. The data in the persistent volume is not deleted and can be accessed again when a new instance is created.

IDEs are an experimental feature on SciLifeLab Serve, hence not well-documented.

## Available storage

Each project on SciLifeLab Serve has a persistent volume (folder) attached to it, called 'project-vol'. All IDE instances created within that project can get access to this persistent volume. Please make sure to save all your data files, script files, output from computations, etc. inside 'project-vol'; the files located elsewhere can be deleted at any point. By default each project will have 1 GB storage capacity, and you can yourself increase that to 5 GB. If this is still not enough, you can request more by emailing us: serve@scilifelab.se. We will accommodate your request if we have enough storage available on our cluster.

## Assigned CPU, GPU, RAM

Each IDE instance receives 2 vCPU and 4 GB of memory/RAM by default. If you need more computational resources, we can assign up to 12 vCPU and 48 GB of memory/RAM. In addition, you can launch an IDE instance with access to an NVIDIA A40 GPU. Get in touch with us (serve@scilifelab.se) with a motivated request if you need more computational resources, and we will accommodate your request if there is sufficient room on our cluster.

## Working together with collaborators

You can add collaborators to the project (go to Settings -> Access) to use IDEs collaboratively or to allow them to inspect your results. Each IDE instance can be set to be visible only to the owner (permissions set to *Private*) or to everyone who has been added to a project (permissions set to *Project*).

## Different environments 

When creating Jupyter Lab and RStudio instances you can sometimes also select an *Environment*. Environments differ in terms of pre-installed packaged, IDE versions, and included datasets. In other words, depending on the selected environments, you may have some but not other Python or R packages pre-installed (you can still install your more packages in any instance) and some datasets may be included (you can still download other datasets in any instance).

We offer four Jupyter Lab environments to serve different needs:

- _Jupyter Lab Minimal (default)_: A lightweight environment with essential features.

- _Jupyter Lab Data Science_: Includes essential tools and libraries for data analysis and visualization.

- _Jupyter Lab PyTorch_: Preconfigured with the PyTorch package for deep learning and machine learning tasks.

- _Jupyter Lab TensorFlow_: Preconfigured with the TensorFlow package for deep learning and machine learning tasks.

You are welcome to select the one that best fits your requirements.
