https://serve.scilifelab.se/docs/application-hosting/gradio/

SciLifeLab Serve allows hosting of web applications built with the [Gradio](https://www.gradio.app/). [Gradio](https://github.com/gradio-app/gradio) is a Python-based framework that simplifies the process of building apps with graphical user interfaces for machine learning models. Whatever data type or model architecture you work with, most probably you can easily create a Gradio-based application that will allow users to make inferences using your model.  Gradio is open source and has a large community around it, meaning that there is good documentation and that good examples are available.

## Introduction

SciLifeLab Serve allows hosting of Gradio apps free of charge to researchers in life sciences working at a Swedish research institution as well as their collaborators abroad. The code and model behind each app hosted on SciLifeLab Serve need to be made publicly available. All apps hosted on SciLifeLab Serve are publicly available through a URL in the form of *x.serve.scilifelab.se*. Currently, all apps need to be packaged as a Docker container image prior to hosting (see the instructions below for how to do that).

Each Gradio app hosted on SciLifeLab Serve receives 2 vCPU and 4 GB of memory/RAM by default. These can be requested to be increased up to 12 vCPU, 1 GPU, and 48 GB of memory/RAM if need is demonstrated (this means that you provide an example of a likely user interaction, for example user input, where having more hardware resources allocated will make a significant difference to performance).

## Step-by-step guide

This step-by-step guide will walk you through creating and publishing a Docker container image with your Gradio app, registering on SciLifeLab Serve, creating a project, and, finally, creating an app inside your project resulting in a public URL. We have not gone into detail explaining each of the tools and settings we used during the process in order to streamline the instructions. We welcome contributions and suggestions for improvement of this guide.

As of now, SciLifeLab Serve only allows to host Gradio applications if they are packaged as Docker images ([Docker](https://en.wikipedia.org/wiki/Docker_(software)) is a powerful and widespread tool for deployment of applications). Packaging your Gradio application as a Docker image is relatively straightforward, so do not be concerned if you have never done this before. The first steps of this guide will explain in detail how to do just that. If you run into an issue you cannot resolve, the SciLifeLab Serve team is happy to help you with this through a free individual consultation, get in touch with us by e-mailing <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>.

### Step 0. Prepare your Gradio app

Here we will assume that you already have a Gradio app that is working on your computer and that is ready to be hosted. To learn about how to create a Gradio app, [please see this separate tutorial that we prepared](https://github.com/ScilifelabDataCentre/serve-tutorials/tree/main/Workshops/Building-sharing-ML-demo-apps). The target audience of that tutorial are researchers working with machine learning models that do not have web development background but still want to share demos of their models as web applications. In that tutorial we show how to start with Gradio and build increasingly complex applications. Gradio makes this process easy and quick, without needing to learn anything more than researchers working with machine learning models in Python already know.

### Step 1. Download and install Docker Desktop

You will need to have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed on your computer to be able to build an image. 

### Step 2. Prepare files for building a Docker image

To host your app on SciLifeLab Serve, you first need to package it as a Docker image. This is a simple process even if you have not done this before so do not worry. You can also simply start with [our example Gradio app](https://github.com/ScilifelabDataCentre/gradio-flower-classification) and modify it to fit your own app scripts, data files, etc.

We assume that your app files have the following structure:

```bash
...
└── gradio_app/
│   ├── requirements.txt
│   ├── main.py
│   └── assets/
│       └── ... (model and any other static files required)
```
Before you can build a Docker image, you will need to create one additional file - Dockerfile.

Dockerfile is a file containing instructions for how your Docker image should be built. See [the official documentation](https://serve.scilifelab.se/docs/application-hosting/gradio/(https:/docs.docker.com/engine/reference/builder/)) if you are curious to learn more but for the purpose of hosting your app it is sufficient to simply copy and adjust the template below. Note that this file should be called simply `Dockerfile`, without any file extension.

```dockerfile
# Select base image
FROM python:3.11-slim

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

# Copy requirements.txt and install packages listed there with pip (this will place the files in home/username/)
COPY requirements.txt $HOME/app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install torch, torchvision, torchaudio packages with pip separately from the packages installed through the requirements.txt
RUN python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy all files that are needed for your app to run with the directory structure as your files expect
COPY main.py $HOME/app/main.py
COPY assets/example_images/ $HOME/app/assets/example_images/
COPY assets/flower_dataset_labels.txt $HOME/app/assets/flower_dataset_labels.txt
# Because the model file is too large we download it separately and put in the correct location
ADD https://nextcloud.dc.scilifelab.se/s/GSf2g5CAFxBPtMN/download $HOME/app/assets/flower_model_vgg19.pth

# If your app allows users to upload files set a directory where Gradio can place temporary files
ENV GRADIO_TEMP_DIR="/home/username/app/temp/"

# Give access to appripriate files and folders to the created user
RUN chown -R $USER:$USER $HOME \
    && rm -rf /var/lib/apt/lists/*

USER $USER

EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python", "main.py"]

```

This Dockerfile instructs to start with a base image containing Python version 3.11 (it is going to contain Ubuntu as operating system and components required to run Python), install the required packages listed in *requirements.txt*, copy all the scripts and other necessary files for the app into the image (adjust this to copy all files your app needs to rum), and, finally adds the command to start the app that will be run every time (specifically, it will run `python main.py` that starts the Gradio app). The Dockerfile also contains information about which user should be running the app and which port it should expose (*7860* is the standard port for Gradio).

At this point, you should have the following file structure in your app directory:

```bash
...
└── gradio_app/
│   ├── requirements.txt
│   ├── main.py
│   ├── assets/
│       └── ... (model and any other static files required)
│   └── Dockerfile
```

You can see our example app with these files [in this GitHub repository](https://github.com/ScilifelabDataCentre/gradio-flower-classification).

### Step 3. Build a Docker image

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
docker run --rm -it -p 7860:7860 <some-name>:<some-tag>
```

If everything went well, you should now be able to navigate to `http://localhost:7860` in your browser and see and interact with your app.

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

Keep in mind the you might need to login to you dockerhub user incase you haven't done so already. This can be done as follows:

```bash
docker login --username=<your-dockerhub-username>
```

This should publish your image on *https://hub.docker.com/r/&lt;your-dockerhub-username&gt;/&lt;some-name&gt;:&lt;some-tag&gt;*. Please note that your image should stay available even after your app is published on Serve because it will be fetched with regular intervals.

#### Option 2. Automatically publishing an image on GitHub

The Docker image can be built and published automatically using GitHub Actions every time you push a change to your repository containing the app code. We recommend setting up this workflow as it will minimize the need for you to do things manually every time you make a change in your app.

The [repository of our example Gradio app](https://github.com/ScilifelabDataCentre/gradio-flower-classification) contains an example of how to set up GitHub action for publishing on GitHub packages (file '.github/workflows/docker-image-ghcr.yml'). Copy this file into your own repository into the same folder and customize if you would like.

This workflow to build and publish an image will be triggered on push to the *main* branch. To learn more about how GitHub actions work here and how you can further customize this action [please see the official documentation](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images
). The resulting Docker image can be found under Packages in your account or on the bottom of the right sidebar on your repository homepage. For example, our example app image is available under *ghcr.io/scilifelabdatacentre/gradio-flower-classification:20231220-114734*. Keep in mind that the Docker image needs to be publicly available for SciLifeLab Serve to see it, the images on GitHub are not always public by default.

### Step 5. Create a user account on SciLifeLab Serve

If you do not already have a user account on SciLifeLab Serve, [create an account](https://serve.scilifelab.se/signup/).

### Step 6. Create a project

Every app and model has to be located within a project. Projects that you have created/been granted access to can be found under **[My projects](https://serve.scilifelab.se/projects/)** page.

You need to be logged in to create a project. To create a project, click on the corresponding button on that page. Choose Default project template. The name and description of the project are visible only to you and those who you grant access to the project. Once the project is created, you will be taken to the project dashboard where you can create different types of apps.

### Step 7. Create an app

In order to host a Gradio app click the Create button on the *Gradio app* card. Then enter the information below in the form. Some of the fields are required while others are optional.

* **Subdomain:** This is the subdomain that the deployed app will be available at (e.g., a subdomain of 'my-cool-app' would mean that the app will be available at my-cool-app.serve.scilifelab.se). If no subdomain name is entered, a random name will be generated by default. By typing in the input box you can specify the custom subdomain name of your choice.
* **Mount path:** If your app is saving some data or accessing data from a folder that you would like to keep on the project’s persistent volume, select one of the **mount paths** defined in the project’s **Settings → Storage**. Selecting a mount path will attach the project storage at the corresponding path inside your container. If you do not need storage, choose **None**. If you need storage but do not see any options here, first configure mount paths in the project storage settings.
* **Hardware:** Amount of CPU and RAM dedicated to your app. By default there is only one option that is sufficient for most users; get in touch with us if your app needs more hardware resources.
* **Port:** The port that the Gradio app runs on (in our case it was 7860).
* **Image:** URL to the image on GitHub or another image repository (for DockerHub: your-dockerhub-username/your-image-name:your-image-tag). Note that each version of your app should have a unique tag. When an image with a certain tag has been deployed once it will no longer be possible to change the app without a new tag.

* **Title:** Title of the app that will be displayed on the Public apps page.
* **Description:** Provide a description of the app, will also be displayed on the Public apps page. This functions as an abstract describing your application.
* **Subjects and keywords:** Provide a few keywords describing your application, you can select from a large set of keywords.
* **Permissions:** The permissions for the project. There are four levels of permissions for an app:
1. **Private:** The app can only be accessed by the user that created the app (sign in required). Please note that we only allow the permissions to be set to Private temporarily, while you are developing the app. Eventually each app should be published publicly.
2. **Project:** All members of the project where the app is located will be able to access the app (sign in required). Please note that we only allow the permissions to be set to Project temporarily, while you are developing the app. Eventually each app should be published publicly.
3. **Link:** Anyone with the URL can access the app but this URL will not be publicly listed anywhere by us (this option is best in case you want to share the app with certain people but not with everyone yet).
4. **Public:** Anyone with the URL can access the app and the app will be displayed under Public apps page.
__Note: There is a known bug with the Gradio app deployment using permissions _Project_ and _Private_. We are working on fixing this bug but in the meantime use only _Public_ and _Link_ options.__ 
* **Creators:** List of authors for your application. You can fill out information manually or make use of, for example, ORCID IDs to fetch information automatically. You can also decide the order in which the creators will appear.
* **Language of the application interface:** Select the language of the text inside your application.
* **Funding sources:** Here you can select funders, indicate the grant numbers, etc.
* **Source code URL:** Provide a URL where source code of your app can be accessed. This can, for example, be a link to GitHub repository, an entry on Zenodo or Figshare or another repository. If your source code is stored with a DOI, provide a link starting with https://doi.org/.

The rest of the settings can be left as default if you do not intend to make use of more complex scenarios.

For our example app, the settings look as shown in the image below.

[image:23 size:large]
    Screenshot of app settings for our example app

After you click "Submit", you will be taken to the page where you can see how your app is added step-by-step. Once it is done, you will be taken to the deployment overview page. Please note that even after the status is 'Running' it may take up to a couple of minutes for the app to actually start. If you chose "Link" or "Public" permissions, the app can now be accessed by anyone opening the app URL. "Public" apps are also displayed under the "Apps" page on SciLifeLab Serve.

To update your Gradio app, you need to first publish an updated container image with a new tag. Once your updated container image has been published, go the app settings page (click on the "Settings" link), change the tag in the Image field, and press on the Update button on the bottom of the form. To delete the app, press the "Delete" link next to the "Settings" link.

## Frequently Asked Questions

**I am stuck while following the guide. Can I get help?**

Yes, feel free to get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>). Please provide a link to your Gradio app code and associated files (for example, to your GitHub repository) in your email so that we can best help you. 

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

**I updated the Docker image in the app settings, why do I still see the old version?**

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

**Why is my app giving an error or not letting me upload files anymore?**

There could be a few reasons:

Your app might be running out of memory. Check the error logs for details. Try optimizing your code to use less memory. If the issue persists, contact us—we may be able to increase the limit.

If temporary files exceed 5 GB, uploads may fail. Learn more about Gradio resource cleanup here: [Gradio Resource Cleanup](https://www.gradio.app/guides/resource-cleanup).

**Is there a size limit for a file I want to upload when using the app?**

Yes, for Gradio apps, the upload size limit is 100MB. If your project requires uploading files with larger size, contact us at <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>
