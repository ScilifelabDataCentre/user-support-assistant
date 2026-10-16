https://serve.scilifelab.se/docs/model-serving/options/

SciLifeLab Serve offers functionality to host trained machine learning models to make them available for inferences/predictions (this is also called *model serving*). The models are then available at all times from our servers and can be used by other researchers, by general public, by tools (e.g. pipelines and analysis scripts) for inferences. You can host a model with a graphical user interface (essentially, offering a website where users can interact with your model) and with a REST API endpoint (the model can then be called programmatically, for example, using Python code from a JupyterLab notebook). Models trained using any Python frameworks can be hosted on SciLifeLab Serve.

This page provides a step-by-step guide on how you can prepare and host your models.

## Introduction

There are multiple ways to approach hosting (also referred to as *serving*) of a trained machine learning model. Here are we will focus on quickly creating a graphical user interface and a [REST API endpoint](https://blog.postman.com/rest-api-examples/) for your model, then packaging it as a [Docker image](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/), and, finally, hosting it on SciLifeLab Serve. 

The setup described here will cover the needs of a large majority of researchers when they want to share their ML model, allowing to give the model users instant predictions and good performance overall. There are however also other approaches. For example, one can serve models using dedicated serving frameworks optimized for performance such as [ONNX](https://github.com/onnx/onnx), [PyTorch Serve](https://github.com/pytorch/serve), or [NVIDIA Triton](https://developer.nvidia.com/triton-inference-server). We do not currently support any of these dedicated serving frameworks out-of-the-box because these are rarely needed in the research context. Instead we focus on more generally applicable solution. If you need to use those, feel free to get in touch with us to discuss how we can help you.

While the process described on this page may seem complicated at first, any researcher who is regularly training machine learning models using Python should be able to follow the steps described. This is because you can make use of modern open source frameworks with excellent documentation which make this process easy. If you run into any issues or have questions, our team will be happy to help, send us an email to [serve@scilifelab.se](mailto:serve@scilifelab.se).

## Step-by-step guide

### Step 1. Make sure the model is able to make inference on your computer

Before you can start preparing and packaging your model, create a Python function that takes input for your model, uses your trained model to make a prediction, and gives output from your model. This means that your trained model (regardless of the format it is in) should be callable and should send back a response. Exactly what kind of processing happens inside that function does not matter for the next steps, what matters is that this function takes some input(s) and provides some output(s). 

Prepare a folder with all necessary files and functions to make inferences using your model. Try making predictions that require less and more intense computations, and make sure the performance is satisfactory, otherwise consider what would be needed. If your model predictions are too slow because you need more hardware resources than you have on your computer you ask for those resources on SciLifeLab Serve. On the other hand, if your predictions are slow because you need to optimize the prediction process you should do that before hosting your model; consider reading [how to optimize you python code here](https://enccs.github.io/python-perf/).

### Step 2. Select a framework that will act as a foundation

Now you need to embed your function and necessary files into an application that can hosted on the web, either with a graphical user interface or an API. In the former case the user would see a webpage where they can type, select or upload their input to the model and where they can then see the output from the model. In the latter case the user would send a REST API request with their model input and receive the model output back. Modern open source [Python frameworks](https://en.wikipedia.org/wiki/Category:Python_(programming_language)_web_frameworks) will help to achieve this with a few lines of Python code.

There are two open source frameworks that are popular, easy-to-use, and were made with researchers in machine learning in mind; they cover the needs of most researchers. These are [Gradio](https://github.com/gradio-app/gradio) and [Streamlit](https://github.com/streamlit/streamlit). They are similar in their intended use cases and target audience. Both of these frameworks have good documentation and numerous tutorials online for all kinds of input and output types and customization (for example, with additional HTML and CSS if you are up to it but it's not necessary).

Take a look at [Gradio documentation](https://www.gradio.app/guides/quickstart) and [Streamlit documentation](https://docs.streamlit.io/get-started/tutorials/create-an-app).

From the SciLifeLab Serve point of view there is no difference which of these frameworks you use. Below are some aspects of each of these frameworks that we are aware of which may help you choose.

- _Streamlit_ allows for customization of what elements appear on each page and their order by declaring Python variables in a particular order whereas customization of the look in a _Gradio_ application is not as straightforward. _Streamlit_ also allows to easily build multi-page applications. 
- _Gradio_ automatically builds both a graphical user interface and a REST API interface for all apps whereas _Streamlit_ only builds a graphical user interface. 
- _Gradio_ has an out-of-the-box solution for handling queues - if multiple users interact with your model at the same time, their requests will be put into a queue and handled in order.
- Default visual look of _Gradio_ and _Streamlit_ apps are quite different so you may have a preference for one over the other if you do not plan to do further customization.
- There is a difference in the types of input and output that have already been implemented in each of the frameworks. For example, _Streamlit_ has [an integration of Ketcher](https://blog.streamlit.io/introducing-a-chemical-molecule-component-for-your-streamlit-apps/) that allows users to draw chemical compounds. You can see all input and output types here: [standard Gradio components](https://www.gradio.app/docs/gradio/introduction), [Gradio components created by community](https://www.gradio.app/custom-components/gallery), [standard Streamlit components](https://docs.streamlit.io/develop/api-reference), [Streamlit components created by the community](https://streamlit.io/components).

If you already have experience with web development you may want to use another framework, that will not be an issue from the perspective of using SciLifeLab Serve. For example, you may want to use [Flask](https://github.com/pallets/flask) or [FastAPI](https://github.com/fastapi/fastapi).

[image:6 size:large]
    Screenshot of a Gradio app; source: https://flower-classification.serve.scilifelab.se.

[image:7 size:large]
    Screenshot of a Streamlit app; source: https://antimicrobial-kg.serve.scilifelab.se.

### Step 3. Create an application from your model

When you made a decision about which framework to use go ahead and create an application. One good approach would be to start small from an example in the documentation and build from there.

For building apps with Gradio we prepared a [detailed tutorial ourselves](https://github.com/ScilifelabDataCentre/serve-tutorials/tree/main/Workshops/Building-sharing-ML-demo-apps) which you can follow. There are many other tutorials you can find online for both frameworks.

### Step 4. Package and publish your application on SciLifeLab Serve

Once your application works on your laptop you can package it for publishing on SciLifeLab Serve and start hosting it. We have separate tutorials for this - [user guide on packaging and publishing a Gradio app](https://serve.scilifelab.se/docs/application-hosting/gradio/), [user guide on packaging and publishing a Streamlit app](https://serve.scilifelab.se/docs/application-hosting/streamlit/). In both cases we also have example applications that you can use as a starting point or for reference.

## Frequently Asked Questions

**I am stuck while following this guide. Can I get help?**

Yes, feel free to get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) and we can try to help. Please provide a link to your code so far (for example, to your GitHub repository) in your email so that we can best help you.

**Can I serve my model using ONNX/PyTorch/Triton/TensorFlow Serving/similar?**

We do not currently support that but we would be interested to hear about your particular use case and see if we can help you in another way, get in touch with us.

**How many users can use my model simultaneously?**

We do not restrict the number of requests that can be sent to your application/model; what happens after the request arrives is handled at the level of your application. If you use Gradio to create your app, there will be a queue of requests and they will be handled in the order that they arrived. If you use Streamlit and expect multiple users we recommend finding a solution for creating a similar queue manually.

**Can I make inference calls to my model from JupyterLab or other notebooks?**

Yes, you can do that if your app has a possibility to accept REST API calls. This comes out-of-the-box for apps that were built using Gradio. Simply use the API endpoints that you have with the URL of your model/application.

**How much CPU and RAM/memory does Serve allocate to my model?**

Please find the default allocation in the user guide pages [for Gradio
](https://serve.scilifelab.se/docs/application-hosting/gradio/) and [for Streamlit](https://serve.scilifelab.se/docs/application-hosting/other/). If you would like for your model/app to be allocated more than the default amount of resources, get in touch with us (<a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>) with a motivation.

**Can I have a GPU allocated for my model to make predictions?**

We are currently working on implementing this. We are interested to learn about more use cases so get in touch with us and tell us about your model.

**Can I keep my model private while my article/conference submission is under review?**

Yes, it is possible to publish an app/model in such a way that only those with a URL can open it. To do that, choose "Link" option in the Permissions field of the app settings. In this case those who you share the link with (for example, reviewers of your article) will be able to open it but this link will not be available anywhere publicly.

**Can I host a private model for my research group?**

No, each app/model on SciLifeLab Serve needs to be made public eventually. The apps/models can only stay private while you are still developing it or while it is under peer review.

**Can I see how many users are using my model?**

At the moment we do not track such statistics. We plan to implement this at some point in the future.

**Can I host my R model on SciLifeLab Serve?**

Get in touch with us and we can probably help you.
