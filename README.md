<a id="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<br />
<div align="center">
  <a href="https://github.com/alonsojj/Yggdrasil">
    <img src="https://github.com/alonsojj/Yggdrasil/blob/main/app/static/logo.png?raw=true" alt="drawing" width="200"/>
  </a>

<h3 align="center">Yggdrasil</h3>

  <p align="center">
    Yggdrasil is a self-hosted server for Stremio. It acts as an engine to execute and serve local scraper scripts, allowing you to build and host your own video sources privately.
    <br />
    <a href="https://github.com/alonsojj/Yggdrasil"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/alonsojj/Yggdrasil/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/alonsojj/Yggdrasil/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
        <a href="#configuration">Configuration</a>
        <ul>
            <li><a href="#https-certificates">HTTPS & Certificates</a></li>
        </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#environment-variables">Environment Variables</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#top-contributors">Top Contributors</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

## About The Project

**Yggdrasil** serves as a bridge between your custom Python scrapers and Stremio. Instead of relying on public addons, Yggdrasil runs locally (or on your server), loads your Python scripts from the `addons/` directory, and serves them as a standard Stremio addon manifest.


<p align="right">(<a href="#readme-top">back to top</a>) </p>

### Built With

* [![FastAPI][FastAPI-badge]][FastAPI-url]
* [![Python][Python-badge]][Python-url]
* [![Docker][Docker-badge]][Docker-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Roadmap

- [x] **Core Engine**: Load local addons and serve Stremio manifest.
- [x] **Docker Support**: Easy deployment via Docker.
- [ ] **Advanced Proxy Support**: Add option to configure external proxies per addon or globally via UI.
- [ ] **Addon Management System**:
    - [ ] Install addons via Git URL (cloning directly into `addons/`).
    - [ ] Manage installed addons (enable/disable/update).
    - [ ] Support for scrapers on external plataforms such as Apify
- [ ] **User Interface**: A web dashboard to view logs and manage settings.

See the [open issues](https://github.com/alonsojj/Yggdrasil/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

You can run Yggdrasil using **Docker** (recommended for most users) or **Locally** for development.

### Prerequisites

* **Docker Path:** Only [Docker](https://docs.docker.com/engine/install/) is required. (No need for Python or UV).
* **Local Path:** [UV](https://docs.astral.sh/uv/getting-started/installation/) - Fast Python package manager.

---

### Option 1: Docker

#### 1. Create a configuration file
Create a `.env` file in your project folder:
```env
PORT=8000
SECRET_KEY=your_super_secret_key_here
TMDB_KEY=your_tmdb_api_key_here
ENABLE_HTTPS=False
```

#### 2. Run the Container

**Using Docker Run**
```bash
docker run -d \
  --name yggdrasil \
  -p 8000:8000 \
  --env-file .env \
  alonsojj/yggdrasil:latest
```

**Using Docker Compose**
Download the `docker-compose.yaml` or create one:
```yaml
services:
  yggdrasil:
    image: alonsojj/yggdrasil:latest
    container_name: yggdrasil
    restart: unless-stopped
    env_file: .env
    ports:
      - "${PORT:-8000}:8000"
    # Uncomment if using self-signed certificates
    # volumes:
      # - ./certs:/app/certs
```
Then run:
```bash
docker-compose up -d
```

> **⚠️ Note on HTTPS & Self-Signed Certificates:**
> If you set `ENABLE_HTTPS=True`, you **must** share your certificates with the container by adding a volume:
> *   **Docker Run:** Add `-v $(pwd)/certs:/app/certs`
> *   **Docker Compose:** Add `- ./certs:/app/certs` under `volumes`.

---

### Option 2: Local Installation (Manual)

Use this method if you want to develop or run without Docker.

1. **Clone the repository**
   ```bash
   git clone https://github.com/alonsojj/Yggdrasil.git
   cd Yggdrasil
   ```

2. **Setup with UV**
   ```bash
   uv venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   uv sync
   ```

3. **Configure & Run**
   ```bash
   cp .env.example .env
   # Edit .env with your keys
   uv run -m app.main
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Configuration

### HTTPS & Certificates

**⚠️ Important:** Stremio typically **requires** addons to be served over **HTTPS**. The only common exception is running strictly on `localhost` (127.0.0.1) for local desktop clients.

To enable HTTPS, you have two main options:

1.  **Reverse Proxy (Recommended):**
    Keep `ENABLE_HTTPS=False` and run Yggdrasil behind a reverse proxy like **Nginx**, **Traefik**, or **Caddy** (or a cloud provider like Render/Heroku) that handles the SSL termination. This is the easiest and most robust method.

2.  **Native HTTPS:**
    If you want Yggdrasil to handle SSL directly:
    *   Set `ENABLE_HTTPS=True` in your `.env`.
    *   **You must provide signed certificates.**
    *   Place your certificate files in the `certs/` folder:
        *   `certs/cert.pem` (The Certificate)
        *   `certs/key.pem` (The Private Key)
    
    *If using Self-Signed certificates, be aware that Stremio clients (especially Web and TV) may reject the connection due to security policies.*

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

Once the server is running (default port 8000), you can access the Stremio Manifest URL.

1. Open your browser and go to `http://localhost:8000/docs` to see the API endpoints.
2. The main manifest for Stremio is typically available at:
   ```
   http://localhost:8000/manifest.json
   ```
3. Add this URL to your Stremio search bar or addon configuration to install.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Project Structure

```
Yggdrasil/
├── addons/                  # Scraper modules folder
│   └── fembed/              # Example Fembed scraper
├── app/
│   ├── core/                # Core configuration & engines
│   ├── routers/             # API Endpoints (Manifest, Streams)
│   ├── schemas/             # Pydantic Models
│   ├── services/            # Business Logic (Addon Engine)
│   ├── utils/               # Helpers (HLS, Network)
│   ├── dependencies.py
│   └── main.py              # Application Entry Point
├── certs/                   # SSL Certificates (required if ENABLE_HTTPS=True)
├── images/                  # Project assets
├── .env.example             # Config template
├── docker-compose.yaml      # Docker setup
├── Dockerfile
├── pyproject.toml           # Dependencies (UV)
└── README.md
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Security key for the app | ✅ | - |
| `TMDB_KEY` | API Key for TMDB (metadata) | ✅ | - |
| `PORT` | Application port | ❌ | `8000` |
| `ENABLE_HTTPS` | Enable SSL support (Requires certs in `certs/`) | ❌ | `False` |
| `PROXY_URL` | Global proxy URL for requests | ❌ | `None` |
| `ADDON_PATH` | Custom path for addons | ❌ | `None` |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Top Contributors

<a href="https://github.com/alonsojj/Yggdrasil/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=alonsojj/Yggdrasil" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Acknowledgments

This project was inspired by the features and logic of other amazing projects in the Stremio community. Special thanks to the developers for paving the way:

* [http-stremio](https://github.com/Huuuuuugo/http-stremio)
* [NuvioStreaming](https://github.com/tapframe/NuvioStreaming)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

Project Link: [https://github.com/alonsojj/Yggdrasil](https://github.com/alonsojj/Yggdrasil)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/alonsojj/Yggdrasil.svg?style=for-the-badge
[contributors-url]: https://github.com/alonsojj/Yggdrasil/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/alonsojj/Yggdrasil.svg?style=for-the-badge
[forks-url]: https://github.com/alonsojj/Yggdrasil/network/members
[stars-shield]: https://img.shields.io/github/stars/alonsojj/Yggdrasil.svg?style=for-the-badge
[stars-url]: https://github.com/alonsojj/Yggdrasil/stargazers
[issues-shield]: https://img.shields.io/github/issues/alonsojj/Yggdrasil.svg?style=for-the-badge
[issues-url]: https://github.com/alonsojj/Yggdrasil/issues
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/your_linkedin

[FastAPI-badge]: https://img.shields.io/badge/FastAPI-009485.svg?logo=fastapi&logoColor=white&style=for-the-badge
[FastAPI-url]: https://fastapi.tiangolo.com/
[Python-badge]: https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white&style=for-the-badge
[Python-url]: https://www.python.org/
[Docker-badge]: https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white&style=for-the-badge
[Docker-url]: https://www.docker.com/

