# Flask-Banking-Application
## Project Description
This is a Flask web application that functions as a banking app with two pages: a login page and a dashboard page for logged-in users.

The login page has two forms, one for logging in and one for creating a new account. The login form has fields for a username and password, while the create account form has fields for a first name, last name, email, username, password, and confirm password. Both forms use POST requests to submit data to the server.

The dashboard page displays the user's balance and transaction history in a table. It has buttons for depositing and withdrawing funds, and a log out button that sends a GET request to the server. The transaction forms are hidden by default and are shown when the deposit or withdraw button is clicked using JavaScript. The forms use POST requests to submit data to the server.

The application also uses the Flask flash message system to display success and error messages to the user. The messages are displayed at the top of the page and are styled differently based on their category (success, info, warning, or danger). The application also uses CSS to style the pages and jQuery DataTables to display the transaction table.

This app uses a SQLite database that allows users to create an account, log in, and view their account information. The database has two tables: 'users' and 'transactions'. The 'users' table contains information about each user, including their user ID, name, email, username, password, balance, and account creation date. The 'transactions' table contains information about each transaction, including the transaction ID, user ID, transaction type (e.g., deposit, withdrawal), transaction amount, memo, and transaction time.

The application has several routes:

#### '/' (index): displays the home page and creates the 'users' and 'transactions' tables if they don't already exist.
#### '/create_account': creates a new user account with the given information.
#### '/login': logs in the user with the given username and password.
#### '/logout': logs out the current user.
#### '/dashboard/<username>': displays the dashboard for the given user, including their account balance and transaction history.
#### '/deposit': allows the user to deposit money into their account.
#### '/withdraw': allows the user to withdraw money from their account.

The application also includes some helper functions for validating input and generating unique IDs.

## Example Pages:
### User Login
![image](https://user-images.githubusercontent.com/87671757/224449013-71f774b5-2524-48c0-b0a1-2ea6daf01a09.png)

### User Account Dashboard
![image](https://user-images.githubusercontent.com/87671757/224448951-4f24278b-8532-47fc-aecd-3ee85629969d.png)
