FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Set environment variable to indicate we're in Docker
ENV RUNNING_IN_DOCKER=true

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    firefox \
    tor \
    xvfb \
    x11vnc \
    novnc \
    net-tools \
    wget \
    unzip \
    libx11-xcb1 \
    libdbus-glib-1-2 \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Firefox GeckoDriver
RUN GECKODRIVER_VERSION=$(wget -qO- "https://api.github.com/repos/mozilla/geckodriver/releases/latest" | grep -Po '"tag_name": "\K.*?(?=")') \
    && wget -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz \
    && tar -C /usr/local/bin -zxf /tmp/geckodriver.tar.gz \
    && chmod +x /usr/local/bin/geckodriver \
    && rm /tmp/geckodriver.tar.gz

# Set up VNC server
RUN mkdir -p /usr/share/novnc/utils/websockify
RUN wget -qO- https://github.com/novnc/noVNC/archive/v1.3.0.tar.gz | tar xz --strip 1 -C /usr/share/novnc
RUN wget -qO- https://github.com/novnc/websockify/archive/v0.10.0.tar.gz | tar xz --strip 1 -C /usr/share/novnc/utils/websockify

# Set up working directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Create directories for data persistence
RUN mkdir -p /app/data/output /app/data/html_snapshots

# Create supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports for noVNC and Tor
EXPOSE 8080 9050 9051

# Set up entrypoint
ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]