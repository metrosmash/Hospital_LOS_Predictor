# Refactoring cycle note 

## file style 
we are changing the file layout so this is the newly proposed layout
```
my_web_app/
        ├── .env.example              # Template for environment variables
        ├── Dockerfile                # Container setup for deployment
        ├── pyproject.toml            # Dependencies and tool settings
        ├── README.md
        ├── migrations/               # Database migration scripts (e.g., Alembic)
        ├── src/
        │   └── my_app/
        │       ├── __init__.py
        │       ├── main.py           # Server entrypoint (ASGI/WSGI instance)
        │       ├── config.py         # Environment variables & settings
        │       ├── api/              # Route handlers / endpoints
        │       │   ├── __init__.py
        │       │   └── v1/
        │       ├── core/             # DB connections, auth, shared utilities
        │       ├── models/           # Database ORM schemas
        │       ├── services/         # Core business logic
        │       ├── static/           # CSS, JS, and images (if serving assets)
        │       └── templates/        # Jinja2 / HTML files (if server-rendered)
        └── tests/
            ├── conftest.py
            └── test_api.py
```



## Git development cycle 
(GitHub Flow)

main is production: Always stable, always runnable, always deployable.

Short-lived branches: Branch directly off main using simple prefixes like feat/ or fix/.

PR directly to main: Use automated tests (CI) on the Pull Request, then merge straight into main once verified.

Current-branch is dev for the file changes and refactoring we want to do 