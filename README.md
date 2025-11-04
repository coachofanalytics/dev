<<<<<<< HEAD
# Biashara Bridges



## Features

- Django 5.2.7
- Bootstrap 5.3.2 frontend
- PostgreSQL database
- Responsive design
- User authentication ready
- Media and static file handling

## Prerequisites

- Python 3.13.5
- PostgreSQL (installed and running)
- pip

## Installation

1. **Clone the repository** (if using git):
   ```bash
   git clone <repository-url>
   cd biashara_bridges
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows Git Bash
   # or
   venv\Scripts\activate  # On Windows CMD
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env` (if available)
   - Update the `.env` file with your PostgreSQL credentials:
     ```
     DB_NAME=biashara_bridges
     DB_USER=postgres
     DB_PASSWORD=your_password_here
     DB_HOST=localhost
     DB_PORT=5432
     SECRET_KEY=your-secret-key-here
     DEBUG=True
     ALLOWED_HOSTS=localhost,127.0.0.1
     ```

5. **Create the PostgreSQL database**:
   ```bash
   psql -U postgres -c "CREATE DATABASE biashara_bridges;"
   ```

6. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

9. **Access the application**:
   - Home page: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/

## Project Structure

```
biashara_bridges/
├── config/              # Django project settings
│   ├── settings.py     # Main settings file
│   ├── urls.py         # URL configuration
│   └── wsgi.py         # WSGI configuration
├── templates/          # HTML templates
│   ├── base.html      # Base template with Bootstrap 5
│   └── home.html      # Home page template
├── static/            # Static files
│   ├── css/          # CSS files
│   └── js/           # JavaScript files
├── media/            # User uploaded files
├── venv/             # Virtual environment
├── manage.py         # Django management script
├── requirements.txt  # Python dependencies
└── .env             # Environment variables (not in git)
```

## Technologies Used

- **Backend**: Django 5.2.7
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5.3.2
- **Icons**: Bootstrap Icons
- **Environment Management**: python-decouple
- **Image Processing**: Pillow

## Development

To start development:

1. Activate the virtual environment
2. Make sure PostgreSQL is running
3. Run the development server: `python manage.py runserver`
4. Access the application at http://localhost:8000/

## License

All rights reserved © 2024 Biashara Bridges
=======
# Biashara Bridges



## Features

- Django 5.2.7
- Bootstrap 5.3.2 frontend
- PostgreSQL database
- Responsive design
- User authentication ready
- Media and static file handling

## Prerequisites

- Python 3.13.5
- PostgreSQL (installed and running)
- pip

## Installation

1. **Clone the repository** (if using git):
   ```bash
   git clone <repository-url>
   cd biashara_bridges
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows Git Bash
   # or
   venv\Scripts\activate  # On Windows CMD
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env` (if available)
   - Update the `.env` file with your PostgreSQL credentials:
     ```
     DB_NAME=biashara_bridges
     DB_USER=postgres
     DB_PASSWORD=your_password_here
     DB_HOST=localhost
     DB_PORT=5432
     SECRET_KEY=your-secret-key-here
     DEBUG=True
     ALLOWED_HOSTS=localhost,127.0.0.1
     ```

5. **Create the PostgreSQL database**:
   ```bash
   psql -U postgres -c "CREATE DATABASE biashara_bridges;"
   ```

6. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

9. **Access the application**:
   - Home page: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/

## Project Structure

```
biashara_bridges/
├── config/              # Django project settings
│   ├── settings.py     # Main settings file
│   ├── urls.py         # URL configuration
│   └── wsgi.py         # WSGI configuration
├── templates/          # HTML templates
│   ├── base.html      # Base template with Bootstrap 5
│   └── home.html      # Home page template
├── static/            # Static files
│   ├── css/          # CSS files
│   └── js/           # JavaScript files
├── media/            # User uploaded files
├── venv/             # Virtual environment
├── manage.py         # Django management script
├── requirements.txt  # Python dependencies
└── .env             # Environment variables (not in git)
```

## Technologies Used

- **Backend**: Django 5.2.7
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5.3.2
- **Icons**: Bootstrap Icons
- **Environment Management**: python-decouple
- **Image Processing**: Pillow

## Development

To start development:

1. Activate the virtual environment
2. Make sure PostgreSQL is running
3. Run the development server: `python manage.py runserver`
4. Access the application at http://localhost:8000/

## License

All rights reserved © 2024 Biashara Bridges
>>>>>>> 4372396bb28edaacf987601e99c0fe19f72e7fe8
