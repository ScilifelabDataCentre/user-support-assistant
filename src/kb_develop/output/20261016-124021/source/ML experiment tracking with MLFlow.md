https://serve.scilifelab.se/docs/mlflow/

  SciLifeLab Serve strives to be a platform that offers a suite of tools for researcher building and using machine learning models. While we do not offer hardware resources for training machine learning models (see [NAISS resources](https://www.naiss.se/) for access to clusters for ML training in Sweden), you can use our service to track your machine learning experiments. This is made possible through integration of the most popular solution for experiment tracking - the open source suite [MLFlow](https://github.com/mlflow/mlflow).

You can track your machine learning work through SciLifeLab Serve regardless of where exactly you are running training and analyses, it can be on your own computer, your research group machine, or the national clusters offered by NAISS. When you create an MLFlow instance through the Serve interface you will receive credentials with which you can connect to our servers and send metrics and artifacts. These metrics and artifacts alongside the other features become available in the graphical user interface of your MLFlow instance on SciLifeLab Serve.


### MLFlow Tracking Setup on Serve
   
**Note:** We use MLFlow version 2.20.3.
   
To set up your MLFlow instance on Serve, follow these steps:
   
1\. Navigate to `My Projects` and either open an existing project or create a new one.
   
2\. Under the `Develop` section, click `Create` on the MLFlow app card.

[image:12 size:large]

**Note:** Users can only have one MLFlow instance per project.
   
3\. Fill in the form by assigning a name to your MLFlow instance.

[image:16 size:large]

4\. Wait for the instance status to transition from `Created` to `Running`.

[image:14 size:large]

5\. Once the instance status is `Running`, click on the name of your MLFlow instance, indicated by a key (🔑) icon.
   
You'll receive instructions on integrating MLFlow into your machine learning workflow and accessing the MLFlow web interface.

[image:15 size:large]

If you are already experienced with MLFlow, you're now ready to begin tracking your experiments. For beginners, we recommend reviewing the official MLFlow documentation: [MLFlow Official Documentation](https://mlflow.org/docs/latest/index.html).
   
### Alternatives
   
For those seeking alternative tracking solutions, Neptune is another popular platform that offers comprehensive experiment tracking and model management.
