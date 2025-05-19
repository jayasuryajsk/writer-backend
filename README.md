# Writer Backend
A minimal backend project for writing applications.

## Quickstart
```bash
git clone <repo-url>
cd writer-backend
docker compose up
```

## Environment Variables
| Variable | Description |
| -------- | ----------- |
| `ZED_SERVER_URL` | URL for the Zed frontend to reach this backend |
| `DATABASE_URL` | Postgres connection string |

## Google OAuth Setup in Supabase
1. Log in to your Supabase project.
2. Go to **Authentication > Settings > External OAuth Providers**.
3. Enter your Google client ID and secret and save.

To point Zed at this backend, set `ZED_SERVER_URL=https://api.$DOMAIN`.

## API Endpoints
| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/health` | Health check |
| POST | `/login` | Authenticate user |

## Secrets
Create a `.env` file in the project root to store environment variables and secrets. These values will be loaded by the application at runtime.

For more details on project setup and testing, see [AGENTS.md](agents.md).
