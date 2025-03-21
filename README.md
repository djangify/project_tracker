Project Tracker 

# Project Tracker

A Django-based project management system to track and manage multiple projects, tasks, and work sessions.

## Features

- Track projects with status (active, paused, completed)
- Manage tasks for each project
- Log work sessions to monitor progress
- REST API for integration with other systems
- Responsive UI using Tailwind CSS

## Project Structure

The application follows a clean Django project structure:

- `config/`: Main Django configuration (settings, urls, wsgi)
- `core/`: Shared functionality and home page
- `projects/`: Project management app with models and views
- `templates/`: Project-wide templates
- `static/`: Static files (CSS, JS, images)

## Setup

### Prerequisites

- Python 3.8+
- MariaDB/MySQL (or SQLite for development)
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/project-tracker.git
cd project-tracker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your environment settings:
```
SECRET_KEY=your-secret-key
DB_NAME=project_tracker
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Visit http://localhost:8000 in your browser

## Deployment

### cPanel Deployment

1. Upload the project to your cPanel hosting account
2. Create a MySQL/MariaDB database
3. Update the `.env` file with production settings
4. Make sure the `passenger_wsgi.py` file is in the project root
5. Configure the domain to point to the project directory

## API Endpoints

The application provides a REST API for projects, tasks, and work sessions:

- `/projects/api/projects/` - Project management
- `/projects/api/tasks/` - Task management
- `/projects/api/sessions/` - Work session management

## License

MIT
