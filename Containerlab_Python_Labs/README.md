# Containerlab Python Labs

Hands-on lab: **Containerlab + FRR + BGP + SSH + Python + Netmiko + pytest + JUnit + Jenkins**.

## Canonical lab path

The repository folder is:

`Containerlab_Python_Labs`

After cloning:

```bash
cd ~/Network_Automation/Containerlab_Python_Labs
```

Do not use the old `Network_Automation_Containerlab` name.

## Prerequisites

Run on a fresh Ubuntu VM:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates python3 python3-pip python3-venv netcat-openbsd iproute2 openssh-client
```

Verify:

```bash
python3 --version
git --version
curl --version
ip -br addr
free -h
df -h
```

### Docker

Install Docker Engine using Docker's official Ubuntu installation instructions. Then verify:

```bash
docker --version
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo usermod -aG docker "$USER"
newgrp docker
docker ps
```

### Containerlab

```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
containerlab version
```

### Git

```bash
cd ~
git clone https://github.com/ajayyadav941/Network_Automation.git
cd ~/Network_Automation/Containerlab_Python_Labs
```

## Build the FRR SSH image

Choose a local classroom password. It is intentionally not stored in Git.

```bash
export LAB_USERNAME='root'
export LAB_PASSWORD='change-me'
docker build \
  --build-arg LAB_PASSWORD="$LAB_PASSWORD" \
  -t frr-netmiko:latest \
  -f docker/Dockerfile .
docker image inspect frr-netmiko:latest
```

## Deploy and validate

```bash
containerlab deploy -t topology/lab.clab.yml
containerlab inspect -t topology/lab.clab.yml
```

Expected management IPs:

```text
R1 172.20.20.11
R2 172.20.20.12
```

Then follow:

`Network_Testing_Containerlab.md`

For the beginner version:

`PDF/Containerlab_Python_Labs_Beginner_Guide.pdf`

## Python / Netmiko / pytest

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

export LAB_USERNAME='root'
export LAB_PASSWORD="$LAB_PASSWORD"

pytest -v -s tests/test_bgp.py tests/test_ping.py
```

Expected:

```text
6 passed
```

Generate JUnit:

```bash
bash scripts/run_tests.sh
```

## Jenkins

Jenkins is a Dockerized classroom CI environment. It is intentionally privileged because Containerlab needs access to the host Docker daemon and host network namespaces.

Build:

```bash
docker build -t network-jenkins:latest -f jenkins/Dockerfile .
docker volume create jenkins_home
```

Determine the host Docker GID:

```bash
export DOCKER_GID="$(getent group docker | cut -d: -f3)"
echo "$DOCKER_GID"
```

Create a host-visible CI directory owned by the current user:

```bash
export CI_ROOT="$HOME/jenkins-ci"
mkdir -p "$CI_ROOT"
```

Run Jenkins:

```bash
docker run -d \
  --name jenkins \
  --restart unless-stopped \
  --privileged \
  --network host \
  --pid host \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/run/netns:/var/run/netns \
  -v "$CI_ROOT":/home/jenkins/ci \
  --group-add "$DOCKER_GID" \
  network-jenkins:latest
```

Verify:

```bash
docker exec jenkins docker ps
docker exec jenkins containerlab version
docker exec jenkins id
```

Open:

```text
http://<UBUNTU_VM_IP>:8080
```

For Jenkins credentials and pipeline setup, follow the Jenkins section in `Network_Testing_Containerlab.md`.

## Important

The Jenkins container has host Docker and privileged network access. Treat this as an isolated classroom VM, not a production deployment.
