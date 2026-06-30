from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time
from collections import defaultdict

app = FastAPI()

EMAIL = "23f2004792@ds.study.iitm.ac.in"

# Allowed origins
allowed_origins = [
    "https://app-imaxbw.example.com",
    "https://exam.sanand.workers.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

WINDOW = 10  # seconds
LIMIT = 8    # requests

client_hits = defaultdict(list)


# -------------------------
# Rate Limiter Middleware
# -------------------------
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    # Allow CORS preflight without rate limiting
    if request.method == "OPTIONS":
        return await call_next(request)

    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    hits = client_hits[client]

    # Remove old timestamps
    while hits and hits[0] <= now - WINDOW:
        hits.pop(0)

    if len(hits) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    hits.append(now)

    return await call_next(request)


# -------------------------
# Request Context Middleware
# -------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -------------------------
# Root Endpoint
# -------------------------
@app.get("/")
async def root():
    return {"status": "ok"}


# -------------------------
# Ping Endpoint
# -------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }