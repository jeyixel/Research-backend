Based on your uploaded project document, I recommend Python + FastAPI as the backend for your entire project, with Supabase for the database and file storage, and Redis for background AI processing.



This is a good fit for your final-year research project because you need to handle video uploads, run multiple machine-learning models, connect to YouTube APIs, and generate a combined prediction report.



\## 1. The backend technology stack I recommend



\[FastAPI framework Logo PNG Vector (AI) Free Download](https://images.openai.com/static-rsc-4/mmw63tL5nCBVMdFp9xNwd96YrsynXVxEUbND-TJXiR20urNBGKHcLYKfQAduEr3tdpTX5OcZJjkYW1dw7dGskljIn3lBh4ogAqBVKHtiOGbbHGqkwkq9IzhfwMn2KO8eh22R2KNs8wSTzPJT2OzkYClACAqzzMrwcxicoqOrzes?purpose=inline)



FastAPI + Python



Recommended backend



Main API, AI integration, video-processing orchestration and report generation



\[Supabase SVG Icon - Free Supabase PNG \& SVG Download](https://images.openai.com/static-rsc-4/mmSzpSnWSlpeTtirj4LRa5yelpKFVGj-uv7pn-D81vZkzPqVqUV1bJHyLAr4izbxBYsejC4D4vGX3gFJnIS53\_-ZqavT6K9DFtbaBX-bK2aUd6oJkukWLm69khpAmV0I7YM8S00ro97kFnZ3RIJGuPKf8WV8OlBMxX\_OoNWlRNM?purpose=inline)



Supabase



PostgreSQL database, user authentication and video/thumbnail storage



\[Paul Kuruvilla - Build Redis: Ping <-> Pong](https://images.openai.com/static-rsc-4/kSvfU8J7pwh1dte5otNRNCj0-Z6R6Qg2SlpRI2IiDaajL1\_XD-tFhitGhEigHgYuqB5m6b8BZEcFwpZruS4dD3zqlinhmHr0tNlQp5kCE7j4AR5lNcX1QXwO2TQPAXELT78bgt5rVfsiFB8lf2yT8D7--mc5F-RddAfx1g97oAo?purpose=inline)



Redis + RQ



Queue long-running AI analysis tasks outside the API server



\[Yatri Cloud · 50% OFF Cloud Certification Vouchers](https://images.openai.com/static-rsc-4/Mif5Qzd0qx3Jbj-4TuWVI\_O9UDwBlSBL30CyUxSUfYZGP9oKeaWHiWDAVPpobyT8lL6Wrb-lZ1pWXRD-zaUMMUg2XXOaEPzknWtoW7BVHHjTTjHFXwt7f9DNRNV8bPVbZOCAXIqXMgnyelx4CBxJ\_ZSfEsqXafuxj078-zWQ5fI?purpose=inline)



Docker



Consistent development environments across your four-person team



\[GitHub official Logo PNG Vector (EPS) Free Download](https://images.openai.com/static-rsc-4/j6DnFoGR1MfnOBr9lIK962EQdYyxmY8SyJ9-28a69vOkM2BzMHwDekYl2JG6WLr8JTUKKPjN98M-z-HFImt0j5nyukd1e120mDGQLqeLKnLZ8JVrrifApGVGwSFY2cM3RpPDf7Km3KmgvbycYPvr2t5PuRLGFKmpzE2a9ikOtUk?purpose=inline)



GitHub



Version control, module integration and team collaboration



\### Why this matches your project



Your document specifies six modules: A for title/transcript honesty, B for trends, C for CTR, D for retention, E for channel history, and F for fusion, explainability and report generation. The architecture diagram on page 5 shows Modules A–E feeding into Module F.\&#x20;



My part.docx







I'd implement this as a modular Python backend, not six separately deployed microservices. Each teammate can develop their own module, while FastAPI provides a shared interface for calling them.



The backend will eventually work like this:



Frontend



Creator uploads video, thumbnail and metadata



FastAPI backend



Validation, authentication and prediction-job creation



Supabase



Video storage + PostgreSQL



Redis + RQ



Background worker queue



AI analysis workers



A



B



C



D



E



Module F — Fusion + XAI



Final creator report



Predicted CTR, ECR, NAWP and explanations



The important architectural decision is to keep heavy video processing in separate workers. FastAPI's own documentation recommends a dedicated processing system for computationally expensive background jobs.\&#x20;



\[image](https://www.google.com/s2/favicons?domain=https://fastapi.tiangolo.com\\\&sz=32)



FastAPI







For now, we will set up this foundation. No dataset collection, model training or GPU setup is required yet.



\## 2. Accounts you should register



Start with these services. You don't have to pay for cloud hosting or GPU instances at this stage.



| Platform              | What to do                                                                                                                    | Priority |

| --------------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------- |

| GitHub                | \[Create an account](https://github.com?utm\_source=chatgpt.com) and a private project repository. Invite your teammates.       | Now      |

| Supabase              | \[Create an account](https://supabase.com?utm\_source=chatgpt.com) and a project for your database, authentication and storage. | Now      |

| Google Cloud          | \[Create a project](https://console.cloud.google.com?utm\_source=chatgpt.com) and enable YouTube Data API v3.                   | Now      |

| Hugging Face          | \[Register](https://huggingface.co?utm\_source=chatgpt.com) for accessing pretrained ML models.                                 | Later    |

| Render                | \[Register](https://render.com?utm\_source=chatgpt.com) when you need to deploy your FastAPI server and workers.                | Later    |

| Google Colab / Kaggle | Set up GPU notebooks when you start model training.                                                                           | Later    |



\### Set up Supabase



After registering:



1\. Click New Project, select your organization, and choose a project name such as `sl-youtube-performance-ai`.

2\. Choose a strong database password and a nearby supported region.

3\. Wait for the PostgreSQL database to be provisioned.

4\. Under Storage, create three private buckets: `videos`, `thumbnails`, and `reports`.

5\. Find the Project URL, API keys and database connection details. Keep them out of GitHub.



We'll use local PostgreSQL for initial testing, then connect to this Supabase database later. For production, uploaded videos should go directly to private object storage through controlled, resumable uploads rather than passing entire video files through FastAPI.\&#x20;



\[image](https://www.google.com/s2/favicons?domain=https://supabase.com\\\&sz=32)



Supabase Docs



+1







\### Set up Google Cloud



The document identifies YouTube Data API v3 as the public metadata source for Module B's trend intelligence, with channel metadata also relevant to Module E.\&#x20;



My part.docx







Go to Google Cloud Console:



1\. Create a project, for example `sl-youtube-predictor`.

2\. Open APIs \& Services → Library.

3\. Search for YouTube Data API v3 and enable it.

4\. Open Credentials → Create Credentials → API Key.

5\. Restrict the key to the YouTube Data API and, where practical, restrict which backend can use it.

6\. Save it securely for later.



An API key is sufficient to begin working with public YouTube data. You don't need Google OAuth credentials for creator-private analytics yet; we can add those later if the application needs creator-authorized API access.\&#x20;



\[image](https://www.google.com/s2/favicons?domain=https://developers.google.com\\\&sz=32)



Google for Developers







\## 3. Software to install on your laptop



Visual Studio Code



Your development editor



Git



Version control and team integration



Docker Desktop



Runs PostgreSQL and Redis locally



uv



Installs Python and manages your project dependencies



FFmpeg



Video processing and frame extraction when Module D is implemented



Use Python 3.11 as the team's initial shared Python version. It's a conservative choice for packages such as PyTorch, torchvision, XGBoost and computer-vision libraries.



For Windows, install Docker Desktop with WSL2 enabled. You can use PowerShell for the API and Docker commands below.



You can install `uv` with:



Windows PowerShell



```

winget install --id=astral-sh.uv -e

```



macOS / Linux



```

curl -LsSf https://astral.sh/uv/install.sh | sh

```



Restart your terminal after installation, and check:



```

uv --version

git --version

docker --version

docker compose version

```



\## 4. Create your Python backend project



Open a terminal in the folder where you want to build the project.



Step 1 — Initialize the backend



```

uv python install 3.11



uv init creator-performance-backend --bare --python 3.11



cd creator-performance-backend

```



Step 2 — Install the initial backend dependencies



```

uv add "fastapi\[standard]" python-multipart

uv add pydantic-settings sqlalchemy "psycopg\[binary]" alembic

uv add supabase redis rq httpx

uv add --dev pytest ruff

```



What these packages are for



| Package                 | Purpose                                 |

| ----------------------- | --------------------------------------- |

| `fastapi`, `uvicorn`    | Main backend API and development server |

| `python-multipart`      | Receiving uploaded files and form data  |

| `pydantic-settings`     | Managing environment configuration      |

| `sqlalchemy`, `psycopg` | PostgreSQL database connections         |

| `alembic`               | Database schema migrations              |

| `supabase`              | Connecting to Supabase services         |

| `redis`, `rq`           | Background job queues                   |

| `httpx`                 | Calling external APIs                   |

| `pytest`, `ruff`        | Testing and code quality                |



The project will have a `pyproject.toml` and `uv.lock`. Commit both so teammates can install the same dependency versions.



Step 3 — Create the initial folder structure



I recommend organizing your backend like this:



creator-performance-backend/ │ ├── app/ │   ├── \\\_\\\_init\\\_\\\_.py │   ├── main.py │   ├── api/ │   ├── core/ │   ├── db/ │   ├── schemas/ │   ├── workers/ │   │ │   └── modules/ │       ├── module\_a\_integrity/ │       ├── module\_b\_trends/ │       ├── module\_c\_ctr/ │       ├── module\_d\_retention/ │       ├── module\_e\_channel/ │       └── module\_f\_fusion/ │ ├── tests/ ├── compose.yaml ├── .env ├── .env.example ├── .gitignore ├── pyproject.toml └── uv.lock



Create these directories and an empty `app/\_\_init\_\_.py` file manually in VS Code for now.



Each teammate should keep their module's inference code within its own folder, with a defined input/output interface. This makes integration into Module F much easier.



\## 5. Set up local PostgreSQL and Redis



Create a file named `compose.yaml` in the backend project root.



```



services:

&#x20; postgres:

&#x20;   image: postgres:17-alpine

&#x20;   environment:

&#x20;     POSTGRES\_USER: app

&#x20;     POSTGRES\_PASSWORD: localdevonly

&#x20;     POSTGRES\_DB: creator\_predictor

&#x20;   ports:

&#x20;     - "127.0.0.1:5432:5432"

&#x20;   volumes:

&#x20;     - postgres\_data:/var/lib/postgresql/data



&#x20; redis:

&#x20;   image: redis:7-alpine

&#x20;   ports:

&#x20;     - "127.0.0.1:6379:6379"



volumes:

&#x20; postgres\_data:



```



These database credentials are only for local development. Use secure, separately managed credentials when deploying.



With Docker Desktop running, execute:



```

docker compose up -d

```



Then verify that both containers have started:



```

docker compose ps

```



Create a `.env` file in your backend root:



```



DATABASE\_URL=postgresql+psycopg://app:localdevonly@localhost:5432/creator\_predictor



REDIS\_URL=redis://localhost:6379/0



YOUTUBE\_API\_KEY=

SUPABASE\_URL=

SUPABASE\_KEY=



```



You can leave the API values empty until those services are integrated. When switching to Supabase PostgreSQL, replace `DATABASE\_URL` with the connection details from your Supabase dashboard, using a compatible SQLAlchemy/Psycopg URL and an SSL-enabled connection.\&#x20;



\[image](https://www.google.com/s2/favicons?domain=https://supabase.com\\\&sz=32)



Supabase Docs







Also create a `.gitignore`:



```

.env

.venv/

\_\_pycache\_\_/

.pytest\_cache/

.ruff\_cache/

data/

artifacts/

```



Never commit actual API keys or database passwords. Keep an `.env.example` with placeholder values for your teammates.



\## 6. Start the backend and test everything



Create `app/main.py` and paste in:



```

from fastapi import FastAPI, HTTPExceptionfrom pydantic\_settings import BaseSettings, SettingsConfigDictfrom sqlalchemy import create\_engine, textfrom redis import Redisclass Settings(BaseSettings):    database\_url: str    redis\_url: str    model\_config = SettingsConfigDict(env\_file=".env")settings = Settings()app = FastAPI(    title="Sri Lankan YouTube Performance Predictor",    version="0.1.0")@app.get("/health")def health():    return {"status": "ok", "service": "FastAPI"}@app.get("/health/dependencies")def dependencies():    try:        engine = create\_engine(settings.database\_url)        with engine.connect() as connection:            connection.execute(text("SELECT 1"))        engine.dispose()        Redis.from\_url(settings.redis\_url).ping()    except Exception:        raise HTTPException(            status\_code=503,            detail="Database or Redis unavailable"        )    return {"postgres": "ok", "redis": "ok"}

```



Run the backend:



```

uv run uvicorn app.main:app --reload

```



Now open these URLs:



\[localhost:8000/health](http://localhost:8000/health?utm\_source=chatgpt.com)



Check whether FastAPI is running



\[localhost:8000/health/dependencies](http://localhost:8000/health/dependencies?utm\_source=chatgpt.com)



Verify PostgreSQL and Redis connections



\[localhost:8000/docs](http://localhost:8000/docs?utm\_source=chatgpt.com)



View interactive Swagger API documentation



When `/health/dependencies` returns both services as `ok`, you've verified the three most important pieces of your foundation: FastAPI, PostgreSQL and Redis.



You don't need to run RQ workers yet. Once you have actual analysis jobs, start a separate worker process with:



```

uv run rq worker --url redis://localhost:6379/0 analysis

```



Use Linux/WSL2 or a Docker container for standard RQ workers. On native Windows, RQ offers `SimpleWorker` for development.\&#x20;



\[image](https://www.google.com/s2/favicons?domain=https://python-rq.org\\\&sz=32)



python-rq.org







\## 7. AI libraries you'll install later



Your project specifically uses a mixture of NLP, image understanding, temporal video models and tabular prediction, according to Sections 7–9 of the uploaded document.\&#x20;



My part.docx







You do not need to install all of these immediately.



| Module                      | AI libraries to plan for                                        |

| --------------------------- | --------------------------------------------------------------- |

| A — Integrity / Sinhala NLP | `transformers`, `sentence-transformers`                         |

| B — Trend intelligence      | `google-api-python-client`, `sentence-transformers`             |

| C — Thumbnail / CTR         | `opencv-python-headless`, `pillow`, `torchvision`               |

| D — Video retention         | `torch`, `torchvision`, `opencv-python-headless`, system FFmpeg |

| E — Channel history         | `xgboost`, `scikit-learn`, `pandas`                             |

| F — Fusion + XAI            | `scikit-learn`, `shap`, an LLM provider SDK if needed           |



PyTorch and related libraries should be installed when the team confirms its operating systems, CPU/GPU hardware and model requirements. This avoids unnecessary large downloads and potential conflicts now.



For hosting, Render is a reasonable later option for the FastAPI API and a separately deployed worker, while Supabase supplies managed data storage. Render documents both FastAPI web services and background workers, although the required resources may involve paid hosting.\&#x20;



\[image](https://www.google.com/s2/favicons?domain=https://render.com\\\&sz=32)



Render Docs



+1







\## 8. What you should have completed before moving to datasets



Backend setup checklist



0 of 10 completed



Register GitHub and create your backend repository



Register Supabase and create your project



Create a Google Cloud project and enable YouTube Data API v3



Install Git, Docker Desktop, VS Code and uv



Create the FastAPI backend with Python 3.11



Install the initial backend dependencies



Create the modular project folder structure



Start PostgreSQL and Redis through Docker



Create the local .env file and .gitignore



Run FastAPI and verify /health/dependencies and /docs



At that point, the initial environment is ready. The next backend development phase would be building the API routes for video submissions, job status, model outputs and report retrieval. We can do that before collecting any datasets.



One question before you start: Are you developing on Windows 10/11, macOS, or Linux? I can tailor the installation steps and Docker configuration to your operating system so you don't run into platform-specific issues.

