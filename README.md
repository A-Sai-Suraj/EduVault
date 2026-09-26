# EduVault

## Run with Docker

Build the image from the project root:

```sh
docker build -t my-streamlit-app .
```

Run it locally:

```sh
docker run --rm -p 8501:8501 my-streamlit-app
```

Open <http://localhost:8501>.

`ADMIN_PASSWORD` is optional. Set it to enable the admin login; without it, the
admin panel remains inaccessible. For local use, copy `.env.example` to `.env`,
set the value there, and run `docker run --rm -p 8501:8501 --env-file .env
my-streamlit-app`. Keep `.env` out of source control. Streamlit's local
`.streamlit/secrets.toml` fallback remains supported outside the image.

## Cloud deployment

Deploy the root `Dockerfile` on Railway or Render; both provide `PORT` at
runtime, which the container uses automatically. Set `ADMIN_PASSWORD` in the
platform's environment/secrets settings if admin access is needed. Google Cloud
Run provides `PORT` (normally `8080`) in the same way.

For Hugging Face Spaces, create a Docker Space and configure its exposed
container port as `7860`; set `PORT=7860` in the Space variables. Store
`ADMIN_PASSWORD` in Space secrets, not in this repository.

## SQLite persistence

The image includes the populated `academic_hub.db`. Admin changes are written to
SQLite inside the running container. Container-local writes may be lost when a
platform replaces or restarts the container; configure persistent storage at
`/app/academic_hub.db` where the platform supports it, or arrange backups before
replacing instances. The app continues to use SQLite and does not require a
separate database service.