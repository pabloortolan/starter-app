# Docker Starter App 🐳

A tiny web app (Python + Redis) built to learn the everyday building blocks of
modern IT and cloud: **Git/GitHub, Docker, Docker Compose, CI/CD and cloud deployment**.

```
 ┌──────────── your laptop / a cloud server ────────────┐
 │                                                      │
 │   browser ──► [ web container ] ──► [ redis container ]
 │               Flask + Gunicorn        visit counter  │
 │               port 8000               + volume       │
 └──────────────────────────────────────────────────────┘
        ▲
        │  image built automatically by GitHub Actions
        │  and stored in GitHub Container Registry (ghcr.io)
```

## What's in the box

| File | What it teaches |
|---|---|
| `app/main.py` | A small web app with `/`, `/health` and `/info` endpoints |
| `tests/test_app.py` | Automated tests (run in the pipeline) |
| `Dockerfile` | How to package an app into an image (layers, caching, non-root user, healthcheck) |
| `docker-compose.yml` | Running several containers together (networking, volumes, env vars) |
| `.github/workflows/ci.yml` | CI/CD: test → build → publish an image on every push |
| `.dockerignore` / `.gitignore` | Keeping junk out of images and repos |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux)
- [Git](https://git-scm.com/downloads)
- A free [GitHub](https://github.com) account
- A code editor — [VS Code](https://code.visualstudio.com/) is a good choice

---

## The learning path

Do one level per session. Each one builds on the previous.

### Level 1 — Run a single container

```bash
docker build -t starter-app .
docker run -p 8000:8000 starter-app
```

Open http://localhost:8000. The counter shows `?` and Redis is "unavailable" —
that's expected, the app is alone in its container.

Try:
- `docker images` — see the image you built and its size
- `docker ps` — see the running container; note its ID matches "Served by container …" on the page
- `docker logs <container-id>` — see the web server logs
- `docker exec -it <container-id> sh` — open a shell *inside* the container, look around, `exit`
- `docker history starter-app` — see the layers from your Dockerfile

💡 **Concept:** an *image* is the packaged app (like a template); a *container* is a running instance of it.

### Level 2 — Multi-container app with Compose

```bash
docker compose up --build
```

Now the counter works. Refresh a few times.

Try:
- `docker compose down` then `docker compose up` — the counter **keeps its value** (that's the volume)
- `docker compose down -v` — the `-v` deletes the volume, the counter resets
- `docker compose ps` / `docker compose logs -f web`
- Stop just the database: `docker compose stop redis` — the site still loads but shows "unavailable". Start it again.

💡 **Concepts:** containers talk to each other by service name (`REDIS_HOST: redis`);
containers are disposable, so persistent data lives in *volumes*.

### Level 3 — Put it on GitHub

1. Create an empty repository on GitHub (no README), e.g. `docker-starter-app`
2. In this folder:

```bash
git init
git add .
git commit -m "First version"
git branch -M main
git remote add origin https://github.com/<your-username>/docker-starter-app.git
git push -u origin main
```

### Level 4 — CI/CD with GitHub Actions

As soon as you push, open the **Actions** tab of your repo. You'll see the pipeline:

1. **test** — installs Python and runs the tests
2. **build-and-push** — builds the Docker image and publishes it to `ghcr.io/<you>/docker-starter-app`

Find the image under your GitHub profile → **Packages**. Now anyone (or any server) can run it:

```bash
docker run -p 8000:8000 ghcr.io/<your-username>/docker-starter-app:latest
```

(Packages are private by default — make it public in the package settings, or `docker login ghcr.io` first.)

Try:
- Break a test on purpose (`assert False`), push, and watch the pipeline turn red and **refuse to publish** the image
- Work on a branch and open a Pull Request — only the tests run, nothing is published

💡 **Concept:** CI = every change is tested automatically. CD = every good change is packaged and shipped automatically.

### Level 5 — Deploy to the cloud

The same image runs anywhere. Pick the cloud your company uses — they all have a
"give me a container image, I'll run it" service:

| Cloud | Service | Good to know |
|---|---|---|
| Microsoft Azure | Azure Container Apps | Very common in corporate environments |
| AWS | App Runner or ECS | Most widely used cloud overall |
| Google Cloud | Cloud Run | Probably the simplest to start with |

Point the service at your `ghcr.io/...` image, set port **8000**, and you get a public URL.
The app will show Redis "unavailable" — that's fine; adding a managed Redis
(Azure Cache for Redis, AWS ElastiCache, Google Memorystore) and setting `REDIS_HOST`
is a great next exercise.

⚠️ Check the free tier / pricing page first and delete resources when you're done.

### Level 6 — Ideas to go further

- **Scaling:** change the web port mapping to `"8000-8002:8000"` and run
  `docker compose up --scale web=3`. Hit `/info` on ports 8000, 8001, 8002 — different hostnames.
- **Configuration:** add a `.env` file and read a new setting (e.g. a page title) from an environment variable
- **Reverse proxy:** add an `nginx` service in front of `web`
- **Security scanning:** add a step to the pipeline that scans the image with [Trivy](https://github.com/aquasecurity/trivy-action)
- **Kubernetes:** run the same image on a local cluster with [kind](https://kind.sigs.k8s.io/) or minikube
- **Infrastructure as Code:** create the cloud resources with Terraform instead of clicking in the portal

---

## Run without Docker (for development)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest                             # run the tests
python -m app.main                 # start the dev server on http://localhost:8000
```

## Cheat sheet

| Command | Does |
|---|---|
| `docker build -t name .` | Build an image from the Dockerfile in this folder |
| `docker run -p 8000:8000 name` | Run it, mapping host port → container port |
| `docker ps` / `docker ps -a` | Running containers / all containers |
| `docker logs -f <id>` | Follow a container's logs |
| `docker exec -it <id> sh` | Shell inside a running container |
| `docker stop <id>` / `docker rm <id>` | Stop / delete a container |
| `docker compose up --build -d` | Start the stack in the background |
| `docker compose down` | Stop and remove the stack (keeps volumes) |
| `docker system prune` | Clean up unused images/containers |
