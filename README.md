# Writer Backend
A minimal backend project for writing applications.

## Quickstart
```bash
git clone <repo-url>
cd writer-backend
docker compose up
```

## API Endpoints
| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/health` | Health check |
| POST | `/login` | Authenticate user |

## Secrets
Create a `.env` file in the project root to store environment variables and secrets. These values will be loaded by the application at runtime.

For more details on project setup and testing, see [AGENTS.md](agents.md).
