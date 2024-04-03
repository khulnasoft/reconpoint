### Features
<p align="center">
  <a href="https://www.youtube.com/watch?v=Xk_YH83IQgg" target="_blank"><img src="https://img.shields.io/badge/BlackHat--Arsenal--Asia-2023-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://www.youtube.com/watch?v=Xk_YH83IQgg" target="_blank"><img src="https://img.shields.io/badge/BlackHat--Arsenal--USA-2022-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://www.youtube.com/watch?v=Xk_YH83IQgg" target="_blank"><img src="https://img.shields.io/badge/Open--Source--Summit-2022-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://cyberweek.ae/2021/hitb-armory/" target="_blank"><img src="https://img.shields.io/badge/HITB--Armory-2021-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://www.youtube.com/watch?v=7uvP6MaQOX0" target="_blank"><img src="https://img.shields.io/badge/BlackHat--Arsenal--USA-2021-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://drive.google.com/file/d/1Bh8lbf-Dztt5ViHJVACyrXMiglyICPQ2/view?usp=sharing" target="_blank"><img src="https://img.shields.io/badge/Defcon--Demolabs--29-2021-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://www.youtube.com/watch?v=A1oNOIc0h5A" target="_blank"><img src="https://img.shields.io/badge/BlackHat--Arsenal--Europe-2020-blue.svg?&logo=none" alt="" /></a>&nbsp;
</p>

<p align="center">
<a href="https://github.com/khulnasoft/reconpoint/actions/workflows/codeql-analysis.yml" target="_blank"><img src="https://github.com/khulnasoft/reconpoint/actions/workflows/codeql-analysis.yml/badge.svg" alt="" /></a>&nbsp;<a href="https://github.com/khulnasoft/reconpoint/actions/workflows/build.yml" target="_blank"><img src="https://github.com/khulnasoft/reconpoint/actions/workflows/build.yml/badge.svg" alt="" /></a>&nbsp;
</p>

<p align="center">
<a href="https://discord.gg/H6WzebwX3H" target="_blank"><img src="https://img.shields.io/discord/880363103689277461" alt="" /></a>&nbsp;
</p>

<p align="center">
<a href="https://opensourcesecurityindex.io/" target="_blank" rel="noopener">
<img style="width: 282px; height: 56px" src="https://opensourcesecurityindex.io/badge.svg" alt="Open Source Security Index - Fastest Growing Open Source Security Projects" width="282" height="56" /> </a>
</p>
* Reconnaissance:
  * Subdomain Discovery
  * IP and Open Ports Identification
  * Endpoints Discovery
  * Directory/Files fuzzing
  * Screenshot Gathering
  * Vulnerability Scan
    * Nuclei
    * Dalfox XSS Scanner
    * CRLFuzzer
    * Misconfigured S3 Scanner
  * WHOIS Identification
  * WAF Detection
* OSINT Capabilities
  * Meta info Gathering
  * Employees Gathering
  * Email Address gathering
  * Google Dorking for sensitive info and urls
* Projects, create distinct project spaces, each tailored to a specific purpose, such as personal bug bounty hunting, client engagements, or any other specialized recon task.
* Perform Advanced Query lookup using natural language alike and, or, not operations
* Highly configurable YAML-based Scan Engines
* Support for Parallel Scans
* Support for Subscans
* Recon Data visualization
* GPT Vulnerability Description, Impact and Remediation generation
* GPT Attack Surface Generator
* Multiple Roles and Permissions to cater a team's need
* Customizable Alerts/Notifications on Slack, Discord, and Telegram
* Automatically report Vulnerabilities to HackerOne
* Recon Notes and Todos
* Clocked Scans (Run reconnaissance exactly at X Hours and Y minutes) and Periodic Scans (Runs reconnaissance every X minutes/- hours/days/week)
* Proxy Support
* Screenshot Gallery with Filters
* Powerful recon data filtering with autosuggestions
* Recon Data changes, find new/removed subdomains/endpoints
* Tag targets into the Organization
* Smart Duplicate endpoint removal based on page title and content length to cleanup the reconnaissance data
* Identify Interesting Subdomains
* Custom GF patterns and custom Nuclei Templates
* Edit tool-related configuration files (Nuclei, Subfinder, Naabu, amass)
* Add external tools from Github/Go
* Interoperable with other tools, Import/Export Subdomains/Endpoints
* Import Targets via IP and/or CIDRs
* Report Generation
* Toolbox: Comes bundled with most commonly used tools during penetration testing such as whois lookup, CMS detector, CVE lookup, etc.
* Identification of related domains and related TLDs for targets
* Find actionable insights such as Most Common Vulnerability, Most Common CVE ID, Most Vulnerable Target/Subdomain, etc.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

### Scan Engine

