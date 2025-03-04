# PS1 - ERA Payment Posting

## Description:
A description of your digital worker here

## Automations
- Please list all applications / APIs this DW automates and integrates, and [link to documentation](https://www.google.com)

###[PDD](https://airtable.com/) (Please update this URL with your DWs PDD)
___
## Preflight:
   0. Have an AE get your manifest.yaml from devex team 

        ( tools for generating the manifest are in development )

   1. [Connect to AWS CodeArtifact](https://www.notion.so/thoughtfulautomation/Connect-to-AWS-CodeArtifact-a1b06ba960d44d23b7315f30be961efa) (our private repo)

   2. Install basic requirements (run the following command)
       
        `pip install -r requirements.txt`

   3. Checkout a new branch from dev

## Developer Notes
All Digital workers going forward must implement supervisor! The quickstart guide for supervisor can be found [here](https://www.notion.so/thoughtfulautomation/Supervisor-QS-2b22c7a111b8466481d78df3ff1cc5b4). Our goal is for supervisor to easily update the front-end as the DW runs - [here is an example of the resulting work report the client sees](https://app.thoughtfulautomation.dev/reports/work/2211)

## File Descriptions
| File                     | Purpose                                                                                                           |
|--------------------------|-------------------------------------------------------------------------------------------------------------------|
| VERSION                  | Defines the version of the DW (initial release is 1.0)                                                            |
| .pre-commit-config.yaml  | Defines the checks that are performed during pre-commit                                                           |
| bitbucket-pipelines.yaml | Defines the bitbucket pipelines (runs pre-commit and pushes to robocloud)                                         |
| conda.yaml               | Used to build the environment on Robocloud                                                                        |
| manifest.yaml            | Used by supervisor to map functions to steps in our automation and update the front-end as the DigitalWorker runs |

# Delete Batches Script
     delete_batches.py
### Purpose
This code is designed to facilitate the deletion of batches based on data provided in Excel or Json files. It automates the process of identifying batches to be deleted and performs the deletion within the NextGen application.

### How to Run
To execute this code, follow these steps:

1. Place the following files in the same directory as the script:
    - `Need to Delete Batches.xlsx`: Excel file containing data on batches to be deleted, with columns 'NUM' and '835 FILE'.
    - `Proliance Mapping.xlsx`: Excel file containing mapping data, with columns 'WS_ID' and 'APP_NAME'.

2. If you already have a json file in the following format, you don't need the previous files

          [
               {
                    "num": "xxxxxxx",
                    "app_name": "xxxxxxxxxxxxxxxx"
               },
               ...
          ]
3. Run the script by executing the following command in your terminal or command prompt:
    ```
    python delete_batches.py
    ```

4. **Optional Argument:**
    - `--xlsx`: In case you don't have the Json, use this optional argument to create it from the xlsx's files

### Required Columns for the XLSX File
The script expects the following columns in the input Excel files:
- For "Need to Delete Batches.xlsx":
    - `NUM`: Represents the check number.
    - `835 FILE`: Represents the file, used to find the Practice in the other file.

- For "Proliance Mapping.xlsx":
    - `WS_ID`: Used to match with `835 FILE` and retrieve the row.
    - `APP_NAME`: Represents the application name (Practice).

### Result
After running the script, batches specified in the input files will be deleted from the NextGen application. The script will generate a file named `batches_to_delete.json`, which contains information about the deleted batches. Additionally, the script provides logs for each step of the deletion process.

### Possible issues
 - Window not found
