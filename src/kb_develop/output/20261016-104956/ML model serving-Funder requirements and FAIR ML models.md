https://serve.scilifelab.se/docs/model-serving/fair/

## Introduction

Machine learning (ML) models produced by researchers are considered to be **research output** just like more traditional research outputs such as journal articles, conference papers, book chapters, etc. This means that, when creating and sharing machine learning models, researchers need to fulfil funder and institutional requirements for research outputs.

For example, researchers need to ensure that all their work falls under the ethical approval in projects where such approval is applicable (see guidelines from e.g., [Swedish Research Council](https://www.vr.se/english/applying-for-funding/requirements-terms-and-conditions/conducting-ethical-research.html), [ERC](https://erc.europa.eu/manage-your-project/ethics-guidance)). In addition, their research output needs to meet open access publication requirements (e.g., [Swedish Research Council](https://www.vr.se/english/applying-for-funding/requirements-terms-and-conditions/publishing-open-access.html), [ERC](https://erc.europa.eu/manage-your-project/open-science )), open data requirements (e.g., [Swedish Research Council](https://www.vr.se/english/mandates/open-science/open-access-to-research-data/vision-and-guiding-principles.html ), [ERC](https://erc.europa.eu/manage-your-project/open-science )), open analysis workflows and code requirements (e.g., [National guidelines for promoting open science in Sweden](https://www.kb.se/samverkan-och-utveckling/nytt-fran-kb/nyheter-samverkan-och-utveckling/2024-01-15-national-guidelines-for-promoting-open-science-in-sweden.html )). 

To meet these requirements, European and Swedish funders and universities currently recommend adhering to FAIR principles (e.g., [Swedish Research Council: Making research data accessible and FAIR criteria](https://www.vr.se/english/mandates/open-science/open-access-to-research-data/support-and-tools-/making-research-data-accessible-and-fair.html)).

## FAIR ML models

FAIR (Findable, Accessible, Interoperable, Reusable) is a set of principles originally written for research data (see [Wilkinson et al 2016](https://doi.org/10.1038/sdata.2016.18)) but since expanded to other research output (see [Baker et al 2022](https://doi.org/10.1038/s41597-022-01710-x), [Patel et al 2023](https://doi.org/10.1038/s41597-023-02463-x)). There is no one specific way to 'make something FAIR'; instead, research output can adhere to FAIR principles to different extent and in different ways.

The long-term goal of SciLifeLab Serve is to allow Swedish researchers to meet funder requirements in terms of FAIR principles when publishing machine learning models without any extra work; in other words, everything should be done for you automatically when you publish your model on SciLifeLab Serve. While we still have a lot to do to achieve this for ML models (specifically in terms of, e.g. sharing various artifacts associated with training the model, sharing code, describing the models according to open standards, as described below), SciLifeLab Serve already now helps to fulfil the funder requirements to some extent. On this page, we describe what is already possible and give recommendations on further steps researchers can take to adhere to FAIR principles to a reasonable extent.

### Meeting FAIR requirements in web applications with ML models

Currently, researchers can share their machine learning models through SciLifeLab Serve by turning them into independent web applications. We have [guidelines for how to do it here](https://serve.scilifelab.se/docs/model-serving/options/). All models shared on SciLifeLab Serve as Public web applications will fulfil the requirements on meeting FAIR principles to a large extent. You can read more about it on the separate page describing in what way these published applications (including machine learning applications) [already meet FAIR requirements, but also what more researchers need to do](https://serve.scilifelab.se/docs/application-hosting/fair/).

SciLifeLab Serve helps to fulfil the requirements by, for example, [issuing a DOI](https://serve.scilifelab.se/docs/doi/) (a [persistent identifier](https://support.orcid.org/hc/en-us/articles/360006971013-What-are-persistent-identifiers-PIDs)) for all public apps, by collecting metadata and using controlled vocabularies where appropriate, making the collected metadata harvestable, etc. You can read about [how exactly we fulfil FAIR requirements on this dedicated page](https://serve.scilifelab.se/about/fair_principles/).

When you refer to your app with the model in your scientific publications and presentations, use the DOI that is issued for it rather than the URL (because whereas URLs can change, DOI should always work and because DOI can be used to retrieve metadata about your app). SciLifeLab Serve will issue a general DOI that will always lead to the latest version of your app as well as version-specific DOIs; use the one that you think is appropriate for the context.

In order to improve the discoverability of your application and the quality of the metadata associated with it, you should make sure to provide a good title, description, appropriate keywords. It is also helpful to indicate related publications, datasets, published code, funders, etc. in the form on SciLifeLab Serve. To make sure you get appropriate credit, make sure to add your ORCID ID to your own profile on SciLifeLab Serve but also indicate ORCID IDs of your collaborators.

### Additional suggestions specific to ML models

When it comes to specifically machine learning models, researchers should in addition put extra effort into the descriptions of their models so that they useful information for use and reuse of the model. Good descriptions (metadata) are one of the pillars of FAIR. Pick recommendations below that are relevant for you, create a description file with the text following the recommendations, and share this file in the same place where you share the model artifact files (for example, in a GitHub repository).

There is no single standard for describing ML models because it is still a relatively new field and because coming up with such a community standard is complicated due to differences in ML modeling approaches. However, there are already recommendations that gained traction. For example, you can follow the [Model cards format suggested by researchers at Google](https://modelcards.withgoogle.com/about) to describe your model. Another influential recommendation is [Model cards format by HuggingFace](https://huggingface.co/docs/hub/model-cards). A model card is simply a file with structured text that describes the specific aspects of the model.

*[DOME (Data, Optimization, Model and Evaluation)](https://dome-ml.org/)* is a set of community recommendations for reporting supervised machine learning–based analyses applied to biological studies ([Walsh et al 2021](https://doi.org/10.1038/s41592-021-01205-4)). DOME recommendations are written specifically with the goal to improve machine learning assessment and reproducibility. These recommendations were developed primarily for the case of supervised learning in biological applications in the absence of direct experimental validation, as this is the most common type of ML approach used in biology. Since their publication, DOME recommendations have been increasingly adopted by the community, including some journals requiring descriptions according to DOME. There is also a [DOME registry](https://registry.dome-ml.org/intro) website where researchers can add their models.

## Open ML models

As mentioned in the Introduction, funders and institutions require open sharing of research output. Research projects using machine learning models make use of and create many artifacts, and all of these components need to be taken into account when considering the funder and institutional requirements. We at SciLifeLab Serve endorse the so-called *Model Openness Framework* (MOF, [White et al 2024](    
https://doi.org/10.48550/arXiv.2403.13784)) developed by researchers at [Linux Foundation](https://www.linuxfoundation.org/) and elsewhere.

The Model Openness Framework identifies 17 components that can be shared by researchers developing machine learning models as well as appropriate licenses that these need to be shared with. There is also [Model Openness Tool](https://isitopen.ai/) where researchers can add their own models or get an overview of how other models are classified in MDF.

While the Model Openness Framework is designed for deep learning artifacts and does not transfer directly to every form of learning in AI, we think this is a great starting point for any ML researchers wishing to share their models. We recommend the researchers strive to share as many components as possible from the list. The long-term goal of SciLifeLab Serve is to make sharing all these components as easy as possible.

### Model Openness Framework Components and Licenses

Source: *Table 2* of [White et al 2024](    
https://doi.org/10.48550/arXiv.2403.13784)

| Component | Domain | Content Type | Accepted Open License |
| --- | --- | --- | --- |
| Datasets | Data | Data | Preferred: [CDLA-Permissive-2.0](https://cdla.dev/permissive-2-0/), [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.en). Acceptable: Any including unlicensed |
| Data Preprocessing Code | Data | Code | Acceptable: [OSI-approved](https://opensource.org/licenses), e.g., [The MIT License](https://opensource.org/licenseslicense/mit) |
| Model Architecture | Model | Code | Acceptable: [OSI-approved](https://opensource.org/licenses), e.g., [The MIT License](https://opensource.org/licenseslicense/mit) |
| Model Parameters | Model | Data | Preferred: [CDLA-Permissive-2.0](https://cdla.dev/permissive-2-0/). Acceptable: [OSI-approved](https://opensource.org/licenses), e.g., [The MIT License](https://opensource.org/licenseslicense/mit), Permissive Open Data Licenses |
| Model Metadata | Model | Data | Preferred: [CDLA-Permissive-2.0](https://cdla.dev/permissive-2-0/). Acceptable: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.en), Permissive Open Data Licenses |
| Training Code | Model | Code | Acceptable: [OSI-approved](https://opensource.org/licenses), e.g., [The MIT License](https://opensource.org/licenseslicense/mit) |
| Inference Code | Model | Code | Acceptable: [OSI-approved](https://opensource.org/licenses), e.g., [The MIT License](https://opensource.org/licenseslicense/mit) |
| Evaluation Code | Model | Code | Acceptable: [OSI-approved](https://opensource.org/licenses), e.g., [The MIT License](https://opensource.org/licenseslicense/mit) |
| Evaluation Data | Model | Data | Preferred: [CDLA-Permissive-2.0](https://cdla.dev/permissive-2-0/). Acceptable: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.en), Permissive Open Data Licenses |
| Evaluation Results | Model | Documentation | Preferred: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.en). Acceptable: Permissive Open Content Licenses |
| Supporting Libraries & Tools | Model | Code | Acceptable: [OSI-approved](https://opensource.org/licenses), e.g., [The MIT License](https://opensource.org/licenseslicense/mit) |
| Model Card | Model | Documentation | Preferred: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.en). Acceptable: Permissive Open Content Licenses |
| Data Card | Data | Documentation | Preferred: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.en). Acceptable: Permissive Open Content Licenses |
| Technical Report | Model & Data | Documentation | Preferred: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.en). Acceptable: Permissive Open Content Licenses |
| Research Paper | Model & Data | Documentation | Preferred: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/deed.en). Acceptable: Permissive Open Content Licenses |
| Sample Model Outputs | Model | Data or Code | Unlicensed |

## Other sources of information

There are many other good sources of information about FAIR ML models and open ML models that you can use if you are interested to dive into this. Here are some recommendations:

[Ten simple rules for good model-sharing practices](https://doi.org/10.1371/journal.pcbi.1012702)

[FAIR, AI Readiness, and Reproducibility Network: Resources](https://www.farr-rcn.org/resources)