```yaml
subdomain_discovery: {
  'uses_tools': [
    'subfinder',
    'ctfr',
    'sublist3r',
    'tlsx',
    'oneforall',
    'netlas'
  ],
  'enable_http_crawl': true,
  'threads': 30,
  'timeout': 5,
}
http_crawl: {}
port_scan: {
  'enable_http_crawl': true,
  'timeout': 5,
  # 'exclude_ports': [],
  # 'exclude_subdomains': true,
  'ports': ['top-100'],
  'rate_limit': 150,
  'threads': 30,
  'passive': false,
  # 'use_naabu_config': false,
  # 'enable_nmap': true,
  # 'nmap_cmd': '',
  # 'nmap_script': '',
  # 'nmap_script_args': ''
}
osint: {
  'discover': [
      'emails',
      'metainfo',
      'employees'
    ],
  'dorks': [
    'login_pages',
    'admin_panels',
    'dashboard_pages',
    'stackoverflow',
    'social_media',
    'project_management',
    'code_sharing',
    'config_files',
    'jenkins',
    'wordpress_files',
    'php_error',
    'exposed_documents',
    'db_files',
    'git_exposed'
  ],
  'custom_dorks': [
    {
      'lookup_site': 'google.com',
      'lookup_keywords': '/home/'
    },
    {
      'lookup_site': '_target_',
      'lookup_extensions': 'jpg,png'
    }
  ],
  'intensity': 'normal',
  'documents_limit': 50
}
dir_file_fuzz: {
  'auto_calibration': true,
  'enable_http_crawl': true,
  'rate_limit': 150,
  'extensions': ['html', 'php','git','yaml','conf','cnf','config','gz','env','log','db','mysql','bak','asp','aspx','txt','conf','sql','json','yml','pdf'],
  'follow_redirect': false,
  'max_time': 0,
  'match_http_status': [200, 204],
  'recursive_level': 2,
  'stop_on_error': false,
  'timeout': 5,
  'threads': 30,
  'wordlist_name': 'dicc'
}
fetch_url: {
  'uses_tools': [
    'gospider',
    'hakrawler',
    'waybackurls',
    'gospider',
    'katana'
  ],
  'remove_duplicate_endpoints': true,
  'duplicate_fields': [
    'content_length',
    'page_title'
  ],
  'enable_http_crawl': true,
  'gf_patterns': ['debug_logic', 'idor', 'interestingEXT', 'interestingparams', 'interestingsubs', 'lfi', 'rce', 'redirect', 'sqli', 'ssrf', 'ssti', 'xss'],
  'ignore_file_extensions': ['png', 'jpg', 'jpeg', 'gif', 'mp4', 'mpeg', 'mp3']
  # 'exclude_subdomains': true
}
vulnerability_scan: {
  'run_nuclei': false,
  'run_dalfox': false,
  'run_crlfuzz': false,
  'run_s3scanner': true,
  'enable_http_crawl': true,
  'concurrency': 50,
  'intensity': 'normal',
  'rate_limit': 150,
  'retries': 1,
  'timeout': 5,
  'fetch_gpt_report': true,
  'nuclei': {
    'use_nuclei_config': false,
    'severities': [
      'unknown',
      'info',
      'low',
      'medium',
      'high',
      'critical'
    ],
    # 'tags': [],
    # 'templates': [],
    # 'custom_templates': [],
  },
  's3scanner': {
    'threads': 100,
    'providers': [
      'aws',
      'gcp',
      'digitalocean',
      'dreamhost',
      'linode'
    ]
  }
}
waf_detection: {}
screenshot: {
  'enable_http_crawl': true,
  'intensity': 'normal',
  'timeout': 10,
  'threads': 40
}

# custom_header: "Cookie: Test"
```

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

### Quick Installation

**Note:** Only Ubuntu/VPS

1. Clone this repo

    ```bash
    git clone https://github.com/khulnasoft/reconpoint && cd reconpoint
    ```

1. Edit the dotenv file, **please make sure to change the password for postgresql `POSTGRES_PASSWORD`!**

    ```bash
    nano .env
    ```

1. In the dotenv file, you may also modify the Scaling Configurations

    ```bash
    MAX_CONCURRENCY=80
    MIN_CONCURRENCY=10
    ```

    MAX_CONCURRENCY: This parameter specifies the maximum number of reconPoint's concurrent Celery worker processes that can be spawned. In this case, it's set to 80, meaning that the application can utilize up to 80 concurrent worker processes to execute tasks concurrently. This is useful for handling a high volume of scans or when you want to scale up processing power during periods of high demand. If you have more CPU cores, you will need to increase this for maximised performance.

    MIN_CONCURRENCY: On the other hand, MIN_CONCURRENCY specifies the minimum number of concurrent worker processes that should be maintained, even during periods of lower demand. In this example, it's set to 10, which means that even when there are fewer tasks to process, at least 10 worker processes will be kept running. This helps ensure that the application can respond promptly to incoming tasks without the overhead of repeatedly starting and stopping worker processes.

    These settings allow for dynamic scaling of Celery workers, ensuring that the application efficiently manages its workload by adjusting the number of concurrent workers based on the workload's size and complexity

1. Run the installation script, Please keep an eye for any prompt, you will also be asked for username and password for reconPoint.

    ```bash
    sudo ./install.sh
    ```

    If `install.sh` does not have install permission, please change it, `chmod +x install.sh`

**reconPoint can now be accessed from <https://127.0.0.1> or if you're on the VPS <https://your_vps_ip_address>**

**Unless you are on development branch, please do not access reconPoint via any ports**
