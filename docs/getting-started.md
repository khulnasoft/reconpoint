# reconPoint installation for Hackers

This section aims to answer some of the most frequently asked questions on installing reconPoint.

!!! danger "Attention"
    It is recommended that you follow each steps to avoid encountering any errors/issues during the setup.

This guide is divided into several sections based on the frequently asked questions:

- [reconPoint installation for Hackers](#reconpoint-installation-for-hackers)
  - [⚡ Quick Installation](#-quick-installation)
  - [Running reconPoint on local machine](#running-reconpoint-on-local-machine)
  - [Running reconPoint on VPS](#running-reconpoint-on-vps)
  - [Running reconPoint with your own managed database](#running-reconpoint-with-your-own-managed-database)

## ⚡ Quick Installation

If you are on Ubuntu/VPS/Linux, install script is provided for quick installation.

Follow [⚡ Quick Installation instructions](install/quick.md).

## Running reconPoint on local machine

Running reconPoint on local machine is a very straight forward process. You'll neeed `docker`, `docker-compose` and `make` to build and run reconPoint on local machine.

!!! info "Quick Installation for Linux Debian like Ubuntu"
    If you are using Ubuntu or Kali as your base OS and wish to run reconPoint on it, you may skip the prerequisites section, installation script is provided with this project that takes care of installing docker and its dependencies. [Quick Installation](quick-install)

[Quick Install reconPoint on Ubuntu or Kali](install/quick.md)

[Installing reconPoint on Windows or Mac](install/detailed.md)


## Running reconPoint on VPS

While the installation step should be very similar across all VPS providers, an example of running reconPoint on DigitalOcean is provided.

[How to Install reconPoint on DigitalOcean or any VPS](install/vps.md)


## Running reconPoint with your own managed database

This is related to a [Github Issue](https://github.com/khulnasoft/reconpoint/issues/180)

It is a good idea to run reconPoint using managed database, or remote database.

Find [how to use reconPoint with managed/remote database](install/remotedb.md)
