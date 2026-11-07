# VisionAlert

## Development

Pull the latest changes and apply migrations from the repository root:

```powershell
git pull
.\venv\Scripts\python.exe manage.py migrate
```

Run the backend and frontend in two terminals.

Terminal 1, from the repository root:

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Open the frontend at `http://localhost:5173`.

## Checks and tests

From the repository root:

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test core_app
```

From the `frontend` directory:

```powershell
npm run lint
npm run build
```
