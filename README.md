\# BUYBACK - Dota 2 Marketplace

A marketplace for buying and selling Dota 2 virtual items.

This is a full-stack Flask web application built for our Midterm Project. It features user authentication, dynamic marketplace routing, a relational database, and an interactive shopping cart/checkout system.



\## Group Members

\* Marx Juris D. Gabrito

\* John Andraei J. Panizares

\* Ariel Dominic D. Songalia



\## Features

\* \*\*User Authentication:\*\* Registration and Secure Login (Flask-Login).

\* \*\*CRUD Operations:\*\* Users can Create, Read, and Delete their own product listings.

*   **Database:** PostgreSQL database integrated via Flask-SQLAlchemy and Flask-Migrate.

\* \*\*Interactive UI:\*\* Dynamic shopping cart, interactive checkout form, and mockup messaging system.



\## How to Run Locally

1\. Clone this repository.

2\. Create a `.env` file in the project root. Add your `SECRET_KEY`, `DATABASE_URL`, and other secrets. Also, add the following line to enable Flask CLI commands:
   ```
   FLASK_APP=index.py
   ```

3\. Create a virtual environment: `python -m venv venv`

4\. Activate the environment: `venv\\Scripts\\activate`

5\. Install dependencies: `pip install -r requirements.txt`

6\. Run the database migrations: `flask db upgrade`

7\. (Optional) Populate the market: `python seed.py`

8\. Run the application: `flask run`
