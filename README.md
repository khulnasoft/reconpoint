# Recon Point

<p align=""><a href="https://github.com/khulnasoft/reconpoint/releases" target="_blank"><img src="https://img.shields.io/badge/version-v2.0.0-informational?&logo=none" alt="reconPoint Latest Version" /></a>&nbsp;<a href="https://www.gnu.org/licenses/gpl-3.0" target="_blank"><img src="https://img.shields.io/badge/License-GPLv3-red.svg?&logo=none" alt="License" /></a>&nbsp;<a href="#" target="_blank"><img src="https://img.shields.io/badge/first--timers--only-friendly-blue.svg?&logo=none" alt="" /></a>&nbsp;<a href="https://huntr.dev/bounties/disclose/?target=https%3A%2F%2Fgithub.com%2Fkhulnasoft%2Freconpoint" target="_blank"><img src="https://cdn.huntr.dev/huntr_security_badge_mono.svg" alt="" /></a>&nbsp;</p>

<p align="">
  <a href="https://www.youtube.com/watch?v=Xk_YH83IQgg" target="_blank"><img src="https://img.shields.io/badge/BlackHat--Arsenal--Asia-2023-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://www.youtube.com/watch?v=Xk_YH83IQgg" target="_blank"><img src="https://img.shields.io/badge/BlackHat--Arsenal--USA-2022-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://www.youtube.com/watch?v=Xk_YH83IQgg" target="_blank"><img src="https://img.shields.io/badge/Open--Source--Summit-2022-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://cyberweek.ae/2021/hitb-armory/" target="_blank"><img src="https://img.shields.io/badge/HITB--Armory-2021-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://www.youtube.com/watch?v=7uvP6MaQOX0" target="_blank"><img src="https://img.shields.io/badge/BlackHat--Arsenal--USA-2021-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://drive.google.com/file/d/1Bh8lbf-Dztt5ViHJVACyrXMiglyICPQ2/view?usp=sharing" target="_blank"><img src="https://img.shields.io/badge/Defcon--Demolabs--29-2021-blue.svg?logo=none" alt="" /></a>&nbsp;
  <a href="https://www.youtube.com/watch?v=A1oNOIc0h5A" target="_blank"><img src="https://img.shields.io/badge/BlackHat--Arsenal--Europe-2020-blue.svg?&logo=none" alt="" /></a>&nbsp;
</p>

<p align="">
<a href="https://github.com/khulnasoft/reconpoint/actions/workflows/codeql-analysis.yml" target="_blank"><img src="https://github.com/khulnasoft/reconpoint/actions/workflows/codeql-analysis.yml/badge.svg" alt="" /></a>&nbsp;<a href="https://github.com/khulnasoft/reconpoint/actions/workflows/build.yml" target="_blank"><img src="https://github.com/khulnasoft/reconpoint/actions/workflows/build.yml/badge.svg" alt="" /></a>&nbsp;
</p>

<h3>reconPoint 2.0-jasper<br>Redefining the future of reconnaissance!</h3>

<h4>What is reconPoint?</h4>
<p align="left">reconPoint is your go-to web application reconnaissance suite that's designed to simplify and streamline the reconnaissance process for security professionals, penetration testers, and bug bounty hunters. With its highly configurable engines, data correlation capabilities, continuous monitoring, database-backed reconnaissance data, and an intuitive user interface, reconPoint redefines how you gather critical information about your target web applications.

Traditional reconnaissance tools often fall short in terms of configurability and efficiency. reconPoint addresses these shortcomings and emerges as a excellent alternative to existing commercial tools.

reconPoint was created to address the limitations of traditional reconnaissance tools and provide a better alternative, even surpassing some commercial offerings. Whether you're a bug bounty hunter, a penetration tester, or a corporate security team, reconPoint is your go-to solution for automating and enhancing your information-gathering efforts.
</p>

