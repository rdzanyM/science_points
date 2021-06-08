# science_points
App is available at https://ministry-points.herokuapp.com/

## Deployment <a href="https://dashboard.heroku.com/apps/ministry-points"><img src="https://user-images.githubusercontent.com/43205483/120186868-5f5d0c00-c214-11eb-8d02-615152c161c7.png" width="32" height="32"></a>

The app is deployed on Heroku, using free dynos (lightweight, isolated Linux containers). They have a [limit](https://devcenter.heroku.com/articles/free-dyno-hours) of 550 hours of activity per month. They sleep after 30 minutes of inactivity to preserve remaining free hours. Because of that the first opening of an app can be a bit slower.  

Managing the deployed app (viewing logs, setting url etc.) is available through the Heroku account. To have the access, the account has to be added as a collaborator. The app ownership can also be trasfered to a chosen account. If for some reason access cannot be granted, one could also fork this repository and [link their own app](https://devcenter.heroku.com/articles/github-integration) to this fork.  

The Heroku app is linked to this GitHub repository and is updated after every change to the *deploy* branch. 

## Updating the data
### Access
To update the data, the repository access is required to modify the branches. Again, the repository ownership can be tranfered to a chosen account and if for some reason access cannot be granted, one could also fork this repository and [link their own app](https://devcenter.heroku.com/articles/github-integration) to this fork.  
### Journals and conferences
If a new data is published it can be added to the app by:
* placing the .xlsx file [here](https://github.com/rdzanyM/science_points/tree/deploy/data/journals) and setting the filename as *wykaz_czasopism_DD-MM-YYYY.xlsx*
* adding the entry with an url, date and title to the [config](https://github.com/rdzanyM/science_points/blob/deploy/config.yaml)
* running the [build_db](https://github.com/rdzanyM/science_points/blob/deploy/build_db.py) script to update the database
* pushing the changes to the *deploy* branch

The script assumes that the data format will be the same as in 09-02-2021 data. If the format changes, the new .xlsx file can be modified to fit the 09-02-2021 data format (for example by deleting any new columns and moving the records so that the data starts at the same cells as in 09-02-2021 file).

### Monographs
The data for monographs is scraped from given urls, so the necessary steps to update it are:
* adding the entry with an url, date and title to the [config](https://github.com/rdzanyM/science_points/blob/deploy/config.yaml)
* running the [build_db](https://github.com/rdzanyM/science_points/blob/deploy/build_db.py) script to update the database
* pushing the changes to the *deploy* branch

## Running the app localy
To run the app localy, one can pull the *deploy* branch and run the [app.py](https://github.com/rdzanyM/science_points/blob/deploy/app.py) script. The required packages can be installed via the `pipenv install` command.

