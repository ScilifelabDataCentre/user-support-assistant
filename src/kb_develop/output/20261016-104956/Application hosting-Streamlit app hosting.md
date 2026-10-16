https://serve.scilifelab.se/docs/application-hosting/streamlit/

SciLifeLab Serve allows hosting of web applications built with the [Streamlit](https://streamlit.io/). [Streamlit](https://github.com/streamlit/streamlit) is a Python-based framework that simplifies the process of building apps with graphical user interfaces for data science applications and machine learning models. Whatever data type or model architecture you work with, most probably you can easily create a Streamlit-based application that will allow users to make inferences using your model.  Streamlit is open source and has a large community around it, meaning that there is good documentation and that good examples are available.

## Introduction

SciLifeLab Serve allows hosting of Streamlit apps free of charge to researchers in life sciences working at a Swedish research institution as well as their collaborators abroad. The code and model behind each app hosted on SciLifeLab Serve need to be made publicly available. All apps hosted on SciLifeLab Serve are publicly available through a URL in the form of *x.serve.scilifelab.se*. Currently, all apps need to be packaged as a Docker container image prior to hosting (see the instructions below for how to do that).

Each Streamlit app hosted on SciLifeLab Serve receives 2 vCPU and 4 GB of memory/RAM by default. These can be requested to be increased up to 12 vCPU, 1 GPU, and 48 GB of memory/RAM if need is demonstrated (this means that you provide an example of a likely user interaction, for example user input, where having more hardware resources allocated will make a significant difference to performance).

## Step-by-step guide

This step-by-step guide will walk you through creating and publishing a Docker container image with your Streamlit app, registering on SciLifeLab Serve, creating a project, and, finally, creating an app inside your project resulting in a public URL. We have not gone into detail explaining each of the tools and settings we used during the process in order to streamline the instructions. We welcome contributions and suggestions for improvement of this guide.

As of now, SciLifeLab Serve only allows to host Streamlit applications if they are packaged as Docker images ([Docker](https://en.wikipedia.org/wiki/Docker_(software)) is a powerful and widespread tool for deployment of applications). Packaging your Streamlit application as a Docker image is relatively straightforward, so do not be concerned if you have never done this before. The first steps of this guide will explain in detail how to do just that. If you run into an issue you cannot resolve, the SciLifeLab Serve team is happy to help you with this through a free individual consultation, get in touch with us by e-mailing <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>.

### Step 0. Prepare your Streamlit app

Here we will assume that you already have a Streamlit app that is working on your computer and that is ready to be hosted. To learn about how to create a Streamlit app, [please see Streamlit documentation](https://docs.streamlit.io/). Streamlit apps should be easy to create for researchers already working with machine learning models in Python because apps are written purely in Python and in just *.py* files.

### Step 1. Download and install Docker Desktop

You will need to have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed on your computer to be able to build an image. 

### Step 2. Prepare files for building a Docker image

To host your app on SciLifeLab Serve, you first need to package it as a Docker image. This is a simple process even if you have not done this before so do not worry. You can also simply start with [our example Streamlit app](https://github.com/ScilifelabDataCentre/streamlit-image-to-smiles) and modify it to fit your own app scripts, data files, etc.

We assume that your app files have the following structure:

```bash
...
└── app/
│   ├── app.py
│   ├── requirements.py
│   ├── pages/ (if you have a multi-page app)
│   └──... (any other files your app needs)
```

Before you can build a Docker image, you will need to create one additional file - *Dockerfile*. 

Dockerfile is a file containing instructions for how your Docker image should be built. See [the official documentation](https://serve.scilifelab.se/docs/application-hosting/streamlit/(https:/docs.docker.com/engine/reference/builder/)) if you are curious to learn more but for the purpose of hosting your app it is sufficient to simply copy and adjust the template below. Note that this file should be called simply `Dockerfile`, without any file extension. It should be placed in the same level folder as your folder */app/* containing all files for your app.

```dockerfile
# select starting image
FROM python:3.10.0-slim

# Create user name and home directory variables. 
# The variables are later used as $USER and $HOME. 
ENV USER=username
ENV HOME=/home/$USER

# Add user to system
RUN useradd -m -u 1000 $USER

# Set working directory (this is where the code should go)
WORKDIR $HOME/app

# Update system and install dependencies.
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    software-properties-common

# Copy all files that the app needs (this will place the files in home/username/)
COPY app/app.py $HOME/app/app.py
COPY app/requirements.txt $HOME/app/requirements.txt
COPY app/pages $HOME/app/pages/
# more COPY commands here if you have other files to copy

# Install packages listed in requirements.txt with pip
RUN pip install --no-cache-dir -r requirements.txt

USER $USER
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]

```

This Dockerfile instructs to start with a base image containing Python version 3.10 (it is going to contain Ubuntu as operating system and components required to run Python), copy all files required for the app into the image (adjust this to copy all files your app needs to run), install the required packages listed in *requirements.txt*, and, finally, points to the script to start the app (ENTRYPOINT command). The Dockerfile also contains information about which user should be running the app and which port it should expose.

Please note that for hosting your Streamlit app on SciLifeLab Serve it is important that your main application file is called *app.py*, and that it is located in the working directory inside your Docker image.

At this point, you should have the following file structure in your app directory:

```bash
...
├── Dockerfile
└── app/
│   ├── app.py
│   ├── requirements.py
│   ├── pages/ (if you have a multi-page app)
│   └──... (any other files your app needs)
```

You can see our example app with these files [in this GitHub repository](https://github.com/ScilifelabDataCentre/streamlit-image-to-smiles/).

### Step 3. Build a Docker image

Ensure that Docker Desktop is running. Open Terminal (or Windows Terminal) and navigate to the folder where your app folder and the Dockerfile are located.

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
docker run --rm -it -p 8501:8501 <some-name>:<some-tag>
```

If everything went well, you should now be able to navigate to `http://localhost:8501` in your browser and see and interact with your app.

### Step 4. Publish your Docker image

You have now built and tested an image for your app on your computer. In order to be able to host this image on SciLifeLab Serve it needs to be published in a so-called image registry. One such image registry that is popular is [DockerHub](https://hub.docker.com/), another one is GitHub container repository. Below we show how to publish the image using to DockerHub (using the graphical user interface of Docker Desktop or Terminal) and an alternative way to publish an image on GitHub container repository (automated using GitHub actions).

#### Option 1. Manually publishing an image on DockerHub

Register on [DockerHub](https://hub.docker.com/) and sign in with your account on Docker Desktop app.

Next, re-build your image as described above, this time including your DockerHub username in the image name, as shown below. It is important that each new version of your app has a unique image tag. You can use v1, version124, date, or any other versioning that you like.

```bash
docker build --platform linux/amd64 -t <your-dockerhub-username>/<some-name>:<some-tag> .
```

Once the image is built and visible on Docker Desktop, pick *"Push to Hub"* among the options for your app image. 

Alternatively, you can also use the following command from the terminal instead:

```bash
docker push <your-dockerhub-username>/<some-name>:<some-tag>
```

Keep in mind the you might need to login to you dockerhub user in case you haven't done so already. This can be done as follows:

```bash
docker login --username=<your-dockerhub-username>
```

This should publish your image on *https://hub.docker.com/r/&lt;your-dockerhub-username&gt;/&lt;some-name&gt;:&lt;some-tag&gt;*. Please note that your image should stay available even after your app is published on Serve because it will be fetched with regular intervals.

#### Option 2. Automatically publishing an image on GitHub

The Docker image can be built and published automatically using GitHub Actions every time you push a change to your repository containing the app code. We recommend setting up this workflow as it will minimize the need for you to do things manually every time you make a change in your app.

The [repository of our example Streamlit app](https://github.com/ScilifelabDataCentre/streamlit-image-to-smiles/) contains an example of how to set up GitHub action for publishing on GitHub packages (file '.github/workflows/docker-image-ghcr.yml'). Copy this file into your own repository into the same folder and customize if you would like.

This workflow to build and publish an image will be triggered on push to the *main* branch. To learn more about how GitHub actions work here and how you can further customize this action [please see the official documentation](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images
). The resulting Docker image can be found under Packages in your account or on the bottom of the right sidebar on your repository homepage. For example, our example app image is available under *ghcr.io/scilifelabdatacentre/streamlit-image-to-smiles:20241112-183549*. Keep in mind that the Docker image needs to be publicly available for SciLifeLab Serve to see it, the images on GitHub are not always public by default (can be changed under _Package settings_).

### Step 5. Create a user account on SciLifeLab Serve

If you do not already have a user account on SciLifeLab Serve, [create an account](https://serve.scilifelab.se/signup/).

### Step 6. Create a project

Every app and model has to be located within a project. Projects that you have created/been granted access to can be found under **[My projects](https://serve.scilifelab.se/projects/)** page.

You need to be logged in to create a project. To create a project, click on the corresponding button on that page. Choose Default project template. The name and description of the project are visible only to you and those who you grant access to the project. Once the project is created, you will be taken to the project dashboard where you can create different types of apps.

### Step 7. Create an app

In order to host a Strealit app click the Create button on the *Streamlit App* card. Then enter the information below in the form. Some of the fields are required while others are optional.

* **Subdomain:** This is the subdomain that the deployed app will be available at (e.g., a subdomain of 'my-cool-app' would mean that the app will be available at my-cool-app.serve.scilifelab.se). If no subdomain name is entered, a random name will be generated by default. By typing in the input box you can specify the custom subdomain name of your choice.
* **Mount path:** If your app is saving some data or accessing data from a folder that you would like to keep on the project’s persistent volume, select one of the **mount paths** defined in the project’s **Settings → Storage**. Selecting a mount path will attach the project storage at the corresponding path inside your container. If you do not need storage, choose **None**. If you need storage but do not see any options here, first configure mount paths in the project storage settings.
* **Hardware:** Amount of CPU and RAM dedicated to your app. By default there is only one option that is sufficient for most users; get in touch with us if your app needs more hardware resources.
* **Port:** The port that the Streamlit app runs on (in our case it is 8501).
* **Image:** URL to the image on GitHub or another image repository (for DockerHub: your-dockerhub-username/your-image-name:your-image-tag). Note that each version of your app should have a unique tag. When an image with a certain tag has been deployed once it will no longer be possible to change the app without a new tag.

* **Title:** Name of the app that will be displayed on the Public apps page.
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

The rest of the settings can be left as default if you do not intend to make use of more complex scenarios.

For our example app, the settings look as shown in the image below.

[image:22 size:large]
    Screenshot of app settings for our example app

Note that our example app required **more than the default 2 vCPU and 4 GB RAM** because the model behind this app is computationally expensive. You can request more than default hardware allocation for your app as well.

After you click "Submit", you will be taken to the page where you can see how your app is added step-by-step. Once it is done, you will be taken to the deployment overview page. Please note that even after the status is 'Running' it may take up to a couple of minutes for the app to actually start. If you chose "Link" or "Public" permissions, the app can now be accessed by anyone opening the app URL. "Public" apps are also displayed under the "Apps" page on SciLifeLab Serve.

To update your Streamlit app, you need to first publish an updated Docker image with a new tag. Once your updated container image has been published, go the app settings page (click on the "Settings" link), change the tag in the Image field, and press on the Update button on the bottom of the form. To delete the app, press the "Delete" link next to the "Settings" link.

## Frequently Asked Questions

**I am stuck while following the guide. Can I get help?**

Yes, feel free to get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>). Please provide a link to your Streamlit app code and associated files (for example, to your GitHub repository) in your email so that we can best help you. 

**Can my app be hosted at a top-level domain, such as www.example.org?**

Yes, it is possible. Your app will then be available at both *x.serve.scilifelab.se* and your own *example.org*. To do this, you will need to purchase a domain name yourself and set up DNS settings that you will get from us. Get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) so that we can arrange this for you.

**Can my app contain sensitive data?**

No, SciLifeLab Serve does not support hosting of apps with sensitive data. 

**How much CPU and RAM/memory does Serve allocate to my app?**

Please find the default allocation in the text of this page above. If you would like for your app to be allocated more than the default amount of resources, get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) with a motivated request.

**Do you have a GPU that my app can use?**

Yes, we have some NVIDIA A40 GPUs that we can allocate, get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) with a motivated request.

**What resource allocations will my app need on Serve?**

You can always deploy your app with default resource allocations and observe its performance, most apps do not need more than the default allocations. If your app is not performing well, and you are unsure how to test what it needs, let us know and we can help you.

**Why is my app slower on Serve than on my laptop?**

This could be the case for various reasons. For example, your app may require more resources than we allocated by default. Get in touch with the us on <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a> and describe your situation.

**I clicked Update in the app settings but it didn't update, why do I still see the old version?**

Most probably the issue is with your Docker image. We require that each version of your app has a unique image tag. When an app has been deployed once using an image with a certain tag it will no longer be possible to fetch an updated image with an identical tag. Therefore, you need to publish your image with a new unique tag and change the image address in the app settings to include this new tag. In other words, instead of using "image:latest" for all of your versions you should be using unique tags for each version, e.g. "image:v3" or "image:20240125". Still seeing the same version despite publishing your Docker image with a new tag? Send us an email to <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>, and we can take a look what went wrong in that case.

**Can I keep my app private while my article/conference submission is under review?**

Yes, it is possible to publish an app in such a way that only those with a URL can open it. To do that, choose "Link" option in the Permissions field of the app settings. In this case those who you share the link with (for example, reviewers of your article) will be able to open it but not anyone else.

**Can I get a DOI (Digital Object Identifier) for my app?**

Yes, all applications published with permission level Public receive a DOI. You can [read more about DOIs here](https://serve.scilifelab.se/docs/doi/).

**Can I host a private app for my research group?**

No, each app on SciLifeLab Serve needs to be made public eventually. The app can only stay private while you are still developing it or while it is under peer review.

**How do I update or delete my app after it has been published?**

Please find the answer in the text of this page.

**Can I delete/hide my Docker image after my app is published?**

No, the Docker images need to stay available at all times. SciLifeLab Serve is regularly fetching the image again. If it is not available, your app will stop working.

**Can I see how many users are accessing my application?**

At the moment we do not track such statistics. We plan to implement this at some point in the future.

**Can I embed my app on another website using an inline frame (iframe)?**

Yes, you can do that. We do not restrict embedding of the apps hosted on SciLifeLab Serve into other websites.

**Is there a size limit for a file I want to upload when using the app?**

Yes, for Streamlit apps, the upload size limit is 100MB. If your project requires uploading files with larger size, contact us at <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>
