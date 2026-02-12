# Use Alpine Linux (small, lightweight)
FROM alpine:latest

# Install dependencies
RUN apk add --no-cache \
    wget \
    ca-certificates \
    ffmpeg

# Download Go2RTC
RUN wget -O /usr/local/bin/go2rtc \
    https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_amd64 && \
    chmod +x /usr/local/bin/go2rtc

# Create config directory
RUN mkdir -p /config

# Expose ports
EXPOSE 1984 8554 8555

# Set working directory
WORKDIR /config

# Run Go2RTC
CMD ["go2rtc", "-config", "/config/go2rtc.yaml"]