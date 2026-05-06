# Node.js installer
# ARG NODE_VERSION=22
ARG NODE_VERSION=22

RUN curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node --version
