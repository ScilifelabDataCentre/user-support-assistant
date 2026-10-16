https://serve.scilifelab.se/docs/teaching/

## Introduction

The tools available on SciLifeLab Serve can be used for workshops, seminars, courses, and other training events where students need to perform hands-on tasks in computational environments. Specifically, using SciLifeLab Serve participants in training events can get access to individual instances of [browser-based notebooks](https://serve.scilifelab.se/docs/notebooks/): JupyterLab, RStudio, or VS Code. In addition, they can launch a custom Docker Image prepared by the instructors beforehand. This negates the need for instructors to spend time ensuring that the software and dependencies needed to complete tasks are correctly installed on each machine. This will both save time and help to ensure the course/workshop can run smoothly.

As with all other resources available through SciLifeLab Serve, the computational notebooks are provided free of charge. Our service can be used for training events at the level of PhD candidates or higher and in events where at least one instructor is affiliated with a Swedish research institute or research infrastructure.

Whilst still in the *beta testing phase*, SciLifeLab Serve has already been used for teaching classes (of around 30-40 students) with great success. However, we prefer if you always have an alternative in case something goes wrong since we cannot guarantee that issues will not arise.

## Who is eligible to apply?

We accept applications for courses, workshops, and webinars that are organised by staff affiliated with Swedish universities or SciLifeLab infrastructure units. The courses/workshops/webinars should be aimed life science researchers at the doctoral level or above.

## What can students use on SciLifeLab Serve?

There are two approaches to using our service in teaching:

### Default JupyterLab, RStudio, or VSCode notebooks

The students can get access to our default JupyterLab, RStudio, or VSCode notebooks. We provide recent versions of the standard distributions with few or no non-standard packages pre-installed on them. Necessary Python and R packages can be installed as usual in these instances (e.g. `pip install x` or `install.packages("x")`). Notebook files or data can be uploaded by students through the Serve interface or downloaded from an external URL through JupyterLab and RStudio interfaces. As an instructor you will need to prepare step-by-step instructions for your students on how they can set up these instances for work during your course or workshop.

### Custom notebooks and other tools

If you have many custom packages that your workshop or course requires or if you would like to include data and other files in the notebooks that your students launch you can create your own installations. Similarly, if you want students to use another tool we can add that to our our service for your students. For this you will need to build a Docker image. We will then add this Docker image (or multiple Docker images) into the options that your students see in the SciLifeLab Serve interface. In this case we recommend starting with one of our existing Dockerfiles and building on top of that (see [JupyterLab](https://github.com/ScilifelabDataCentre/serve-images/tree/main/serve-jupyterlab), [RStudio](https://github.com/ScilifelabDataCentre/serve-images/tree/main/serve-rstudio), [VSCode](https://github.com/ScilifelabDataCentre/serve-images/tree/main/serve-vscode)). This is particularly useful if your course consists of multiple labs where each has its own dependencies that would take look for for students to install each time.

## What kind of compute and storage capacity will we receive? Is there a limit to participant number?

We will discuss your individual requirements for CPUs and memory with you. By default each computational environment created at SciLifeLab Serve gets assigned 2 vCPU and 4 GB RAM. More can be assigned if our infrastructure can accommodate that. For reference, SciLifeLab Serve has previously been used to teach courses involving up to 30-40 participants without issue, and we may have capacity to accommodate larger courses.

Each notebook can have a [storage folder of 1 GB](https://serve.scilifelab.se/docs/files/) attached to it. Here too, more storage can be assigned if our infrastructure can accommodate that.


## How do I request to use SciLifeLab Serve for teaching?

To ensure that our hardware can manage the load that you expect during your training event, we have established a specific [application form](https://serve.scilifelab.se/teaching/#application) for access to this functionality. The [form](https://serve.scilifelab.se/teaching/#application) enables you to provide details about yourself and your planned course/workshop/webinar. Please provide information about what kind of computational environment you require, what hardware resources are needed, how many students, and for how long they will need access.

## What will the process look like from the participants' perspective?

Participants of your training event will need to register on SciLifeLab Serve and subsequently create a new notebook. Accounts of participants that do not have an email belonging to a Swedish university [will need to approved manually](https://serve.scilifelab.se/docs/user-accounts/) so these participants should register on our service before your training event starts. You will need to provide instructions for fetching the files, data, and packages required for your course (for example, using `git clone` and `pip install`). Alternatively, if you provided your own Docker images your students will not need to fetch files etc.

## What support will be provided?

Before the course, you should try the functionality that we have, prepare materials and test how it works. We will be available to answer any questions that you might have regarding features of SciLifeLab Serve, setting up the required instances for students, and the interface of SciLifeLab Serve. During the course, we will monitor our servers throughout. In the event of a server issue, we will do all we can to resolve it quickly. However, we recommend having a backup plan in case there are unforeseen issues that cannot be resolved promptly.

## How is SciLifeLab Serve funded?

SciLifeLab Serve is supported by a grant from the Knut and Alice Wallenberg Foundation given to SciLifeLab for the purpose of supporting research in data-driven life science in Sweden. SciLifeLab Serve is available free of charge to researchers affiliated with Swedish research institutions as well as research infrastructure. Refer to our ['about' page](https://serve.scilifelab.se/about/) for more information.
