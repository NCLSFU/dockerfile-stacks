# Git installation via apt (Ubuntu default version)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
