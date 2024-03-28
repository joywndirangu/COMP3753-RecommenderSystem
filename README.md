# COMP3753-RecommenderSystem

# Installation Instructions

Follow these steps to set up the project on your local environment.

## Step 1: MySQL Installation

1. Download and install a version of MySQL. You can obtain MySQL through various means, but for this setup, it was acquired through AMPPS.
2. Add the MySQL installation location to your system's `%PATH%` environment variable. This step is crucial for ensuring that MySQL commands can be executed from the command line or terminal without specifying the full path to the MySQL binaries.

## Step 2: MySQL Configuration

1. The application expects a specific MySQL user configuration. Ensure that the username and password for your MySQL root user are set to the following:
   - **Username**: root
   - **Password**: mysql
2. If you prefer to use a different user for the MySQL connection, you can do so by editing the `connector.init()` function within the `connector.py` file. Replace the default credentials with your custom username and password.

## Step 3: Project Setup

1. Pull the latest version of this git repository to your local machine.
2. Navigate to the project directory and run the `main.py` file. You can do this from the command line or terminal with the following command:
   ```bash
   python main.py
