# Distributed Streaming System with ICE and Python

## Overview
This project implements a distributed streaming platform inspired by Netflix. It uses **ZeroC ICE** for remote procedure calls and synchronization between microservices. The architecture is built around microservices handling **authentication**, **media cataloging**, and **streaming**, with **IceStorm** as the event broker.

---

## Technical Architecture

### 1. Distributed Communication
- **Proxies**:
  - Services expose methods via ICE proxies, abstracting the implementation details and ensuring seamless invocation.
- **IceStorm**:
  - Manages event-based communication between services through topics like `ServiceAvailability` and `MediaAnnouncements`.

### 2. Security
- **Token-Based Authentication**:
  - SHA256-based credential hashing.
  - Temporary tokens expire in 30 seconds and are revoked via `AuthenticationStatus`.
- **Topic Access Control**:
  - Restricted publication and subscription to authorized services.

### 3. Load Balancing
- Services use **round-robin** selection for distributing requests to active instances.
- Fault tolerance ensures inactive proxies are removed dynamically.

### 4. Streaming Protocol
- **RTSP Streaming**:
  - Media is streamed via RTSP using **GStreamer**.
  - Clients authenticate and receive SDP files for video playback.

---

## Workflow

### 1. System Startup
1. **IceStorm** initializes as the event broker.
2. Microservices (Authentication, Catalog, Streaming, Main) are launched in parallel.
3. Each service:
   - Publishes availability in `ServiceAvailability`.
   - Listens for relevant events.

### 2. Microservice Behavior

#### Authentication
- Validates credentials and issues temporary tokens.
- Publishes token revocation events.

#### Catalog
- Indexes media announced by streaming services.
- Handles searches by ID, name, or tags.

#### Streaming
- Scans a directory, calculates SHA256 hashes, and announces available media.
- Streams videos upon client requests.

#### Main
- Serves as the system’s entry point.
- Provides active proxies for authentication and catalog services.

### 3. Client Interaction
1. Connects to the Main service.
2. Authenticates and receives a temporary token.
3. Searches for media and selects one for playback.
4. Requests streaming from the respective service.

---

## File Descriptions

### Configuration
- `authentication.conf`, `catalog.conf`, etc.:
  - Define ICE adapter settings and communication endpoints.

### Implementations
- `authentication.py`, `catalog.py`, `streaming.py`:
  - Contain microservice logic and event handling.
- `iceflixrtps.py`:
  - Manages RTSP video streaming with GStreamer.
- `iceFlixClient.py`:
  - Provides a CLI for system interaction.

---

## Execution

### Steps
1. Start IceStorm:
   ```bash
   make run-icestorm
./run_auth_server
./run_main
./run_catalog
./run_streaming <video_directory>
./iceFlixClient.py <main_proxy>


## Advanced Details

### 1. Protocols and Security
1. **Proxies and Remote Communication**:
   - Each microservice uses **ICE proxies** to abstract the implementation and provide seamless interaction.
   - Clients and services interact with any available instance without knowledge of its physical location.

2. **Publication and Subscription with IceStorm**:
   - **Defined Topics**:
     - `ServiceAvailability`: Publishes events about new services or disconnected servers.
     - `MediaAnnouncements`: Notifies catalog services of new media.
     - `AuthenticationStatus`: Announces revoked tokens.
   - **Dynamic Subscription**:
     - Services dynamically subscribe and react to real-time events.
     - Example: When a streaming service announces a new media, the catalog indexes it immediately.

3. **Security Management**:
   - Servers validate every token received before processing sensitive requests.
   - Temporary token issuance and automatic expiration prevent unauthorized prolonged access.

### 2. Load Balancing and Fault Tolerance
1. **Load Distribution**:
   - Clients interact with available servers selected randomly or sequentially (`round-robin`).
   - Ensures equitable distribution of requests across instances.

2. **Service Monitoring**:
   - Each service monitors others through `ServiceAvailability` events.
   - Disconnected or failed services are dynamically removed from candidate lists.

### 3. Streaming Implementation
1. **RTSP Protocol**:
   - Each streaming server exposes media using **RTSP**, leveraging **GStreamer** for video transmission.
   - Stream configuration (SDP) is dynamically generated based on the media file and client address.

2. **Stream Controller Management**:
   - **StreamController**:
     - Associated with a specific video stream.
     - Manages playback and allows stopping the stream.
   - **Dynamic Authentication**:
     - Periodically validates tokens and requests renewal if the token expires.

---