reconPoint 2.0-jasper is out now, you can [watch reconPoint 2.0-jasper release trailer here!](https://youtu.be/VwkOWqiWW5g)

reconPoint 2.0-Jasper would not have been possible without [@ocervell](https://github.com/ocervell) valuable contributions. [@ocervell](https://github.com/ocervell) did majority of the refactoring if not all and also added a ton of features. Together, we wish to shape the future of web application reconnaissance, and it's developers like [@ocervell](https://github.com/ocervell) and a [ton of other developers and hackers from our community](https://github.com/khulnasoft/reconpoint/graphs/contributors) who inspire and drive us forward.

Thank you, [@ocervell](https://github.com/ocervell), for your outstanding work and unwavering commitment to reconPoint.

Checkout our contributers here: [Contributers](https://github.com/khulnasoft/reconpoint/graphs/contributors)

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

### Documentation

You can find detailed documentation at [https://recon.khulnasoft.com](https://recon.khulnasoft.com)

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

### Table of Contents

* [About reconPoint](#about-reconpoint)
* [Workflow](#workflow)
* [Features](#features)
* [Scan Engine](#scan-engine)
* [Quick Installation](#quick-installation)
* [What's new in reconPoint 2.0](#changelog)
* [Screenshots](#screenshots)
* [Contributing](#contributing)
* [reconPoint Support](#reconpoint-support)
* [Support and Sponsoring](#support-and-sponsoring)
* [reconPoint Bug Bounty Program](#reconpoint-bug-bounty-program)
* [License](#license)

### About reconPoint

reconPoint is not an ordinary reconnaissance suite; it's a game-changer! We've turbocharged the traditional workflow with groundbreaking features that is sure to ease your reconnaissance game. reconPoint redefines the art of reconnaissance with highly configurable scan engines, recon data correlation, continuous monitoring, GPT powered Vulnerability Report, Project Management and role based access control etc.


🦾&nbsp;&nbsp; reconPoint has advanced reconnaissance capabilities, harnessing a range of open-source tools to deliver a comprehensive web application reconnaissance experience. With it's intuitive User Interface, it excels in subdomain discovery, pinpointing IP addresses and open ports, collecting endpoints, conducting directory and file fuzzing, capturing screenshots, and performing vulnerability scans. To summarize, it does end-to-end reconnaissance. With WHOIS identification and WAF detection, it offers deep insights into target domains. Additionally, reconPoint also identifies misconfigured S3 buckets and find interesting subdomains and URLS, based on specific keywords to helps you identify your next target, making it an go to tool for efficient reconnaissance.

🗃️&nbsp; &nbsp; Say goodbye to recon data chaos! reconPoint seamlessly integrates with a database, providing you with unmatched data correlation and organization. Forgot the hassle of grepping through json, txt or csv files. Plus, our custom query language lets you filter reconnaissance data effortlessly using natural language like operators such as filtering all alive subdomains with `http_status=200` and also filter all subdomains that are alive and has admin in name `http_status=200&name=admin`

🔧&nbsp;&nbsp; reconPoint offers unparalleled flexibility through its highly configurable scan engines, based on a YAML-based configuration. It offers the freedom to create and customize recon scan engines based on any kind of requirement, users can tailor them to their specific objectives and preferences, from thread management to timeout settings and rate-limit configurations, everything is customizable. Additionally, reconPoint offers a range of pre-configured scan engines right out of the box, including Full Scan, Passive Scan, Screenshot Gathering, and the OSINT Scan Engine. These ready-to-use engines eliminate the need for extensive manual setup, aligning perfectly with reconPoint's core mission of simplifying the reconnaissance process and enabling users to effortlessly access the right reconnaissance data with minimal effort.

💎&nbsp;&nbsp;Subscans: Subscan is a game-changing feature in reconPoint, setting it apart as the only open-source tool of its kind to offer this capability. With Subscan, waiting for the entire pipeline to complete is a thing of the past. Now, users can swiftly respond to newfound discoveries during reconnaissance. Whether you've stumbled upon an intriguing subdomain and wish to conduct a focused port scan or want to delve deeper with a vulnerability assessment, reconPoint has you covered.

📃&nbsp;&nbsp; PDF Reports: In addition to its robust reconnaissance capabilities, reconPoint goes the extra mile by simplifying the report generation process, recognizing the crucial role that PDF reports play in the realm of end-to-end reconnaissance. Users can effortlessly generate and customize PDF reports to suit their exact needs. Whether it's a Full Scan Report, Vulnerability Report, or a concise reconnaissance report, reconPoint provides the flexibility to choose the report type that best communicates your findings. Moreover, the level of customization is unparalleled, allowing users to select report colors, fine-tune executive summaries, and even add personalized touches like company names and footers. With GPT integration, your reports aren't just a report, with remediation steps, and impacts, you get 360-degree view of the vulnerabilities you've uncovered.

🔖&nbsp; &nbsp; Say Hello to Projects! reconPoint 2.0 introduces a powerful addition that enables you to efficiently organize your web application reconnaissance efforts. With this feature, you can create distinct project spaces, each tailored to a specific purpose, such as personal bug bounty hunting, client engagements, or any other specialized recon task. Each projects will have separate dashboard and all the scan results will be separated from each projects, while scan engines and configuration will be shared across all the projects.

⚙️&nbsp; &nbsp; Roles and Permissions! Begining reconPoint 2.0, we've taken your web application reconnaissance to a whole new level of control and security. Now, you can assign distinct roles to your team members—Sys Admin, Penetration Tester, and Auditor—each with precisely defined permissions to tailor their access and actions within the reconPoint ecosystem.

  - 🔐 Sys Admin: Sys Admin is a super user that has permission to modify system and scan related configurations, scan engines, create new users, add new tools etc. Super user can initiate scans and subscans effortlessly.
  - 🔍 Penetration Tester: Penetration Tester will be allowed to modify and initiate scans and subscans, add or update targets, etc. A penetration tester will not be allowed to modify system configurations.
  - 📊 Auditor: Auditor can only view and download the report. An auditor can not change any system or scan related configurations nor can initiate any scans or subscans.

🚀&nbsp;&nbsp; GPT Vulnerability Report Generation: Get ready for the future of penetration testing reports with reconPoint's groundbreaking feature: "GPT-Powered Report Generation"! With the power of OpenAI's GPT, reconPoint now provides you with detailed vulnerability descriptions, remediation strategies, and impact assessments that read like they were written by a human security expert! **But that's not all!** Our GPT-driven reports go the extra mile by scouring the web for related news articles, blogs, and references, so you have a 360-degree view of the vulnerabilities you've uncovered. With reconPoint 2.0 revolutionize your penetration testing game and impress your clients with reports that are not just informative but engaging and comprehensive with detailed analysis on impact assessment and remediation strategies.

🥷&nbsp;&nbsp; GPT-Powered Attack Surface Generation: With reconPoint 2.0, reconPoint seamlessly integrates with GPT to identify the attacks that you can likely perform on a subdomain. By making use of reconnaissance data such as page title, open ports, subdomain name etc, reconPoint can advice you the attacks you could perform on a target. reconPoint will also provide you the rationale on why the specific attack is likely to be successful.

🧭&nbsp;&nbsp;Continuous monitoring: Continuous monitoring is at the core of reconPoint's mission, and it's robust continuous monitoring feature ensures that their targets are under constant scrutiny. With the flexibility to schedule scans at regular intervals, penetration testers can effortlessly stay informed about their targets. What sets reconPoint apart is its seamless integration with popular notification channels such as Discord, Slack, and Telegram, delivering real-time alerts for newly discovered subdomains, vulnerabilities, or any changes in reconnaissance data.

### Workflow

### Features

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

### Installation (Mac/Windows/Other)

Installation instructions can be found at [https://recon.khulnasoft.com/install/detailed/](https://recon.khulnasoft.com/install/detailed/)

### Updating

1. Updating is as simple as running the following command:

    ```bash
    cd reconpoint && sudo ./update.sh
    ```

    If `update.sh` does not have execution permissions, please change it, `sudo chmod +x update.sh`
  
    **NOTE:** if you're updating from 1.3.6 and you're getting a 'password authentication failed' error, consider uninstalling 1.3.6 first, then install 2.x.x as you'd normally do.

### Changelog

[Please find the latest release notes and changelog here.](https://recon.khulnasoft.com/changelog/)


### Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire and create. Every contributions you make is **greatly appreciated**. Your contributions can be as simple as fixing the indentation or UI, or as complex as adding new modules and features.

See the [Contributing Guide](.github/CONTRIBUTING.md) to get started.

You can also [join our Discord channel #development](https://discord.gg/JuhHdHTtwd) for any development related questions.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

### First-time Open Source contributors

Please note that reconPoint is beginner friendly. If you have never done open-source before, we encourage you to do so. **We will be happy and proud of your first PR ever.**

You can start by resolving any [open issues](https://github.com/khulnasoft/reconpoint/issues).


### Support and Sponsoring

Over the past few years, I have been working hard on reconPoint to add new features with the sole aim of making it the de facto standard for reconnaissance. I spend most of my free time and weekends working on reconPoint. I do this in addition to my day job. I am happy to have received such overwhelming support from the community. But to keep this project alive, I am looking for financial support.

|                                                                       Paypal                                                                       |                                                            Bitcoin                                                             |                                                            Ethereum                                                            |
| :-------------------------------------------------------------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------------------------------------: |
|[https://www.paypal.com/paypalme/khulnasoft11](https://www.paypal.com/paypalme/khulnasoft11)                                 |                                              `35AiKyNswNZ4TZUSdriHopSCjNMPi63BCX`                                              |                                          `0xe7A337Da6ff98A28513C26A7Fec8C9b42A63d346`  

OR

* Add a [GitHub Star](https://github.com/khulnasoft/reconpoint) to the project.
* Tweet about this project, or maybe blogs?
* Maybe nominate me for [GitHub Stars?](https://stars.github.com/nominate/)
* Join DigitalOcean using my [referral link](https://m.do.co/c/e353502d19fc) your profit is **$100** and I get $25 DO credit. This will help me test reconPoint on VPS before I release any major features.

It takes a considerable amount of time to add new features and make sure everything works. Donating is your way of saying: **reconPoint is awesome**.

Any support is greatly appreciated! Thank you!

### reconPoint Bug Bounty Program

[![huntr](https://cdn.huntr.dev/huntr_security_badge_mono.svg)](https://huntr.dev/bounties/disclose/?target=https%3A%2F%2Fgithub.com%2Fkhulnasoft%2Freconpoint)

Security researchers, welcome aboard! I'm excited to announce the reconPoint bug bounty programme in collaboration with [huntr.dev](https://huntr.dev), which means that you will be rewarded for any vulnerabilities you find in reconPoint.

Thank you for your interest in reporting reconPoint vulnerabilities! If you are aware of any potential security vulnerabilities in reconPoint, we encourage you to report them immediately via [huntr.dev](https://huntr.dev/bounties/disclose/?target=https%3A%2F%2Fgithub.com%2Fkhulnasoft%2Freconpoint).

**Please do not disclose vulnerabilities via Github issues/blogs/tweets after/before reporting to huntr.dev as this is explicitly against the disclosure policy of huntr.dev and reconPoint and will not be considered for monetary rewards.**

Please note that the reconPoint maintainer does not set the bounty amount.
The bounty reward is determined by an industry-first equation developed by huntr.dev to understand the popularity, impact and value of repositories to the open-source community.

**What do I expect from security researchers?**

* Patience: Please note that I am currently the only maintainer in reconPoint and it will take some time to validate your report. I ask for your patience during this process.
* Respect for privacy and security reports: Please do not publicly disclose any vulnerabilities (including GitHub issues) before or after reporting them on huntr.dev! This is against the disclosure policy and will not be rewarded.
* Respect the rules

**What do you get in return?**

* Thanks from the maintainer
* Monetary rewards
* CVE ID(s)

Please find the [FAQ](https://www.huntr.dev/faq) and [Responsible disclosure policy](https://www.huntr.dev/policy/) from huntr.dev.

### License

Distributed under the GNU GPL v3 License. See [LICENSE](LICENSE) for more information.

<p align="right">(ChatGPT was used to write some or most part of this README section.)</p>