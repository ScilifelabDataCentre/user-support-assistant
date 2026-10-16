https://serve.scilifelab.se/docs/files/

Each project created by users on SciLifeLab Serve has a persistent volume attached to it. A persistent volume is essentially a folder where user files (for example, data files) can be stored and accessed. This folder can then be connected to apps, models, or notebooks within that project, allowing them to access, modify, add, or delete the files stored there. It is important to keep in mind that SciLifeLab Serve does not allow any personal or sensitive data in these persistent volumes.

Persistent volumes are especially useful when an app you want to deploy has large data files that cannot simply be included in a Docker image. A persistent volume can be attached to most app types on SciLifeLab Serve.

When working with notebooks, you can select to attach the project's persistent volume in the notebook creation form.

## Storage size and storage settings

By default, each project on SciLifeLab Serve receives 1 GB of persistent storage. And you can manage storage settings directly in the project settings page.  
From there, users can:

- Manage mount paths used by apps; 
- Request additional storage;
- Automatically extend their storage capacity up to **5 GB**.

Requests above 5 GB still require contacting us at <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>.

SciLifeLab Serve uses [FileBrowser](https://github.com/filebrowser/filebrowser), an open-source file management interface, to provide access to storage on persistent volumes.

## Activating file management

To manage files outside of apps or notebooks, you need to activate file management for your project. On your project page, find the **“Manage Files”** section and click **“Activate”**. Once active, you will see an **“Open File Manager”** button. When its status changes to **“Running”**, you can begin using it.

The file management tool stays active for 24 hours. After it expires, you will need to activate it again. Note that your files remain stored on the persistent volume regardless of file management status.

## Uploading and downloading files

Click **“Open File Manager”** to access the web interface. Inside, you will see the folder **`project-vol`** — this is your project's persistent volume. All your files and folders must be placed inside `project-vol` (e.g. `project-vol/my-file.txt`, `project-vol/my-folder/my-file.txt`). Files placed elsewhere may be lost.

You can create new files and folders via the left sidebar.  
You can upload or download files using the top-right menu, including entire folders.

The interface supports large file uploads — we have successfully tested files up to 40 GB (though your available storage may be smaller). If an upload is interrupted, re-upload a file with the same name to the same folder to resume from where it stopped.

## Frequently Asked Questions

**I am stuck while following the guide. Can I get help?**  
Yes. Contact us at <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>. Please include a detailed description of what you tried and where the issue occurred.

**The web interface is not working for my files. Is there an API to upload files?**  
Currently, no API is available for uploading data. However, you can upload a `.zip` or `.tar` archive and use the built-in terminal (press the angle brackets in the top menu) in the File Manager to extract it. At the same time, make the unzipped folder writable by executing the following command: `chmod -R 775 your-folder-name`.

**How much storage can I get?**  
Each project starts with 1 GB. You can request more storage directly in the project settings and automatically extend up to **5 GB**. For larger requests, contact us at <a href="mailto:serve@scilifelab.se">serve@scilifelab.se</a>.

**Can I use this as long-term data storage?**  
Persistent volumes are intended only for storing files required to run apps, models, or notebooks hosted on SciLifeLab Serve. They are not intended for long-term archival storage.

**Can I store a SQLite database for my app?**  
Yes. A SQLite database is just a file, so it can be stored on the persistent volume. Remember that you may **not** store any personal or sensitive data on SciLifeLab Serve.
