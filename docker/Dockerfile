FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install desktop environment, VNC, Firefox, Python, and dependencies
RUN apt-get update && apt-get install -y \
    firefox \
    python3 \
    python3-pip \
    python3-venv \
    xfce4 \
    xfce4-terminal \
    tightvncserver \
    novnc \
    net-tools \
    supervisor \
    tor \
    curl \
    wget \
    gnupg \
    unzip \
    dbus-x11 \
    x11-xserver-utils \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a user to run the VNC server
RUN useradd -m -s /bin/bash tracker && \
    echo "tracker:tracker" | chpasswd && \
    mkdir -p /home/tracker/.vnc

# Set up VNC password
RUN echo "tracker" | vncpasswd -f > /home/tracker/.vnc/passwd && \
    chmod 600 /home/tracker/.vnc/passwd && \
    chown -R tracker:tracker /home/tracker/.vnc

# Set up noVNC (HTML5 VNC client)
RUN mkdir -p /usr/share/novnc/utils/websockify && \
    ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Install geckodriver for Selenium
RUN GECKODRIVER_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep tag_name | cut -d '"' -f 4) && \
    wget https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz && \
    tar -xzf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz -C /usr/local/bin && \
    chmod +x /usr/local/bin/geckodriver && \
    rm geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Create directories for project
RUN mkdir -p /ransomware-tracker/data/output && \
    mkdir -p /ransomware-tracker/data/html_snapshots && \
    mkdir -p /ransomware-tracker/config/sites && \
    mkdir -p /ransomware-tracker/config/code && \
    chown -R tracker:tracker /ransomware-tracker

# Copy project files
COPY --chown=tracker:tracker tracker /ransomware-tracker/tracker
COPY --chown=tracker:tracker config /ransomware-tracker/config

# Create a desktop shortcut to run the tracker
RUN mkdir -p /home/tracker/Desktop
COPY --chown=tracker:tracker docker-resources/run-tracker.sh /home/tracker/Desktop/
RUN chmod +x /home/tracker/Desktop/run-tracker.sh

# Create supervisor configuration
COPY docker-resources/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set up entrypoint script
COPY docker-resources/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose VNC and noVNC ports
EXPOSE 5901 6080

# Set up working directory
WORKDIR /ransomware-tracker

# Start the supervisord
ENTRYPOINT ["/entrypoint.sh"]