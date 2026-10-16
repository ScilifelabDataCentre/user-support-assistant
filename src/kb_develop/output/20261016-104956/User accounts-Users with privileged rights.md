https://serve.scilifelab.se/docs/user-accounts/privileged-users/

## Introduction

SciLifeLab Serve has a special category of users who have privileged rights, that is different limits or access to additional functionality. This is an experimental feature that we introduced in autumn 2026 and are currently evaluating. This documentation page describes the additional functionality for privileged users and how to make use of it.

### Becoming a privileged user

The privileged user category is reserved to users that need to work with the platform significantly more often than the regular users. This can be, for example, a user from a SciLifeLab infrastructure unit that is making use of the platform. Another example is a teacher that is using SciLifeLab Serve functionality to run labs during their course. We make sure that you already know the platform quite well before we promote your account to a privileged user account. Send us an email to serve@scilifelab.se if you would like to apply to become a privileged user.

### Assignment as a privileged user of a particular project

You will automatically have access to privileged user features described below for all projects that you created yourself. For the projects where you are invited by others the user needs to explicitly toggle the option to allow you to have privileged access rights to that project.

## Limits on the number of projects and applications

Privileged users can create an unlimited number of projects and an unlimited number of applications within each project.

## Managing Storage within a project

Privileged users are allowed to increase the storage allocated to their project beyond the limit for regular users (5 GB as of autumn 2026). In order to do that, go into *Project settings* -> *Storage*. Under *Increase volume size* you can decide what the limit should be, then click "Update size". Currently, we allow privileged users to increase the limit up to 50 GB. If you need more than that, you can make use of the *Request more* option, and we will consider your request as usually.

## Managing Hardware within a project

Privileged users are allowed to launch applications with more than the default 2 vCPU and 4 GB RAM and with a GPU without prior approval from the SciLifeLab Serve team. In order to do that, you first need to create a corresponding Hardware option in a particular project where you want to use it. Go to *Project settings* -> *Hardware*. Fill out the form for creating a new Hardware option with the the values that you wish to have. We recommend giving each Hardware option a name that helps to easily identify what it entails (for example, "4 vCPU, 8 GB RAM" would be a good name). The values you need to set are: *CPU limit* that determines the maximum allowed CPUs the app is allowed to use; as *Memory limit* that determines the maximum allowed RAM the app is allowed to use. Unless you have a good reason, the value of *Ephemeral storage* should stay as default.

The *CPU limit* is set in millicores (*m*). The default value 2000m equals 2 virtual CPUs, so if you would like to have 5 virtual CPUs, set it to 5000m. The *Memory limit* is set in Gibibytes (*Gi*). The default value 4Gi equals 4 Gibibytes. In both cases make sure to have the "m" and "Gi" after the number in the corresponding field. For ephemeral storage make sure to have "Mi" (Mebibyte) after the value. The value of *GPU* is set to either 0 or 1 where 1 would mean that an NVIDIA A40 GPU will be assigned.

Once the Hardware option is created, you can use it for a new application that you launch or for an application that is already running by choosing it among the Hardware options in the settings form. The same Hardware options will appear for applications under the Develop category (such as JupyterLab and RStudio) and your own applications under the Serve category (such as Streamlit, Gradio, etc.)

Note that all members of a project will be able to select all Hardware options that you create.

## Managing Environments within a project

The notebooks on SciLifeLab Serve can be launched with different so-called Environments. An Environment is the container image an app runs. Environments are useful if you want to have different pre-installed packaged, IDE versions, or included datasets when you launch a notebook. See [this documentation page](https://serve.scilifelab.se/docs/notebooks/) for some more info about Environments.

Privileged users are allowed to create and use additional Environments for projects without prior approval from the SciLifeLab Serve team. To create a new environment, go to *Project settings* -> *Environments*. Fill out the form to create a new Environment option. Be careful when filling out the form (for example, do not put any extra dots etc.) because the values will be put together to create the full image address. For each Environment that you create you also choose an app type for which it should be available (i.e. notebook type). For example, if you can create an Environment for JupyterLab, it will become an option when the user in the project launches a JupyterLab instance.

Note that all members of a project will be able to select all Environment options that you create.

## Other features for privileged users

Are you a privileged user and would to have additional options/features? Send us an email and let us know.
