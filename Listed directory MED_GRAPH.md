Listed directory MED_GRAPH
Viewed README.md:1-157
Viewed docker-compose.yml:1-106

Here is a comprehensive, step-by-step guide to running the **MedGraph AI** project manually end-to-end. 

There are two main ways to run this project:
1. **Hybrid Development Setup (Recommended)**: Databases run in Docker, while the backend (Python) and frontend (Node.js) run directly on your machine. This is best for active development, debugging, and viewing logs.
2. **Full Docker Setup**: Everything runs in Docker containers. This is easiest if you just want to see the app running without installing dependencies locally.

---

### Prerequisites
Before starting, ensure you have the following installed on your machine:
- **Docker Desktop** (must be running, with WSL2 enabled on Windows)
- **Python 3.12+** (for the backend)
- **Node.js 22+** (for the frontend)
- A **Groq API Key** (for the LLM integrations)

---

### Method 1: Hybrid Development Setup (Recommended)

#### Step 1: Environment Configuration
1. Open a terminal in the root of the project (`c:\Users\ravip\OneDrive\Desktop\MED_GRAPH`).
2. Copy `.env.example` to create your own `.env` file:
   ```cmd
   copy .env.example .env
   ```
3. Open the `.env` file in your editor and add your `GROQ_API_KEY`.

#### Step 2: Start the Databases via Docker
Instead of starting everything, we will use Docker to only start MongoDB, Neo4j, and Qdrant.
```bash
docker compose up -d mongodb neo4j qdrant
```
*(Wait a few moments for the databases to fully initialize).*

#### Step 3: Setup the Python Backend
Open a new terminal window in the project root and run the following:
1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```
2. **Activate the virtual environment:**
   ```bash
   venv\Scripts\activate
   ```
   *(Your terminal prompt should now show `(venv)` at the beginning).*
3. **Install the required dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

#### Step 4: Initialize the Databases
Since this is your first time running the project, you need to set up the schemas for the graph and vector databases. With the virtual environment still activated, run:
```bash
python scripts/init_neo4j.py
python scripts/init_qdrant.py
```

#### Step 5: Start the Backend Server
With the virtual environment active, navigate to the backend folder and start the FastAPI server:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
*The backend API will be running at **http://localhost:8000**. You can view the interactive Swagger docs at **http://localhost:8000/docs**.*

#### Step 6: Start the Frontend React App
Open another new terminal window in the project root, and run the following:
```bash
cd frontend
npm install
npm run dev
```
*The frontend will start on **http://localhost:5173**. Open this URL in your browser to interact with the platform.*

---

### Method 2: Full Docker Deployment
If you prefer not to manage virtual environments and node modules locally, you can spin up the entire stack using Docker Compose.

1. Ensure your `.env` file is created and has your `GROQ_API_KEY` (same as Step 1 above).
2. Open a terminal in the project root and run:
   ```bash
   docker compose up --build -d
   ```
3. Docker will build the backend and frontend containers and start everything. 
4. Once it finishes, you can access the app at:
   - **Frontend UI:** http://localhost *(running on port 80)*
   - **Backend API:** http://localhost:8000

*(Note: For the Full Docker setup, if you are running it for the very first time, you still might need to run the `init_neo4j.py` and `init_qdrant.py` scripts from a local Python environment, or by executing them directly inside the backend docker container).*

### How to Stop the Project
- For the **Frontend/Backend local terminals**: Press `Ctrl + C` in the terminals to stop the servers.
- For **Docker**: Run the following in the project root to stop and remove all containers:
  ```bash
  docker compose down
  ```

Let me know if you hit any errors during setup, especially when installing the Python dependencies or pulling the Docker images!