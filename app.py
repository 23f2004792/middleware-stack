from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import uuid
import time
from collections import defaultdict

EMAIL = "23f2004792@ds.study.iitm.ac.in"

app = FastAPI()

ALLOWED_ORIGINS = [
    "https://app-imaxbw.example.com",
    "https://exam.sanand.workers.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

WINDOW = 10
LIMIT = 8

client_hits = defaultdict(list)


@app.middleware("http")
async def middleware(request: Request, call_next):

    # -------------------------
    # Request ID
    # -------------------------
    request_id = request.headers.get("X-Request-ID")
    if request_id is None:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # -------------------------
    # Skip rate limiting for preflight
    # -------------------------
    if request.method != "OPTIONS":

        client = request.headers.get("X-Client-Id")

        if client:
            now = time.monotonic()

            hits = client_hits[client]

            while hits and now - hits[0] >= WINDOW:
                hits.pop(0)

            if len(hits) >= LIMIT:

                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                )

                origin = request.headers.get("Origin")
                if origin in ALLOWED_ORIGINS:
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"
                    response.headers["Vary"] = "Origin"

                response.headers["X-Request-ID"] = request_id

                return response

            hits.append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }