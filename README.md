# reconPoint

<!-- Banner -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Django-5.2-green.svg" alt="Django">
  <img src="https://img.shields.io/badge/PostgreSQL-17-orange.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Secator-v0.26-red.svg" alt="Secator">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

```
 ::::::::::::::: reconPoint automation script :::::::::::::: 
                       ______                                
                    .-        -.                             
                   /       *    \             by @KhulnaSoft
                  |,  .-.  .-.  ,|        *                  
         *        | )(_ /  \_ )( |                           
                  |/     /\     \|    *                      
        (@_       <__    ^^    __>         *                 
         ) \_______\__|IIIIII|__/__________________________
 ::::(_)@8@8{}<____________________________________________>
         )_/         \ IIIIII /                    :::::     
        (@            --------                        ::     

  ________________[ reconPoint - End-Point Security Scanner]
 :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

<p align="center">
  <strong>Automated Security Reconnaissance Platform</strong><br>
  by <a href="https://github.com/khulnasoft">@KhulnaSoft</a>
</p>

---

## 🔥 Features

### Reconnaissance Engine
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RECONNAISSANCE WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Subdomain│    │   Port   │    │   HTTP   │    │Vulnerability│            │
│  │Discovery │───▶│ Scanning │───▶│ Crawling │───▶│  Scanning  │            │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │              │              │                   │                     │
│       ▼              ▼              ▼                   ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │   DNS    │    │   Nmap   │    │ Screenshots│    │  Nuclei  │              │
│  │ Enumerat.│    │  & Naabu │    │ & Katana │    │ & Custom │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Feature | Description |
|---------|-------------|
| 🌐 **Subdomain Discovery** | Amass, SubFinder, assetfinder integration |
| 🔌 **Port Scanning** | Naabu, Nmap with custom profiles |
| 🌐 **HTTP Probing** | httpx, naabu for service detection |
| 📸 **Screenshot Capture** | EyeWitness,gowitness automation |
| 🔍 **Vulnerability Scanning** | Nuclei templates, custom workflows |
| 📁 **Directory Fuzzing** | ffuf, dirsearch, feroxbuster |
| ☁️ **Cloud Enumeration** | S3, Azure, GCP asset discovery |
| 📧 **OSINT Gathering** | Email, employee, metadata discovery |

### Advanced Capabilities
```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        ADVANCED FEATURES MATRIX                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   🔄 Real-Time     │  🤖 AI-Powered     │  🔗 Attack Chain    │  🛡️ Threat     │
│   WebSocket       │  LLM Analysis      │  Correlation        │  Intelligence  │
│   Streaming       │  & Remediation     │  Detection          │  Integration   │
│                   │                    │                      │                │
├───────────────────┼────────────────────┼──────────────────────┼────────────────┤
│   📊 Custom       │  🎫 Ticketing      │  📈 Comparison      │  🔌 Plugin      │
│   Dashboards      │  Integration       │  Scans & Trends      │  Marketplace   │
│   & Widgets       │  (Jira, GitHub)    │  & Change Tracking   │  & Extensions  │
│                   │                    │                      │                │
├───────────────────┼────────────────────┼──────────────────────┼────────────────┤
│   👥 Multi-Team   │  📋 SLA Policies   │  💻 PoC Generation   │  ⏱️  MTTD/MTTR  │
│   Workspaces      │  & Breach Alerting  │  & Execution        │  Metrics       │
│                   │                    │                      │                │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   NGINX     │
                              │   Proxy     │
                              └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │   Web     │    │  Worker   │    │  Ollama  │
              │ (Django)  │    │ (Secator) │    │   LLM    │
              └─────┬─────┘    └─────┬─────┘    └──────────┘
                    │                │
        ┌───────────┼────────────────┘
        │           │
        ▼           ▼
  ┌──────────┐ ┌──────────┐
  │PostgreSQL│ │  Redis   │
  │Database  │ │  Cache   │
  └──────────┘ └──────────┘
```

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Web Framework** | Django + DRF | 5.2 / 3.16 |
| **Database** | PostgreSQL | 17 |
| **Cache/Broker** | Redis | 7.4 |
| **Task Automation** | Secator | 0.26 |
| **Real-Time** | Django Channels | 4.3 |
| **LLM Integration** | LangChain + Ollama | Latest |
| **Container** | Docker Compose | Latest |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM
- 20GB+ Storage

### Installation

```bash
# Clone the repository
git clone https://github.com/khulnasoft/reconpoint.git
cd reconpoint

