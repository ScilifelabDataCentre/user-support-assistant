https://serve.scilifelab.se/docs/application-hosting/other/

SciLifeLab Serve allows hosting of web applications built with any framework that creates a server listening on ports 3000–9999.

## Introduction

SciLifeLab Serve allows hosting of custom apps free of charge to researchers in life sciences working at a Swedish research institution as well as their collaborators abroad.  
The data and code behind each app hosted on SciLifeLab Serve need to be made publicly available.  
All apps hosted on SciLifeLab Serve are publicly available through a URL in the form of *x.serve.scilifelab.se*.  
Currently, only apps that have been packaged as a Docker container image are supported (see below for instructions on how to do that).

Each app hosted on SciLifeLab Serve receives 2 vCPU and 4 GB of memory/RAM. These can be requested to be increased up to 12 vCPU, 1 GPU, and 48 GB of memory/RAM if need is demonstrated (this means that you provide an example of a likely user interaction, for example user input, where having higher resources allocated will make a significant difference to performance).

Each project on SciLifeLab Serve also has a persistent volume (folder) for data storage that can be shared between apps and notebooks in that project (you can find more [information about file management here](https://serve.scilifelab.se/docs/files/)).

## Step-by-step guide

This step-by-step guide will walk you through creating and publishing a Docker container image, registering on SciLifeLab Serve, creating a project, and, finally, creating an app inside your project. We do not go into detail explaining each of the tools and settings we used during the process in order to streamline the instructions. We welcome contributions and suggestions for improvement of this guide.

As of now, SciLifeLab Serve only allows hosting applications if they are containerized.  
Packaging your application into a container is relatively straightforward, so do not be concerned if you have never done this before.  
The first steps of this guide will explain in detail how to do just that.  
If you run into an issue you cannot resolve, the SciLifeLab Serve team is happy to help you with this through a free individual consultation, get in touch with us by e-mailing <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>.

## Step 1. Install Docker on your computer

See the [official install page here](https://docs.docker.com/engine/install/).

## Step 2. Create a `Dockerfile` for your app

In this tutorial, there is no single correct way of creating a `Dockerfile` because it depends on what you want to host. However, there are 2 requirements for this to work:

- The container must run as a non-root user with user id 1000. If you need to have a different user id in your image get in touch with the SciLifeLab Serve team.
- The container must use a start up script placed at the working directory (`WORKDIR` in the Dockerfile).

See the full example below if something is unclear.

Here is one way of creating a user in a `Dockerfile` (Ubuntu-based):

```dockerfile
# Set username as a variable
ENV USER=username

# Add the user with user id 1000
RUN useradd -u 1000 $USER

# Change ownership of your code to your new user
RUN chown -R $USER:$USER /path/to/code

# Make sure the container is running as non-root
USER $USER
```

Create a start up script and add this to the working directory.

```dockerfile
# Copy the file to the correct location
COPY start-script.sh /path/to/start-script.sh

# Make sure that the script can be executed
RUN chmod +x /path/to/start-script.sh
```

## Step 3. Build and test a Docker image

Ensure that Docker Desktop is running. Open Terminal (or Windows Terminal) and navigate to the folder where your app files and the Dockerfile are located.

```bash
cd path/to/your/folder
```

Run the Docker command to build your image as shown below. Note that the dot at the end of the command is important. Please note that building the image may take a while.

```bash
docker build --platform linux/amd64 -t <some-name>:<some-tag> .
```

Replace `<some-name>:<some-tag>` with the name of the app and some tag to identify this particular version. For instance `my-web-app:v2`.  
Once the process is complete, run the following command in the Terminal. You should see your image in the list.

```bash
docker image ls
```

In order to test that the image you just built works you need to run a container from this image. To do that, run the following command in the Terminal.

```bash
docker run --rm <some-name>:<some-tag> ./start-script.sh
```

If everything went well, you should now be able to navigate to `http://localhost:<host_port>` in your browser and see and interact with your app.

## Step 4. Publish your app Docker image

You have now built and tested an image for your app on your computer. In order to be able to host this image on SciLifeLab Serve it needs to be published in a so-called image registry. One such image registry that is popular is [DockerHub](https://hub.docker.com/), another one is GitHub Container Registry. Below we show how to publish the image using DockerHub (using the graphical user interface of Docker Desktop or Terminal) and an alternative way to publish an image on GitHub Container Registry (automated using GitHub Actions).

#### Option 1. Manually publishing an image on DockerHub

Register on [DockerHub](https://hub.docker.com/) and sign in with your account on the Docker Desktop app.

Next, re-build your image as described above, this time including your DockerHub username in the image name, as shown below. It is important that each new version of your app has a unique image tag. You can use `v1`, `version124`, a date, or any other versioning that you like.

```bash
docker build --platform linux/amd64 -t <your-dockerhub-username>/<some-name>:<some-tag> .
```

Once the image is built and visible on Docker Desktop, pick *“Push to Hub”* among the options for your app image.

Alternatively, you can also use the following command from the terminal instead:

```bash
docker push <your-dockerhub-username>/<some-name>:<some-tag>
```

Keep in mind that you might need to log in to your DockerHub user in case you haven't done so already. This can be done as follows:

```bash
docker login --username=<your-dockerhub-username>
```

This should publish your image on *https://hub.docker.com/r/&lt;your-dockerhub-username&gt;/&lt;some-name&gt;:&lt;some-tag&gt;*. Please note that your image should stay publicly available even after your app is published on Serve because it will be fetched at regular intervals.

#### Option 2. Automatically publishing an image on GitHub

The Docker image can be built and published automatically using GitHub Actions every time you push a change to your repository containing the app code. We recommend setting up this workflow as it will minimize the need for you to do things manually every time you make a change in your app.

[This repository](https://github.com/ScilifelabDataCentre/gradio-flower-classification) contains an example of how to set up a GitHub Action for publishing on GitHub Packages (file `.github/workflows/docker-image-ghcr.yml`). Copy this file into your own repository into the same folder and customize if you would like.

This workflow to build and publish an image will be triggered on push to the *main* branch. To learn more about how GitHub Actions work and how you can further customize this action [please see the official documentation](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images). The resulting Docker image can be found under **Packages** in your account or at the bottom of the right sidebar on your repository homepage. Keep in mind that the Docker image needs to be publicly available for SciLifeLab Serve to see it, the images on GitHub are not always public by default.

## Step 5. Create a user account on SciLifeLab Serve

If you do not already have a user account on SciLifeLab Serve, [create an account](https://serve.scilifelab.se/signup/).

## Step 6. Create a project

Every app and model has to be located within a project. Projects that you have created/been granted access to can be found under the **[My projects](https://serve.scilifelab.se/projects/)** page.

You need to be logged in to create a project. To create a project, click on the corresponding button on that page. Choose the Default project template. The name and description of the project are visible only to you and those who you grant access to the project. Once the project is created, you will be taken to the project dashboard where you can create different types of apps.

Before creating an app that needs storage, you can go to the project **Settings → Storage** page to:

- Review how much storage is available for the project  
- Configure one or more **mount paths** (paths inside your container where the project storage will be mounted)  
- Request more storage and optionally enable automatic extension of the volume up to 5 GB

These mount paths are later selectable in the app form.

## Step 7. Create an app

In order to host your app click the **Create** button on the *Custom app* card. Then enter the information below in the form. Some of the fields are required while others are optional.

* **Subdomain:** This is the subdomain that the deployed app will be available at (e.g., a subdomain of `my-cool-app` would mean that the app will be available at `my-cool-app.serve.scilifelab.se`). If no subdomain name is entered, a random name will be generated by default. By typing in the input box you can specify the custom subdomain name of your choice.
* **Mount path:** If your app is saving some data or accessing data from a folder that you would like to keep on the project’s persistent volume, select one of the **mount paths** defined in the project’s **Settings → Storage**. Selecting a mount path will attach the project storage at the corresponding path inside your container. If you do not need storage, choose **None**. If you need storage but do not see any options here, first configure mount paths in the project storage settings.
* **Hardware:** Amount of CPU and RAM dedicated to your app. By default there is only one option that is sufficient for most users; get in touch with us if your app needs more hardware resources.
* **Port:** The port that the app runs on. Note that we only allow ports in the range 3000–9999.
* **Image:** URL to the image on GitHub or another image repository (for DockerHub: `your-dockerhub-username/your-image-name:your-image-tag`). Note that **each version of your app should have a unique tag**. When an image with a certain tag has been deployed once it will no longer be possible to change the app without a new tag.

* **Title:** Title of the app that will be displayed on the Public apps page.
* **Description:** Provide a description of the app, will also be displayed on the Public apps page. This functions as an abstract describing your application.
* **Subjects and keywords:** Provide a few keywords describing your application, you can select from a large set of keywords.
* **Permission:** The permissions for the project. There are four levels of permissions for an app:  
  1. **Private:** The app can only be accessed by the user that created the app (sign in required). Please note that we only allow the permissions to be set to Private temporarily, while you are developing the app. Eventually each app should be published publicly.  
  2. **Project:** All members of the project where the app is located will be able to access the app (sign in required). Please note that we only allow the permissions to be set to Project temporarily, while you are developing the app. Eventually each app should be published publicly.  
  3. **Link:** Anyone with the URL can access the app but this URL will not be publicly listed anywhere by us (this option is best in case you want to share the app with certain people but not with everyone yet).  
  4. **Public:** Anyone with the URL can access the app and the app will be displayed under the Public apps page.
* **Creators:** List of authors for your application. You can fill out information manually or make use of, for example, ORCID IDs to fetch information automatically. You can also decide the order in which the creators will appear.
* **Language of the application interface:** Select the language of the text inside your application.
* **Funding sources:** Here you can select a funder, indicate the grant number, etc.
* **Source code URL:** Provide a URL where the source code of your app can be accessed. This can, for example, be a link to a GitHub repository, an entry on Zenodo or Figshare, or another repository. If your source code is stored with a DOI, provide a link starting with `https://doi.org/`.

> **Note:** Previously, app settings had separate fields for “Persistent volume” and “Path”. These have now been merged into a single **Storage** field that points to mount paths defined in your project’s storage settings.

After you click "Submit", you will be taken to the page where you can see how your app is added step-by-step. Once it is done, you will be taken to the deployment overview page. Please note that even after the status is 'Running' it may take up to a couple of minutes for the app to actually start. If you chose "Link" or "Public" permissions, the app can now be accessed by anyone opening the app URL. "Public" apps are also displayed under the "Apps" page on SciLifeLab Serve.

To update your app, you need to first publish an updated container image with a new tag. Once your updated container image has been published, go the app settings page (click on the "Settings" link), change the tag in the **Image** field, and press the **Update** button at the bottom of the form. To delete the app, press the "Delete" link next to the "Settings" link.

## Full example

Here is a complete example of a [Streamlit](https://streamlit.io/) app.  
We have four files:

```bash
..
└── app/
│   ├── app.py
│   ├── Dockerfile
│   ├── start-script.sh
│   └── requirements.txt
```

### 1. `app.py`

This is a simple example app that plots points in polar coordinates and allows the user to twist the plot and add more points.

```python
from collections import namedtuple
import altair as alt
import math
import pandas as pd
import streamlit as st

with st.echo(code_location="below"):
    total_points = st.slider("Number of points in spiral", 1, 5000, 2000)
    num_turns = st.slider("Number of turns in spiral", 1, 100, 9)

    Point = namedtuple("Point", "x y")
    data = []

    points_per_turn = total_points / num_turns

    for curr_point_num in range(total_points):
        curr_turn, i = divmod(curr_point_num, points_per_turn)
        angle = (curr_turn + 1) * 2 * math.pi * i / points_per_turn
        radius = curr_point_num / total_points
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        data.append(Point(x, y))

    st.altair_chart(
        alt.Chart(pd.DataFrame(data), height=500, width=500)
        .mark_circle(color="#0068c9", opacity=0.5)
        .encode(x="x:Q", y="y:Q")
    )
```

### 2. `Dockerfile`

This is an example of how to create instructions for how to build and run a container.

```dockerfile
# Select base image (can be ubuntu, python, shiny etc)
FROM python:3.9-slim

# Create user name and home directory variables. 
# The variables are later used as $USER and $HOME. 
ENV USER=username
ENV HOME=/home/$USER

# Add user to system
RUN useradd -m -u 1000 $USER

# Set working directory (this is where the code should go)
WORKDIR $HOME/app

# Update system and install dependencies.
RUN apt-get update && apt-get install --no-install-recommends -y     build-essential     software-properties-common

# Copy code and start script (this will place the files in home/username/)
COPY requirements.txt $HOME/app/requirements.txt
COPY app.py $HOME/app/app.py
COPY start-script.sh $HOME/app/start-script.sh

RUN pip install --no-cache-dir -r requirements.txt     && chmod +x start-script.sh     && chown -R $USER:$USER $HOME     && rm -rf /var/lib/apt/lists/*

USER $USER
EXPOSE 8501

ENTRYPOINT ["./start-script.sh"]
```

### 3. `start-script.sh`

In this particular example, the start script is simple. This can be expanded to an arbitrary complexity if needed.

```bash
#!/bin/bash

streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

### 4. `requirements.txt`

This app requires three packages that are installed with `pip`:

```bash
altair
pandas
streamlit
```

To test if this works, you must first build and then run the container. This is done by running the following (in the terminal). Make sure that you navigate to the location of your `Dockerfile`, like `/app`.

```bash
docker build --platform linux/amd64 -t <some-name>:<some-tag> .
docker run --rm -it -p 8501:8501 <some-name>:<some-tag>
```

Replace `<some-name>:<some-tag>` with the name of the app and some tag to identify this particular version. For instance `my-web-app:v2`.

When adding this app to SciLifeLab Serve, you would fill in the app form as described above (including selecting a **Storage** mount path if your app needs access to project storage).

## Frequently Asked Questions

**I am stuck while following the guide. Can I get help?**  

Yes, feel free to get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>). Please provide a link to your app code and data (for example, to your GitHub repository) in your email so that we can best help you.

**Can I have a database attached to my app?**  

We do not provide separate managed databases, but your app can save and access files on the project’s persistent volume. You configure where this storage is mounted inside the container via **mount paths** in the project’s **Settings → Storage**, and then select one of those mount paths in the app’s **Storage** field. Here you are also allowed to store a file with a SQLite database if that is sufficient for your purposes. Please note that you may not put any user data or other sensitive data into this storage.

**Can I have a user database in my app?**  

No, we do not allow user registration and user databases. We accept only apps that allow users to work with them while they are open. Next time the user comes, the app should be back at its default state.

**Can my app be hosted at a top-level domain, such as www.example.org?**  

Yes, it is possible. Your app will then be available at both *x.serve.scilifelab.se* and your own *example.org*. To do this, you will need to purchase a domain name yourself and set up DNS settings that you will get from us. Get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) so that we can arrange this for you.

**Can my app contain sensitive data?**  

No, SciLifeLab Serve does not support hosting of apps with sensitive data.

**How much CPU and RAM/memory does Serve allocate to my app?**  

Please find the default allocation in the text of this page above. If you would like for your app to be allocated more than the default amount of resources, get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) with a motivation.

**Do you have a GPU that my app can use?**

Yes, we have some NVIDIA A40 GPUs that we can allocate, get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) with a motivated request.

**What resource allocations will my app need on Serve?**  

You can always deploy your app with default resource allocations and observe its performance, most apps do not need more than the default allocations. If your app is not performing well and you are unsure how to test what it needs, let us know and we can help you.

**Where can I see logs of my application?**  

Click on the three dots to the right of your application and click on the "Logs" page. Only the logs from the past 24 hours will be displayed here. Note that these logs are meant to be used only for debugging purposes, you are not allowed to track the users' actions using these logs. The Serve team periodically checks all applications and their logs.

**Why is my app slower on Serve than on my laptop?**  

If your app is slower on Serve than on your own laptop, it probably needs to be assigned more resources to function well. Get in touch with us at <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a> and describe your situation.

**I updated the Docker image in the app settings, why do I still see the old version?**  

We require that each version of your app has a unique Docker image tag. When an app has been deployed once using an image with a certain tag it will no longer be possible to fetch an updated image with an identical tag. Therefore, you need to publish your image with a new unique tag and change the image address in the app settings to include this new tag. In other words, instead of using `image:latest` for all of your versions you should be using unique tags for each version, e.g. `image:v3` or `image:20240125`. Still seeing the same version despite publishing your Docker image with a new tag? Send us an email to <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>, and we can take a look at what went wrong in that case.

**Can I keep my app private while my article/conference submission is under review?**  

Yes, it is possible to publish an app in such a way that only those with a URL can open it. To do that, choose the "Link" option in the Permissions field of the app settings. In this case those who you share the link with (for example, reviewers of your article) will be able to open it but not anyone else.

**Can I get a DOI (Digital Object Identifier) for my app?**

Yes, all applications published with permission level Public receive a DOI. You can [read more about DOIs here](https://serve.scilifelab.se/docs/doi/).

**Can I host a private app for my research group?**  

No, each app on SciLifeLab Serve needs to be made public eventually. The apps can only stay private while you are still developing them or while they are under peer review.

**How do I update or delete my app after it has been published?**  

Please find the answer in the text of this page.

**Can I delete/hide my Docker image after my app is published?**  

No, the Docker images need to stay available at all times. SciLifeLab Serve is regularly fetching the image again. If it is not available, your app will stop working.

**Can I see how many users are accessing my application?**  

At the moment we do not track such statistics. We plan to implement this at some point in the future.

**Can I embed my app on another website using an inline frame (iframe)?**  

Yes, you can do that. We do not restrict embedding of the apps hosted on SciLifeLab Serve into other websites.

**Is there a size limit for a file I want to upload when using the app?**  

Yes, for other types of apps, the upload size limit is 100 MB. If your project requires uploading files with larger size, contact us at <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>.
