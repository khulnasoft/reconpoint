Added

Projects: Projects allow you to efficiently organize their web application reconnaissance efforts. With this feature, you can create distinct project spaces, each tailored to a specific purpose, such as personal bug bounty hunting, client engagements, or any other specialized recon task.
Roles and Permissions: assign distinct roles to your team members: Sys Admin, Penetration Tester, and Auditor—each with precisely defined permissions to tailor their access and actions within the reconPoint ecosystem.
GPT-powered Report Generation: With the power of OpenAI's GPT, reconPoint now provides you with detailed vulnerability descriptions, remediation strategies, and impact assessments.
API Vault: This feature allows you to organize your API keys such as OpenAI or Netlas API keys.
GPT-powered Attack Surface Generation
URL gathering now is much more efficient, removing duplicate endpoints based on similar HTTP Responses, having the same content_lenth, or page_title. Custom duplicate fields can also be set from the scan engine configuration.
URL Path filtering while initiating scan: For instance, if we want to scan only endpoints starting with https://example.com/start/, we can pass the /start as a path filter while starting the scan. @ocervell
Expanding Target Concept: reconPoint 2.0 now accepts IPs, URLS, etc as targets. (#678, #658) Excellent work by @ocervell
A ton of refactoring on reconPoint's core to improve scan efficiency. Massive kudos to @ocervell
Created a custom celery workflow to be able to run several tasks in parallel that are not dependent on each other, such OSINT task and subdomain discovery will run in parallel, and directory and file fuzzing, vulnerability scan, screenshot gathering etc. will run in parallel after port scan or url fetching is completed. This will increase the efficiency of scans and instead of having one long flow of tasks, they can run independently on their own. @ocervell
Refactored all tasks to run asynchronously @ocervell
Added a stream_command that allows to read the output of a command live: this means the UI is updated with results while the command runs and does not have to wait until the task completes. Excellent work by @ocervell
Pwndb is now replaced by h8mail. @ocervell
Group Scan Results: reconPoint 2.0 allows to group of subdomains based on similar page titles and HTTP status, and also vulnerability grouping based on the same vulnerability title and severity.
Added Support for Nmap: reconPoint 2.0 allows to run Nmap scripts and vuln scans on ports found by Naabu. @ocervell
Added support for Shared Scan Variables in Scan Engine Configuration:
enable_http_crawl: (true/false) You can disable it to be more stealthy or focus on something different than HTTP
timeout: set timeout for all tasks
rate_limit: set rate limit for all tasks
retries: set retries for all tasks
custom_header: set the custom header for all tasks
Added Dalfox for XSS Vulnerability Scan
Added CRLFuzz for CRLF Vulnerability Scan
Added S3Scanner for scanning misconfigured S3 buckets
Improve OSINT Dork results, now detects admin panels, login pages and dashboards
Added Custom Dorks
Improved UI for vulnerability results, clicking on each vulnerability will open up a sidebar with vulnerability details.
Added HTTP Request and Response in vulnerability Results
Under Admin Settings, added an option to allow add/remove/deactivate additional users
Added Option to Preview Scan Report instead of forcing to download
Added Katana for crawling and spidering URLs
Added Netlas for Whois and subdomain gathering
Added TLSX for subdomain gathering
Added CTFR for subdomain gathering
Added historical IP in whois section
Added Pagination on Large datatables such as subdomains, endpoints, vulnerabilities etc #949 @psyray
Fixes

GF patterns do not run on 404 endpoints (#574 closed)
Fixes for retrieving whois data (#693 closed)
Related/Associated Domains in Whois section is now fixed
Fixed missing lightbox css & js on target screenshot page #947 #948 @psyray
Issue in Port-scan: int object is not subscriptable Fixed #939, #938 @AnonymousWP
Removed

Removed pwndb and tor related to it.
Removed tor for pwndb