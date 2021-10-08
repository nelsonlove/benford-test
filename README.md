# benford-test
Flask/Vue app for testing conformity of .csv data to Benford's Law

This is a responsive web app built on Flask and Vue.js which accepts .csv files as input, allows users to select a target column with numerical data for analysis, and performs Pearson's chi-square goodness-of-fit test to determine if the frequency of leading digits in the data conforms to Benford's law. The app also persists uploaded information via a SQLite database file.

A live demo running on AWS Elastic Beanstalk is available [here](http://benford.nelson.love) and I have uploaded a container to [Docker Hub](https://hub.docker.com/r/nelsonlove/benford):

`docker pull nelsonlove/benford`

Backend and analysis tests are included in the `tests` directory.