# Start all services
make build_up

# Access the application
open http://localhost
```

### Development Setup

```bash
# Install dependencies
poetry install

# Run migrations
poetry run python manage.py migrate

# Start development server
poetry run python manage.py runserver
```

## 📁 Project Structure

```
reconpoint/
├── web/                          # Django application
│   ├── api/                      # REST API endpoints
│   ├── dashboard/               # Dashboard & workspaces
│   ├── scanEngine/             # Scan engine & workflows
│   ├── startScan/              # Scan execution
│   ├── targetApp/              # Target management
│   ├── recon_note/            # Notes module
│   └── reconPoint/           # Core configuration
├── docker/                     # Docker configuration
├── config/                    # Scan profiles & workflows
└── scripts/                  # Utility scripts
```

## 🔌 Supported Tools

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           SECATOR INTEGRATION                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Subdomain   │  Port      │  Web       │  Vuln      │  OSINT    │  Secrets   │
│  ─────────   │  ──────    │  ────      │  ────      │  ─────    │  ───────   │
│  • subfinder │  • naabu   │  • httpx   │  • nuclei  │  • maigret│  • gitleaks│
│  • amass     │  • nmap    │  • katana  │  • grype   │  • hunter │  • trufflehog
│  • assetfind │  • masscan │  • gospider│  • trivy   │  • holehe │  • secretz  │
│  • findomain │            │  • feroxb  │            │  • email  │            │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  More tools: bbot, cariddi, dalfox, ffuf, gf, wafw00f, wpscan, xurlfind3r... │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 🌐 API Endpoints

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              REST API V2                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Targets                      Scans                    Workflows            │
│  ───────                      ─────                    ─────────            │
│  GET  /api/targets/           POST /api/startScan/     GET  /api/workflows/ │
│  POST /api/add/target         GET  /api/listScan/      POST /api/workflows/ │
│  GET  /api/target/{id}        DELETE /api/stopScan/    GET  /api/runners/    │
│                                                                              │
│  Findings                     Workers                  Customization         │
│  ────────                     ───────                   ─────────────         │
│  GET  /api/findings/          GET  /api/workers/       GET  /api/profiles/  │
│  GET  /api/vulns/             POST /api/workers/add/   GET  /api/tasks/     │
│  GET  /api/secrets/           PUT  /api/workers/{id}   GET  /api/configs/   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 📊 Dashboard Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DASHBOARD WIDGETS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  Subdomain  │ │  Endpoints  │ │Vulnerabilities│ │    Risks    │            │
│  │    Count    │ │    Count    │ │    Count    │ │    Score    │            │
│  │     1,234   │ │     5,678   │ │      89     │ │     75/100  │            │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │                    Severity Distribution                         │         │
│  │   ████████████████████████░░░░░░░░ Critical: 12                 │         │
│  │   ██████████████████████████████████████ High: 45               │         │
│  │   ████████████████████░░░░░░░░░░░░░░░░ Medium: 28               │         │
│  │   ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░ Low: 4                   │         │
│  └─────────────────────────────────────────────────────────────────┘         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │                    Security Posture Trend                        │         │
│  │  100%│    ╭─╮                                                    │         │
│  │   75%│───╯   ╰──╮                                                │         │
│  │   50%│            ╰─────╮                                        │         │
│  │    0%│                  ╰──╮                                      │         │
│  │      └─────────────────────────▶ Timeline                        │         │
│  └─────────────────────────────────────────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔒 Security Features

| Category | Features |
|----------|----------|
| **Threat Intel** | ABUSE.ch, Shodan, AlienVault OTX, VirusTotal integration |
| **Attack Chains** | Vulnerability correlation & attack path analysis |
| **SLA Tracking** | Severity-based remediation deadlines & breach alerts |
| **Compliance** | ISO 27001, SOC 2, PCI-DSS mapping |
| **Metrics** | MTTD, MTTR, closure rates, security posture scores |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Secator](https://github.com/KhulnaSoft/secator) - Security automation framework
- All the amazing open-source tools integrated into reconPoint
- The security community for continuous support

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/khulnasoft">@KhulnaSoft</a>
</p>