https://serve.scilifelab.se/docs/application-hosting/dash/

SciLifeLab Serve allows hosting of web applications built with the [Plotly Dash framework](https://dash.plotly.com/). Dash is primarily used to create data apps with Python cod. Dash apps can contain interactive visualisations, tables, text, analysis tools, ML models, and more.

## Introduction

SciLifeLab Serve allows hosting of Dash apps free of charge to researchers in life sciences working at a Swedish research institution as well as their collaborators abroad. The data and code behind each app hosted on SciLifeLab Serve need to be made publicly available. All apps hosted on SciLifeLab Serve are publicly available through a URL in the form of *x.serve.scilifelab.se*. Currently, only apps that have been packaged as a Docker container image are supported (see the instructions below for how to do that).

Each Dash app hosted on SciLifeLab Serve receives 2 vCPU and 4 GB of memory/RAM by default. These can be requested to be increased up to 12 vCPU, 1 GPU, and 48 GB of memory/RAM if need is demonstrated (this means that you provide an example of a likely user interaction, for example user input, where having higher resources allocated will make a significant difference to performance). If your app requires saving or accessing data files in an attached volume, see [our guide for other app types](https://serve.scilifelab.se/docs/application-hosting/other/) where we describe how to attach a persistent volume.

## Step-by-step guide

This step-by-step guide will walk you through creating and publishing a Docker container image with your Dash app, registering on SciLifeLab Serve, creating a project, and, finally, creating an app inside your project. We have not gone into detail explaining each of the tools and settings we used during the process in order to streamline the instructions. We welcome contributions and suggestions for improvement of this guide.

As of now, SciLifeLab Serve only allows to host Dash applications if they are packaged as Docker images ([Docker](https://en.wikipedia.org/wiki/Docker_(software)) is a powerful and widespread tool for deployment of applications). Packaging your Dash application as a Docker image is relatively straightforward, so do not be concerned if you have never done this before. The first steps of this guide will explain in detail how to do just that. If you run into an issue you cannot resolve, the SciLifeLab Serve team is happy to help you with this through a free individual consultation, get in touch with us by e-mailing <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>.

### Step 1. Download and install Docker Desktop

You will need to have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed on your computer to be able to build an image. 

### Step 2. Create a Dockerfile for your app

In this example, we will assume that the Dash app code is located in a file called *app.py*, the required packages are listed in the file *requirements.txt*, that there is an assets folder with some additional files (in our case styles.css and a data file). Make sure that your app runs as it should with this structure when you run it on your computer. Here is the file structure that we assume:

```bash
..
└── dash_app/
│   ├── app.py
│   ├── requirements.txt
│   └── assets/
│       ├── styles.css
│       └── data.csv
```

Docker images are built from sets of instructions given in a so-called [Dockerfile](https://docs.docker.com/engine/reference/builder/). Create a file called *Dockerfile* (the name of the file should be exactly 'Dockerfile' and it should not have any file extension) using any text editor you have and insert the code below or simply [download this example](https://github.com/ScilifelabDataCentre/dash-covid-in-sweden/blob/main/Dockerfile). Place this file in the same folder. This is what your file structure should look like:

```dockerfile
FROM python:3.9

COPY ./requirements.txt /requirements.txt

RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install -r /requirements.txt
RUN pip3 install gunicorn openpyxl

COPY ./app.py /code/
RUN mkdir /code/assets
COPY ./assets/ /code/assets

WORKDIR /code/
ENV PYTHONPATH /code

ENV GUNICORN_CMD_ARGS "--bind=0.0.0.0:8000 --workers=2 --thread=4 --worker-class=gthread --forwarded-allow-ips='*' --access-logfile -"

CMD ["gunicorn", "app:server"]

```
Here is what your file structure should look like after you create the new files.

```bash
..
└── dash_app/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── assets/
│       ├── styles.css
│       └── data.csv
```

You can change the instructions in the Dockerfile to fit your app's needs (e.g. rename files and copy or run additional files). The first line declares that the image is based on Python 3.9; change the Python version if needed. This is followed by copying the requirements.txt in the image, and the required packages are installed in the line *RUN pip3 install -r /requirements.txt*. Subsequently, the file 'app.py' is copied to */code/*, */code/assests* folder is created and the content of our assets folder is copied there.

You can see our example app with these files [in this GitHub repository](https://github.com/ScilifelabDataCentre/dash-covid-in-sweden).

### Step 3. Build a Docker image

Ensure that Docker Desktop is running. Open Terminal (or Windows Terminal) and navigate to the folder where your app files and the Dockerfile are located. 

```bash
cd path/to/your/folder
```

Run the Docker command to build your image as shown below. Replace *your-image-name* with your own image name. Note that the dot at the end of the command is important. Please note that building the image may take a while.

```bash
docker build --platform linux/amd64 -t your-image-name:your-image-tag .
```

Once the process is complete, your newly created image should appear on Docker Desktop under the Images. Alternatively, run the following command in the Terminal to inspect images on your computer. You should see your image in the list.

```bash
docker image ls
```

In order to test that the image you just built works you need to run a container from this image. To do that, run the following command in the Terminal.

```bash
docker run --rm -p 8000:8000 your-image-name:your-image-tag
```

If everything went as it should, you should now be able to navigate to *http://localhost:8000/* in your browser and see and interact with your Dash app.

### Step 4. Publish your Docker image

You have now built and tested the image for your Dash app on your computer. In order to be able to host this image on SciLifeLab Serve it needs to be published in a so-called image registry.  Below, we show how to publish your image manually on [DockerHub](https://hub.docker.com)  or automatically on DockerHub or GitHub every time you make an update , this is our recommended method (this method uses GitHub Actions).

#### Option 1: Manually publishing an image

Register on [DockerHub](https://hub.docker.com/) and sign in with your account in the Docker Desktop app.

Next, re-build your image as described above, this time including your DockerHub username in the image name, as shown below. It is important that each new version of your app has a unique image tag. You can use v1, version124, date, or any other versioning that you like.

```bash
docker build --platform linux/amd64 -t <your-dockerhub-username>/<your-image-name>:<your-image-tag> .
```

Once the image is built and visible on Docker Desktop, pick *"Push to Hub"* among the options for your app image. This should publish your image on *https://hub.docker.com/r/&lt;your-dockerhub-username&gt;/&lt;your-image-name&gt;:&lt;your-image-tag&gt;*. For example, our example app is available on *https://hub.docker.com/r/scilifelabdatacentre/dash-covid-in-sweden:20240117-063058* (this is one of the image tags that we have). Please note that your image should stay publicly available even after your app is published on Serve because it will be fetched with regular intervals.

#### Option 2:  Automatically publishing an image

The Docker image can be built and published automatically using GitHub Actions every time you push a change to your repository containing the app code. We recommend setting up this workflow as it will minimize the need for you to do things manually every time you make a change in your app.

The [repository of our example Dash app](https://github.com/ScilifelabDataCentre/dash-covid-in-sweden/) contains examples of how to set up GitHub actions for publishing on DockerHub (file 'docker-image-dockerhub.yml') or on GitHub packages (file 'docker-image-ghcr.yml'). See the folder *.github/workflows* for the two examples. Copy one of these into your own repository into the same folder and customize if needed.

For the GitHub packages workflow to work with your own repository you do not need to make any changes. Keep in mind that the Docker image needs to be publicly available for SciLifeLab Serve to see it, the images on GitHub are not always public by default.

For the DockerHub workflow to work with your own repository you will need to: change the repository name to your own repository; change the image name to your own image (use the following format: *&lt;your-dockerhub-username&gt;/&lt;your-image-name&gt;*); add DOCKERHUB_USERNAME and DOCKERHUB_TOKEN to the repository secrets (see repository settings), the token is obtained from the DockerHub account settings.

In both cases the workflow to build and publish an image will be triggered on push to the *main* branch. To learn more about how GitHub actions work here and how you can furher customize them [please see the official documentation](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images
). The resulting Docker image can be found under Packages in your account or on the bottom of the right sidebar on your repository homepage.

### Step 5. Create a user account on SciLifeLab Serve

If you do not already have a user account on SciLifeLab Serve, [create an account](https://serve.scilifelab.se/signup/).

### Step 6. Create a project

Every app and model has to be located within a project. Projects that you have created/been granted access to can be found under **[My projects](https://serve.scilifelab.se/projects/)** page.

You need to be logged in to create a project. To create a project, click on the corresponding button on that page. Choose Default project template. The name and description of the project are visible only to you and those who you grant access to the project. Once the project is created, you will be taken to the project dashboard where you can create different types of apps.

### Step 7. Create an app

In order to host a Dash app click the Create button on the Dash app card. Then enter the information below in the form. Some of the fields are required while others are optional.

* **Subdomain:** This is the subdomain that the deployed app will be available at (e.g., a subdomain of 'my-cool-app' would mean that the app will be available at my-cool-app.serve.scilifelab.se). If no subdomain name is entered, a random name will be generated by default. By typing in the input box you can specify the custom subdomain name of your choice.
* **Hardware:** Amount of CPU and RAM dedicated to your app. By default there is only one option that is sufficient for most users; get in touch with us if your app needs more hardware resources. 
* **Port:** The port that the Dash app runs on (in our case it was 8000). Note that we only allow ports in the range 3000-9999.
* **Image:** Your username, image name and tag on DockerHub (your-dockerhub-username/your-image-name:your-image-tag) or full URL to the image on a different repository. Note that each version of your app should have a unique tag. When an image with a certain tag has been deployed once it will no longer be possible to change the app without a new tag.

* **Title:** Title of the app that will be displayed on the Public apps page.
* **Description:** Provide a description of the app, will also be displayed on the Public apps page. This functions as an abstract describing your application.
* **Subjects and keywords:** Provide a few keywords describing your application, you can select from a large set of keywords.
* **Permissions:** The permissions for the project. There are four levels of permissions for an app:
1. **Private:** The app can only be accessed by the user that created the app (sign in required). Please note that we only allow the permissions to be set to Private temporarily, while you are developing the app. Eventually each app should be published publicly.
2. **Project:** All members of the project where the app is located will be able to access the app (sign in required). Please note that we only allow the permissions to be set to Project temporarily, while you are developing the app. Eventually each app should be published publicly.
3. **Link:** Anyone with the URL can access the app but this URL will not be publicly listed anywhere by us (this option is best in case you want to share the app with certain people but not with everyone yet).
4. **Public:** Anyone with the URL can access the app and the app will be displayed under Public apps page.
* **Creators:** List of authors for your application. You can fill out information manually or make use of, for example, ORCID IDs to fetch information automatically. You can also decide the order in which the creators will appear.
* **Language of the application interface:** Select the language of the text inside your application.
* **Funding sources:** Here you can select a funder, indicate the grant number, etc.
* **Source code URL:** Provide a URL where source code of your app can be accessed. This can, for example, be a link to GitHub repository, an entry on Zenodo or Figshare or another repository. If your source code is stored with a DOI, provide a link starting with https://doi.org/.


For our example app, the settings look as shown in the image below.

[image:21 size:large]
    Screenshot of app settings for our example app

After you click "Submit", you will be taken to the page where you can see how your app is added step-by-step. Once it is done, you will be taken to the deployment overview page. Please note that even after the status is 'Running' it may take up to a couple of minutes for the app to actually start. If you chose "Link" or "Public" permissions, the app can now be accessed by anyone opening the app URL. "Public" apps are also displayed under the "Apps & Models" page on SciLifeLab Serve.

To update your Dash app, you need to first publish an updated container image with a new tag. Once your updated container image has been published, go the app settings page (click on the "Settings" link), change the tag in the Image field, and press on the Update button on the bottom of the form. To delete the app, press the "Delete" link next to the "Settings" link.

## Frequently Asked Questions

**I am stuck while following the guide. Can I get help?**

Yes, feel free to get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>). Please provide a link to your Dash app code and associated files (for example, to your GitHub repository) in your email so that we can best help you. 

**Can my app be hosted at a top-level domain, such as www.example.org?**

Yes, it is possible. Your app will then be available at both *x.serve.scilifelab.se* and your own *example.org*. To do this, you will need to purchase a domain name yourself and set up DNS settings that you will get from us. Get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) so that we can arrange this for you.

**Can my app contain sensitive data?**

No, SciLifeLab Serve does not support hosting of apps with sensitive data. 

**How much CPU and RAM/memory does Serve allocate to my app?**

Please find the default allocation in the text of this page above. If you would like for your app to be allocated more than the default amount of resources, get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) with a motivated request.

**Do you have a GPU that my app can use?**
Yes, we have some NVIDIA A40 GPUs that we can allocate, get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) with a motivated request.

**What resource allocations will my app need on Serve?**

You can always deploy your app with default resource allocations and observe its performance, most apps do not need more than the default allocations. If your app is not performing well and you are unsure how to test what it needs, let us know and we can help you.

**Where can I see logs of my application?**

Click on the three dots to the right of your application and click on the "Logs". Only the logs from the past 24 hours will be displayed here. Note that these logs should only be used for debugging purposes, you are not allowed to track the users' actions using these logs. The Serve team periodically checks all applications and their logs.

**Why is my app slower on Serve than on my laptop?**

This could be the case for various reasons. For example, your app may require more resources than we allocated by default. Get in touch with the us on <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a> and describe your situation.

**I updated the image in the app settings, why do I still see the old version?**

We require that each version of your app has a unique Docker image tag. When an app has been deployed once using an image with a certain tag it will no longer be possible to fetch an updated image with an identical tag. Therefore, you need to publish your image with a new unique tag and change the image address in the app settings to include this new tag. In other words, instead of using "image:latest" for all of your versions you should be using unique tags for each version, e.g. "image:v3" or "image:20240125". Still seeing the same version despite publishing your Docker image with a new tag? Send us an email to <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>, and we can take a look what went wrong in that case.

**Can I keep my app private while my article/conference submission is under review?**

Yes, it is possible to publish an app in such a way that only those with a URL can open it. To do that, choose "Link" option in the Permissions field of the app settings. In this case those who you share the link with (for example, reviewers of your article) will be able to open it but not anyone else.

**Can I get a DOI (Digital Object Identifier) for my app?**

Yes, all applications published with permission level Public receive a DOI. You can [read more about DOIs here](https://serve.scilifelab.se/docs/doi/).

**Can I host a private app for my research group?**

No, each app on SciLifeLab Serve needs to be made public eventually. The apps can only stay private while you are still developing it or while it is under peer review.

**How do I update or delete my app after it has been published?**

Please find the answer in the text of this page.

**Can I delete/hide my Docker image after my app is published?**

No, the Docker images need to stay available at all times. SciLifeLab Serve is regularly fetching the image again. If it is not available, your app will stop working.

**Can I see how many users are accessing my application?**

At the moment we do not track such statistics. We plan to implement this at some point in the future.

**Can I embed my app on another website using an inline frame (iframe)?**

Yes, you can do that. We do not restrict embedding of the apps hosted on SciLifeLab Serve into other websites.

**Is there a size limit for a file I want to upload when using the app?**

Yes, for Dash apps, the upload size limit is 100MB. If your project requires uploading files with larger size, contact us at <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>
