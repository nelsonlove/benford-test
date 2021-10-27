# benford-test

Web application built with Flask/Vue.js for testing conformity of .csv data to Benford's Law.

This app allows users to upload a CSV file with numerical data and test it for conformity to [Benford's Law](https://en.wikipedia.org/wiki/Benford's_law), a statistical phenomenon that can be used in forensic accounting to detect fraud. The law states that in a large set of numbers, leading digits occur with a frequency that is logarithmic to their rank. For example, the number 1 should occur about 30% of the time, while the number 9 should occur about 4.5% of the time.

The specifications to which I built this app can be found at [`specifications.md`](https://github.com/nelsonlove/benford-test/blob/main/specifications.md).

## Features

Features include:

- Simple user interface with single-page architecture
  - Reactive UI elements with Vue.js
  - Bootstrap-based responsive layout
  - Separation between backend and frontend via RESTful API
- Multiple file upload
  - Persistence of uploaded files via a SQLite database
  - Handles exceptions with user feedback, e.g., improperly formatted or non-numeric .csv files
- Preview of uploaded .csv files:
  - Displays filename with row/column count
  - Table of first six rows (five plus header) of file
  - Enumerates columns with numerical data viable for analysis
- Analysis of CSV data:
  - Histogram and frequency table shows expected/observed distributions
  - Test of conformity to Benford's law (Pearson's chi-square goodness-of-fit test)
    - Dropdown menu for p-values from 0.001 to 0.01
    - Test statistic, critical value, and test result for chosen p-value
    - Description of null hypothesis and interpretation of result
- Exception handling:
  - Improperly formatted .csv files or files without numerical data
  - Selected columns which are more than 10% non-numeric

## Demo

A live demo running on AWS Elastic Beanstalk is available [here](http://benford.nelson.love).

## Docker

I have uploaded a container to [Docker Hub](https://hub.docker.com/r/nelsonlove/benford):

`docker pull nelsonlove/benford`

## Tests/Workflows

A number of tests are included in this repo, including tests making use of Benford's original data to ensure that the numerical analysis is accurate. These tests are split into two subdirectories, `tests/backend` and `tests/cypress`. I have written four GitHub Actions workflows for this project, found in the `./github/workflows` subdirectory:

- `backend-tests.yml` and `cypress-tests.yml` trigger on a push event. They do what their names suggest. Backend tests are handled by `python -m unittest discover`; the `cypress-tests.yml` workflow starts a Flask instance in the background before running Cypress.
- `docker-hub-push.yml` and `elastic-beanstalk-deploy.yml` also do what they sound like. Each is triggered manually or on a publish event.
