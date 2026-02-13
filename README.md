# Create a Camera Streaming Pipeline using Go2RTC 
### Repository for Docker-based RTSP camera streaming solution that integrates multiple IP cameras with Home Assistant using Go2RTC and WebRTC technology. 


## Table of Contents

- [Overview](#overview)
- [Project Goals](#project-goals)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Team Members](#team-members)
- [Acknowledgments](#acknowledgments)


## Overview

This project implements a reliable RTSP-based camera streaming pipeline using Go2RTC and integrates it with Home Assistant. It enables real-time, low-latency streaming from multiple IP cameras through a Docker-based deployment. 

## Project Goals

- Stream from multiple RTSP-compatible cameras  
- Deploy Go2RTC as a containerized streaming relay  
- Integrate streams with Home Assistant using WebRTC  
- Create a scalable, reproducible deployment using Docker Compose


## Features

- Multi-Camera Support  
- WebRTC Low-Latency Playback  
- Docker-Based Deployment  
- Real-Time Streaming  
- Dedicated Docker Network Isolation

  
## Architecture

![Streaming Pipeline Flowchart](Flowchart.png)


## Prerequisites 

- Docker (version 20.10 or higher) 
- Docker Compose (version 1.29 or higher) 
- RTSP-compatible IP cameras or RTSP camera apps 
- Network access to camera streams 


## Installation 
### Step 1: Clone the Repository 

[Home Assistant RTSP Server](https://github.com/Metropolia-Garage-Club/Home-Assistant-RTSP-Server)

cd Home-Assistant-RTSP-Server 


### Step 2: Directory Structure 

```text
C:\Home-Assistant-RTSP-Server\
└── software\
    └── deployment\
        └── camera-streaming\
            ├── docker-compose.yml
            ├── go2rtc\
            │   ├── Dockerfile
            │   └── config\
            │       └── go2rtc.yaml
            └── home-assistant\
                ├── Dockerfile
                └── config\
                    ├── configuration.yaml
                    ├── automations.yaml
                    ├── scripts.yaml
                    └── scenes.yaml
```


### Step 3: Deploy with Docker Compose 

docker-compose up 

This will: 

- Build the Go2RTC and Home Assistant Docker images 
- Start both containers 
- Create a dedicated Docker network for communication


### Step 4: Verify Deployment 

Check that both containers are running: 

docker ps 

You should see: 

- go2rtc container running on ports 1984, 8554, 8555 
- homeassistant container running on port 8123 


## Configuration 
### Go2RTC Configuration (go2rtc/config/go2rtc.yaml) 
[`go2rtc.yaml`](software/deployment/camera-streaming/go2rtc/config/go2rtc.yaml)

```text
streams: 
  iphone_cam: 
    - rtsp://camera_ip:8554/stream 
  mobile_cam_2: 
    - rtsp://camera_ip:8554/ 
  camera_3: 
    - rtsp://admin:aiot2024@192.168.50.50:554/h264Preview_01_main 
  raspberrypi_cam: 
    - rtsp://camera_ip:8554/rpi_camera 
    
webrtc: 
  listen: ":8555"   
api: 
  listen: ":1984"   
log: 
  level: debug
```


#### Configuration Notes: 

- Replace camera IP addresses with your actual camera IPs 
- For cameras requiring authentication, use the format: rtsp://username:password@ip:port/path 
- Stream names must match the names used in Home Assistant 


### Go2RTC Dockerfile (go2rtc/Dockerfile) 

```text
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
```


### Home Assistant Configuration (home-assistant/config/configuration.yaml) 

```text
# Loads default set of integrations 
default_config: 
 
# Enable Stream integration 
stream: 
 
# Automation 
automation: !include automations.yaml 
script: !include scripts.yaml 
scene: !include scenes.yaml 
 
# Logger 
logger: 
  default: info 
  logs: 
    homeassistant.core: info 
    homeassistant.components.camera: debug 
    homeassistant.components.stream: debug 
```


### Home Assistant Dockerfile (home-assistant/Dockerfile) 

```text
FROM ghcr.io/home-assistant/home-assistant:stable 
 
ENV TZ=Europe/Helsinki 
 
COPY ./config /config
```


### Docker Compose Configuration (docker-compose.yml) 

```text
services: 
  go2rtc: 
    build: 
      context: ./go2rtc 
      dockerfile: Dockerfile 
    container_name: go2rtc 
    ports: 
      - "1984:1984"   # API 
      - "8554:8554"   # RTSP 
      - "8555:8555"   # WebRTC 
    volumes: 
      - ./go2rtc/config/go2rtc.yaml:/config/go2rtc.yaml:ro 
    restart: unless-stopped 
    networks: 
      - streaming-network 
 
  homeassistant: 
    build: 
      context: ./home-assistant 
      dockerfile: Dockerfile 
    container_name: homeassistant 
    restart: unless-stopped 
    ports: 
      - "8123:8123" 
    volumes: 
      - ./home-assistant/config:/config 
    environment: 
      - TZ=Europe/Helsinki 
    networks: 
      - streaming-network 
    depends_on: 
      - go2rtc 
 
networks: 
  streaming-network: 
    driver: bridge 

```


## usage
### Accessing Go2RTC Web Interface 

1. Open your browser and navigate to:  
   [http://localhost:1984](http://localhost:1984)
2. You should see all configured camera streams listed 
3. Click on any stream to verify it's working


### Adding Cameras to Home Assistant
#### Step 1: Add WebRTC Camera Integration

1. Go to Settings → Devices & Services 
2. Click + Add Integration 
3. Search for WebRTC Camera 
4. Click on it to add the integration 
5. Configure with your host IP address (e.g., 192.168.50.141) 
6. Complete the setup process

#### Step 2: Add Camera Cards to Dashboard 

1. Go to your Home Assistant Dashboard 
2. Click Edit Dashboard → Add Card 
3. Select webrtc-camera Card 
3. Add the following configuration:
   
   type: custom:webrtc-camera
   
 	 url: iphone_cam  
5. Repeat for additional cameras:
   
   type: custom:webrtc-camera
   
  	url: Mobile_cam_2 

 
	  type: custom:webrtc-camera
   
	  url: Camera_3


  - Note: The url field should match the stream name defined in your go2rtc.yaml file.


### Viewing Camera Streams 

Once configured, you can: 

- View all camera streams on your Home Assistant dashboard 
- Access streams from mobile devices using the Home Assistant app 
- Create automations based on camera events


## Project Structure 

```text
Home-Assistant-RTSP-Server/ 
├── README.md 
├── docker-compose.yml 
├── go2rtc/ 
│   ├── Dockerfile 
│   └── config/ 
│       └── go2rtc.yaml 
└── home-assistant/ 
    ├── Dockerfile 
    └── config/ 
        ├── configuration.yaml 
        ├── automations.yaml 
        ├── scripts.yaml 
        └── scenes.yaml 
```


## Troubleshooting 
### Camera Stream Not Appearing in Go2RTC 

1. Verify camera IP address and RTSP URL 
2. Check network connectivity: 
   ping <camera-ip> 
3. Test RTSP stream with VLC or ffplay: 
   ffplay rtsp://<camera-ip>:<port>/<path> 
4. Check Go2RTC logs: 
   docker logs go2rtc 


### WebRTC Not Working in Home Assistant 

1. Verify WebRTC candidate IP matches your host IP 
2. Ensure port 8555 is accessible from your network 
3. Check Home Assistant logs: 
   docker logs homeassistant  
4. Verify the stream name in dashboard card matches go2rtc.yaml 


### Container Won't Start 

1. Check for port conflicts: 
   netstat -tulpn | grep -E '1984|8123|8554|8555' 
2. Verify Docker daemon is running: 
   docker ps 
3. Check container logs: 
   docker-compose logs 

#### Connection Refused Errors 

Ensure both containers are on the same Docker network: 

docker network inspect streaming-network 
  

1. Verify firewall rules allow connections on required ports 
2. Check if cameras are reachable from the Docker container: 
   docker exec -it go2rtc ping <camera-ip>



## Contributing 

Contributions are welcome! Please follow these steps: 

1. Fork the repository 
2. Create a feature branch (git checkout -b feature/amazing-feature) 
3. Commit changes (git commit -m 'Add some amazing feature') 
4. Push to the branch (git push origin feature/amazing-feature) 
5. Open a Pull Request 


## License 

This project is part of a Metropolia University of Applied Sciences internship project. 

## Team Members

- Upeksha
- Lihini
- Shamila

## Acknowledgments 

- Go2RTC - RTSP to WebRTC relay 
- Home Assistant - Home automation platform 
- Metropolia University of Applied Sciences - Project supervision 

 
