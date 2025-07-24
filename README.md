# PayRupeerr - Transactions Made Easy

PayRupeerr is a Django-based banking and financial management web application designed to simplify transactions, manage accounts, and provide AI-powered insights for users. The project includes features such as account management, transaction history, AI chatbot assistance, virtual cards, financial goals, and more.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Deployment](#deployment)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)
- [Contact](#contact)
## Features

- **User Account Management**: Create, view, and manage multiple bank accounts. Each user can have several accounts, each with its own transaction history and details.
- **Transaction Tracking**: View all transactions, filter by type (debit/credit), date, or account. Analyze spending patterns with built-in summaries and visualizations (charts, graphs).
- **AI Chatbot Assistant**: Integrated AI assistant for user queries, financial advice, and help navigating the platform. The chatbot can answer questions about your accounts, spending, and more.
- **Virtual Cards**: Instantly generate and manage virtual cards for secure online transactions. Set spending limits, freeze/unfreeze cards, and monitor card-specific transactions.
- **Financial Goals**: Set, track, and manage personal financial goals (e.g., saving for a trip, emergency fund). Visual progress bars and reminders help users stay on track.
- **Security Settings**: Advanced security features including device fingerprinting, login activity tracking, two-factor authentication (2FA), and customizable security options.
- **Upcoming Transactions**: Schedule and view upcoming payments, transfers, and recurring bills. Get reminders for due dates and insufficient balance alerts.
- **Admin Dashboard**: Powerful Django admin interface for managing users, accounts, transactions, and system settings. Includes analytics and reporting tools.
- **PDF & Report Generation**: Download account statements and transaction reports as PDFs using integrated ReportLab support.
- **Mobile-Friendly UI**: Responsive design ensures a seamless experience on both desktop and mobile devices.

## Tech Stack

- **Backend**: Python, Django
- **Database**: SQLite (default, can be switched to MySQL)
- **Frontend**: Django Templates, HTML, CSS, JavaScript
- **AI Integration**: Custom AI assistant module
- **Other Libraries**: Pillow (image processing), ReportLab (PDF generation), MySQLdb (MySQL support), Chardet, SQLParse

## Project Structure

```
PayRupeerr/
├── Bank/
│   ├── migrations/
│   ├── static/
│   ├── templates/
│   ├── __init__.py
│   ├── admin.py
│   ├── ai_assistant.py
│   ├── apps.py
│   ├── deco.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── PayRupeerr/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── db.sqlite3
├── manage.py
└── env1/ (virtual environment)
```

## Getting Started

### Prerequisites

### Demo Credentials
- You can use the Django admin panel to create test users and accounts for demo purposes.

### Setup Instructions

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/bipinjoseph/PayRupee---Transactions-Made-Easy.git
   cd PayRupee---Transactions-Made-Easy
   ```
2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv env1
   .\env1\Scripts\activate
   ```
3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, install manually:)*
   ```powershell
   pip install django pillow reportlab mysqlclient chardet sqlparse
   ```
4. **Apply migrations:**
   ```powershell
   python manage.py migrate
   ```
5. **Create a superuser (for admin access):**
   ```powershell
   python manage.py createsuperuser
   ```
6. **Run the development server:**
   ```powershell
   python manage.py runserver
   ```
7. **Access the app:**
   - Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.
   - Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## Usage
- Register or log in to manage your accounts and transactions.
- Use the AI chatbot for assistance, financial insights, and help with platform features.
- Set up and manage virtual cards for secure online purchases.
- Define and track your financial goals with visual progress.
- Schedule upcoming transactions and receive reminders.
- Download account statements as PDFs.
- Admins can manage users, accounts, and transactions via the admin dashboard.

## Deployment

### Local Deployment
Follow the setup instructions above to run the project locally for development or testing.

### Production Deployment
1. **Configure Environment Variables:**
   - Set `DEBUG = False` in `PayRupeerr/settings.py`.
   - Configure `ALLOWED_HOSTS` for your domain or server IP.
   - Set up a secure secret key.
2. **Database:**
   - Switch from SQLite to MySQL or PostgreSQL for production.
   - Update `DATABASES` in `settings.py` accordingly.
3. **Static Files:**
   - Run `python manage.py collectstatic` to gather static files.
   - Serve static files using a web server (e.g., Nginx, Apache).
4. **Web Server:**
   - Use Gunicorn or uWSGI as the WSGI server behind Nginx/Apache.
5. **SSL:**
   - Set up HTTPS for secure connections.

## FAQ

**Q: Can I use this project for my own bank or fintech startup?**
A: Yes, the project is open-source under the MIT License. Please review the license terms.

**Q: How do I enable or customize the AI assistant?**
A: The AI assistant logic is in `Bank/ai_assistant.py`. You can extend or replace it as needed.

**Q: How do I switch to MySQL or another database?**
A: Install the appropriate database driver (e.g., `mysqlclient` for MySQL), update `DATABASES` in `PayRupeerr/settings.py`, and run migrations.

**Q: Is there a REST API?**
A: Not yet, but the project is structured to allow easy addition of Django REST Framework endpoints.

**Q: How do I reset my admin password?**
A: Use Django's built-in password reset or run `python manage.py changepassword <username>`.
## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License.

## Author
- [Bipin Joseph](https://github.com/bipinjoseph)

## Contact

For questions, support, or business inquiries, please contact:
- Email: bipinjoseph@example.com
- GitHub Issues: [PayRupee---Transactions-Made-Easy/issues](https://github.com/bipinjoseph/PayRupee---Transactions-Made-Easy/issues)
