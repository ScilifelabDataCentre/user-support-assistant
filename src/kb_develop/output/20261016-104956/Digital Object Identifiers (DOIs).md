https://serve.scilifelab.se/docs/doi/

## What is a Digital Object Identifier (DOI)

[Digital Object Identifiers (DOIs)](https://support.datacite.org/docs/doi-basics) are a main [persistent identifier](https://en.wikipedia.org/wiki/Persistent_identifier) used in scholarly communication. Many are familiar with using DOIs for articles, preprints, or datasets.

DOI provides a permanent link to the research output which does not change over time, meaning that readers can always reliably find it. Using DOIs in citations is important to attribute work correctly. They also allow to interlink related work with each other (for example, a dataset and an application that can be used to explore this dataset). Finally, having a DOI makes research output more discoverable because its metadata is available in the global DOI registry.

A DOI is a unique number made up of a prefix and a suffix separated by a forward slash. This is an example of one: 10.1000/182. It is resolvable using the doi.org proxy server by displaying it as a link: https://doi.org/10.1000/182. 

When a DOI is registered, information about the resource is stored in the global DOI metadata databases. At SciLifeLab Serve, we make use of [DataCite](https://datacite.org/) infrastructure for that.

## DOIs at SciLifeLab Serve

All apps published on SciLifeLab Serve with permission level *Public* will be automatically assigned a DOI. This DOI will then be displayed on the page with the application details. We recommend that you use this DOI rather than the application URL when describing your application in a research paper, preprint, presentation etc. or citing your application.

When you change the Docker image of your model or app, a new DOI will be created as the newer version of the existing DOI. For all other changes, the DOI will stay the same.

In case you have multiple version of the same application, you can use a version specific DOI to refer to that particular version or you can use the general DOI if you want the user to always see the information about the latest application version. Both of these are available on the app details page. See, for example, [this app details page](https://serve.scilifelab.se/records/187/).

## Frequently Asked Questions

#### Which of the DOIs should I use in my paper?

In case you have multiple version of the same application, you can use a version specific DOI to refer to that particular version or you can use the general DOI if you want the user to always see the information about the latest application version. Both of these are available on the app details page. See, for example, [this app details page](https://serve.scilifelab.se/records/187/).

#### Can I get a DOI for my private/project/link app?

We do not currently support automatic DOI assignment for apps that do not have the permission level *Public*, we are working on implementing it. However, if you need a DOI before your application is made public, get in touch with us, and we can create one for you manually.

#### Can I delete a DOI that was created for my app?

It is not possible to delete a DOI that has been created.
