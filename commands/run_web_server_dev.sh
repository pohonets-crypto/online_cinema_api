#!/bin/sh

# Run web server
uvicorn online_cinema.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /usr/src/online_cinema
