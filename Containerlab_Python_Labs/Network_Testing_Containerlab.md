# Network Automation with Containerlab — Complete Hands-On Lab

This folder is a self-contained training project for **Containerlab + FRRouting (FRR) + BGP + SSH + Python + Netmiko + pytest + JUnit + Jenkins**.

The goal is that a student can start with an Ubuntu VM, follow this file from top to bottom, deploy two FRR routers, verify BGP manually, automate validation with Python/Netmiko and pytest, and finally run the same regression from Jenkins.

---

## 1. Final topology

```text
                         10.1.100.0/30

        R1 ------------------------------------- R2
        FRR                                      FRR
        AS 65001                                 AS 65002
        Lo: 1.1.1.1/32                           Lo: 2.2.2.2/32
        eth1: 10.1.100.1/30                      eth1: 10.1.100.2/30
        Mgmt: 172.20.20.11                       Mgmt: 172.20.20.12
```

Expected learned routes:

```text
R1 learns 2.2.2.2/32 via 10.1.100.2
R2 learns 1.1.1.1/32 via 10.1.100.1
```

---

## 2. Folder structure

```text
Containerlab_Python_Labs/
├── .gitignore
├── Jenkinsfile
├── Network_Testing_Containerlab.md
├── requirements.txt
├── docker/
│   └── Dockerfile
├── jenkins/
│   └── Dockerfile
├── topology/
│   └── lab.clab.yml
├── configs/
│   ├── r1/
│   │   ├── daemons
│   │   ├── zebra.conf
│   │   └── bgpd.conf
│   └── r2/
│       ├── daemons
│       ├── zebra.conf
│       └── bgpd.conf
├── scripts/
│   ├── bgp_check.py
│   ├── Both_Router_bgp_check.py
│   └── run_tests.sh
└── tests/
    ├── conftest.py
    ├── test_bgp.py
    └── test_ping.py
```

---

# PART A — Ubuntu, Docker and Containerlab

## 3. Prepare Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates python3 python3-pip python3-venv netcat-openbsd iproute2
```

Verify:

```bash
python3 --version
git --version
ip addr
free -h
df -h
```

**Why:** Docker, Containerlab, Python, Netmiko and Jenkins all depend on a healthy base Linux environment.

---

## 4. Install Docker Engine

Follow Docker's official Ubuntu installation procedure, then verify:

```bash
docker --version
sudo systemctl status docker
sudo docker run --rm hello-world
```

Allow your normal user to use Docker:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Test:

```bash
docker ps
```

**Expected:** no Docker socket permission error.

---

## 5. Install Containerlab

```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
containerlab version
```

Containerlab will create and connect the FRR containers described by `topology/lab.clab.yml`.

---

## 6. Clone the repository

```bash
cd ~
git clone https://github.com/ajayyadav941/Network_Automation.git
cd Network_Automation/Containerlab_Python_Labs
```

Verify:

```bash
pwd
find . -maxdepth 3 -type f | sort
```

---

# PART B — Build the FRR Router Image

## 7. Set a lab password locally

The password is deliberately **not stored in GitHub**.

```bash
export LAB_PASSWORD='choose-a-lab-password'
export LAB_USERNAME='root'
```

Use the same value when building the FRR image and when running Netmiko/pytest.

---

## 8. Build the SSH-enabled FRR image

The provided `docker/Dockerfile` starts from `frrouting/frr:latest`, installs OpenSSH, creates host keys, enables SSH password login for the isolated training environment, and starts SSH plus FRR.

Build:

```bash
docker build \
  --build-arg LAB_PASSWORD="$LAB_PASSWORD" \
  -t frr-netmiko:latest \
  -f docker/Dockerfile .
```

Verify:

```bash
docker images | grep frr-netmiko
```

Expected image:

```text
frr-netmiko   latest
```

---

# PART C — FRR Configuration

## 9. FRR daemons

Both `configs/r1/daemons` and `configs/r2/daemons` enable:

```text
zebra=yes
bgpd=yes
staticd=yes
```

`zebra` manages interface/routing state. `bgpd` provides BGP.

---

## 10. R1 interface configuration

`configs/r1/zebra.conf`:

```text
hostname r1
!
interface eth1
 ip address 10.1.100.1/30
!
interface lo
 ip address 1.1.1.1/32
!
```

## 11. R1 BGP configuration

`configs/r1/bgpd.conf`:

```text
hostname r1
!
router bgp 65001
 bgp router-id 1.1.1.1
 no bgp ebgp-requires-policy
 neighbor 10.1.100.2 remote-as 65002
 !
 address-family ipv4 unicast
  network 1.1.1.1/32
  neighbor 10.1.100.2 activate
 exit-address-family
!
```

---

## 12. R2 interface configuration

`configs/r2/zebra.conf`:

```text
hostname r2
!
interface eth1
 ip address 10.1.100.2/30
!
interface lo
 ip address 2.2.2.2/32
!
```

## 13. R2 BGP configuration

`configs/r2/bgpd.conf`:

```text
hostname r2
!
router bgp 65002
 bgp router-id 2.2.2.2
 no bgp ebgp-requires-policy
 neighbor 10.1.100.1 remote-as 65001
 !
 address-family ipv4 unicast
  network 2.2.2.2/32
  neighbor 10.1.100.1 activate
 exit-address-family
!
```

`no bgp ebgp-requires-policy` prevents the FRR traditional-profile `(Policy)` condition in this simple classroom eBGP lab.

---

# PART D — Deploy Containerlab

## 14. Check for management subnet conflicts

The lab uses `172.20.20.0/24`.

```bash
docker network ls
for n in $(docker network ls -q); do
  docker network inspect "$n" --format '{{.Name}} {{range .IPAM.Config}}{{.Subnet}}{{end}}'
done
```

If another Docker network already owns `172.20.20.0/24`, change the lab management subnet and management addresses consistently.

---

## 15. Deploy the topology

```bash
cd ~/Network_Automation/Containerlab_Python_Labs
containerlab deploy -t topology/lab.clab.yml
```

Inspect:

```bash
containerlab inspect -t topology/lab.clab.yml
```

Expected management addresses:

```text
r1  172.20.20.11
r2  172.20.20.12
```

Check Docker:

```bash
docker ps
```

Expected containers:

```text
clab-pytest-lab-r1
clab-pytest-lab-r2
```

---

# PART E — Manual Network Validation

## 16. Check interfaces

```bash
docker exec clab-pytest-lab-r1 ip addr show eth1
docker exec clab-pytest-lab-r2 ip addr show eth1
```

Expected:

```text
R1 eth1 -> 10.1.100.1/30
R2 eth1 -> 10.1.100.2/30
```

---

## 17. Test direct interface connectivity

```bash
docker exec clab-pytest-lab-r1 ping -c 4 10.1.100.2
docker exec clab-pytest-lab-r2 ping -c 4 10.1.100.1
```

Expected:

```text
0% packet loss
```

Do not troubleshoot BGP until this direct peer connectivity works.

---

## 18. Verify FRR processes

```bash
docker exec clab-pytest-lab-r1 ps aux | grep -E 'zebra|bgpd'
docker exec clab-pytest-lab-r2 ps aux | grep -E 'zebra|bgpd'
```

Functional check:

```bash
docker exec clab-pytest-lab-r1 vtysh -c "show zebra"
docker exec clab-pytest-lab-r2 vtysh -c "show zebra"
```

---

## 19. Verify BGP

```bash
docker exec clab-pytest-lab-r1 vtysh -c "show ip bgp summary"
docker exec clab-pytest-lab-r2 vtysh -c "show ip bgp summary"
```

Expected intent:

```text
R1: local AS 65001, neighbor 10.1.100.2, remote AS 65002
R2: local AS 65002, neighbor 10.1.100.1, remote AS 65001
```

The session must not remain in:

```text
Active
Idle
(Policy)
```

---

## 20. Verify BGP routes

```bash
docker exec clab-pytest-lab-r1 vtysh -c "show ip route bgp"
docker exec clab-pytest-lab-r2 vtysh -c "show ip route bgp"
```

Expected:

```text
R1: 2.2.2.2/32 via 10.1.100.2
R2: 1.1.1.1/32 via 10.1.100.1
```

---

## 21. Verify end-to-end loopback reachability

```bash
docker exec clab-pytest-lab-r1 ping -c 3 2.2.2.2
docker exec clab-pytest-lab-r2 ping -c 3 1.1.1.1
```

Expected:

```text
0% packet loss
```

---

# PART F — SSH, Python and Netmiko

## 22. Test SSH manually

```bash
ssh root@172.20.20.11
```

Enter the value you set in `LAB_PASSWORD`.

Inside R1:

```bash
vtysh -c "show ip bgp summary"
```

Exit:

```bash
exit
```

Repeat for R2:

```bash
ssh root@172.20.20.12
```

**Why:** manual SSH should work before debugging Netmiko.

If the host key changes after a lab redeploy:

```bash
ssh-keygen -R 172.20.20.11
ssh-keygen -R 172.20.20.12
```

---

## 23. Create the Python environment

```bash
cd ~/Network_Automation/Containerlab_Python_Labs
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify:

```bash
pytest --version
python -c "import netmiko; print(netmiko.__version__)"
```

---

## 24. Run the R1 Netmiko script

Make sure the environment variables exist in this shell:

```bash
export LAB_USERNAME='root'
export LAB_PASSWORD='choose-a-lab-password'
```

Run:

```bash
python scripts/bgp_check.py
```

The script connects to R1 over SSH and runs:

```text
show ip bgp summary
```

through `vtysh`.

---

## 25. Run the two-router Netmiko script

```bash
python scripts/Both_Router_bgp_check.py
```

Expected: BGP summary and BGP route output from both routers.

---

# PART G — pytest Network Regression

## 26. Understand the six tests

The active regression contains six tests:

```text
1. R1 BGP neighbor validation
2. R2 BGP neighbor validation
3. R1 learns R2 loopback
4. R2 learns R1 loopback
5. R1 can ping R2 loopback
6. R2 can ping R1 loopback
```

`tests/conftest.py` creates session-scoped Netmiko connections using:

```text
R1 = 172.20.20.11
R2 = 172.20.20.12
username = LAB_USERNAME or root
password = LAB_PASSWORD
```

---

## 27. Run pytest

```bash
export LAB_USERNAME='root'
export LAB_PASSWORD='choose-a-lab-password'

pytest -v -s tests/test_bgp.py tests/test_ping.py
```

Expected:

```text
6 passed
```

---

## 28. Generate JUnit XML

```bash
mkdir -p reports
pytest -v -s \
  tests/test_bgp.py \
  tests/test_ping.py \
  --junitxml=reports/results.xml
```

Verify:

```bash
ls -lh reports/results.xml
```

Or use the included helper:

```bash
bash scripts/run_tests.sh
```

JUnit allows Jenkins to display individual test results and failures.

---

# PART H — Dockerized Jenkins

## 29. Build the Jenkins image

The provided `jenkins/Dockerfile` includes Java/Jenkins, Git, Python, Docker CLI, Containerlab, `iptables`, `iproute2`, and `clab_admins` membership.

```bash
cd ~/Network_Automation/Containerlab_Python_Labs
docker build -t network-jenkins:latest -f jenkins/Dockerfile .
```

Create persistent Jenkins data and the host-visible CI directory:

```bash
docker volume create jenkins_home
mkdir -p $HOME/jenkins-ci
```

If your Linux username is not `ajay`, update the host paths in the Jenkins runtime command and `CI_DIR` in `Jenkinsfile`.

---

## 30. Determine Docker group ID

```bash
DOCKER_GID=$(getent group docker | cut -d: -f3)
echo "$DOCKER_GID"
```

Do not assume the Docker GID is the same on every computer.

---

## 31. Run Jenkins

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
  -v $HOME/jenkins-ci:$HOME/jenkins-ci \
  --group-add "$DOCKER_GID" \
  network-jenkins:latest
```

Check:

```bash
docker ps
docker logs jenkins
```

Because Jenkins uses `--network host`, open:

```text
http://<Ubuntu-VM-IP>:8080
```

Do not add `-p 8080:8080` when using host networking.

> This is a highly privileged classroom design. Do not use a privileged Jenkins controller with host Docker access in production. Use an isolated build agent and proper secret management.

---

## 32. Why Jenkins uses a host-visible CI directory

Jenkins checks out Git under its workspace, but Containerlab communicates with the **host Docker daemon** through `/var/run/docker.sock`.

```text
GitHub
  ↓
Jenkins checkout
/var/jenkins_home/workspace/...
  ↓ copy
/home/jenkins/ci/network-testing
  ↓
Containerlab
  ↓
Host Docker daemon
```

Containerlab converts relative FRR bind mounts into absolute paths. Those source paths must exist on the Ubuntu host. That is why the pipeline copies the SCM checkout to `/home/jenkins/ci/network-testing` before deployment.

---

## 33. Jenkins job configuration

Create a Pipeline job and configure **Pipeline script from SCM**.

Repository:

```text
https://github.com/ajayyadav941/Network_Automation.git
```

Branch:

```text
*/main
```

Script Path:

```text
Containerlab_Python_Labs/Jenkinsfile
```

For a private repository, store the GitHub credential in Jenkins Credentials rather than writing a token into the repository.

---

## 34. Provide the lab password to Jenkins

The repository does not contain the router password. Configure it securely in Jenkins and expose it to the pipeline as `LAB_PASSWORD`.

For classroom testing you can use Jenkins Credentials and bind it as an environment variable. Do not commit the password to Git.

The FRR image must have been built with the same lab password before the pipeline deploys it.

---

## 35. Jenkins pipeline stages

The included `Jenkinsfile` performs:

```text
Environment Check
  ↓
Prepare host-visible CI workspace
  ↓
Install Python dependencies
  ↓
Clean old Containerlab
  ↓
Deploy fresh topology
  ↓
Wait for SSH
  ↓
Wait for Zebra/bgpd
  ↓
Print manual BGP diagnostics
  ↓
Run pytest
  ↓
Copy/publish JUnit
  ↓
Always destroy Containerlab
```

A routing container being `running` is not enough. The pipeline waits for SSH and FRR readiness before starting the protocol regression.

---

# PART I — Failure Testing

## 36. Intentionally break BGP

Edit R2:

```text
configs/r2/bgpd.conf
```

Change:

```text
neighbor 10.1.100.1 remote-as 65001
```

to an incorrect remote AS such as:

```text
neighbor 10.1.100.1 remote-as 65100
```

Redeploy or commit/push and run Jenkins.

Expected behavior:

```text
Containers       PASS
SSH readiness    PASS
FRR readiness    PASS
BGP correctness  FAIL
pytest           FAIL
JUnit            PUBLISHED
Cleanup          RUNS
Jenkins          FAILURE
```

This proves the CI pipeline detects a real network configuration defect.

---

## 37. Restore BGP

Restore:

```text
neighbor 10.1.100.1 remote-as 65001
```

Run again.

Expected final result:

```text
BGP Established
R1 learns 2.2.2.2/32
R2 learns 1.1.1.1/32
Both loopback pings pass
pytest: 6 passed
JUnit published
Containerlab cleaned
Jenkins: SUCCESS
```

---

# PART J — Troubleshooting

## 38. Docker permission denied

```bash
sudo usermod -aG docker $USER
newgrp docker
docker ps
```

## 39. Management subnet overlap

```bash
docker network ls
```

Inspect Docker subnets and choose an unused management subnet.

## 40. R1/R2 not running

```bash
docker ps -a
docker logs clab-pytest-lab-r1
docker logs clab-pytest-lab-r2
```

## 41. eth1 missing or wrong address

```bash
docker exec clab-pytest-lab-r1 ip addr
docker exec clab-pytest-lab-r2 ip addr
```

## 42. Direct peer ping fails

```bash
docker exec clab-pytest-lab-r1 ping -c 3 10.1.100.2
docker exec clab-pytest-lab-r2 ping -c 3 10.1.100.1
```

Fix this before BGP.

## 43. Zebra/bgpd not running

```bash
docker exec clab-pytest-lab-r1 cat /etc/frr/daemons
docker exec clab-pytest-lab-r1 ps aux | grep zebra
docker exec clab-pytest-lab-r1 ps aux | grep bgpd
```

Repeat for R2.

## 44. BGP Active/Idle

Check, in order:

```text
eth1 address
peer ping
neighbor address
remote AS
bgpd process
```

## 45. BGP shows `(Policy)`

Confirm both BGP configs contain:

```text
no bgp ebgp-requires-policy
```

## 46. BGP established but route missing

Verify:

```bash
docker exec clab-pytest-lab-r1 vtysh -c "show ip bgp"
docker exec clab-pytest-lab-r2 vtysh -c "show ip bgp"
```

Check the loopback address, `network` statement, and IPv4 address-family activation.

## 47. Harmless `vtysh.conf` warning

You may see:

```text
% Can't open configuration file /etc/frr/vtysh.conf due to 'No such file or directory'.
```

If the requested `vtysh` command still returns the expected FRR output, this warning does not invalidate this lab.

## 48. SSH connection fails

```bash
nc -zv 172.20.20.11 22
nc -zv 172.20.20.12 22
```

Then test SSH manually before Netmiko.

## 49. Netmiko module missing

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -c "import netmiko; print(netmiko.__version__)"
```

## 50. pytest collects unexpected tests

```bash
pytest --collect-only -q
```

The canonical regression should be run explicitly:

```bash
pytest -v -s tests/test_bgp.py tests/test_ping.py
```

## 51. JUnit missing

```bash
mkdir -p reports
rm -f reports/results.xml
pytest -v -s tests/test_bgp.py tests/test_ping.py --junitxml=reports/results.xml
ls -lh reports/results.xml
```

## 52. Jenkins cannot access Docker

```bash
getent group docker
ls -ln /var/run/docker.sock
docker exec jenkins id
docker exec jenkins docker ps
```

## 53. Containerlab says Jenkins is not in `clab_admins`

The provided Jenkins image creates this group. Verify:

```bash
docker exec jenkins id jenkins
docker exec jenkins getent group clab_admins
```

If an older Jenkins container was created before the Dockerfile fix, rebuild/recreate it.

## 54. `rp_filter`, link, or namespace errors inside Jenkins

The tested one-VM classroom architecture requires:

```text
--privileged
--network host
--pid host
-v /var/run/netns:/var/run/netns
```

## 55. Containerlab bind mounts fail in Jenkins

Run the topology from the host-visible CI path, not directly from `/var/jenkins_home/workspace/...`.

## 56. FRR starts slowly

Use retry logic. Do not assume a fixed sleep proves Zebra/bgpd are ready.

## 57. pytest fails but JUnit must still publish

The included Jenkins pipeline captures pytest's exit status, copies `results.xml`, and then fails the build. This preserves the failure evidence.

## 58. Cleanup must run after failures

Containerlab cleanup belongs in Jenkins `post { always { ... } }` so failed builds do not leave stale routers for the next run.

---

# PART K — Fresh Classroom Reset

## 59. Start every class with a fresh lab

```bash
cd ~/Network_Automation/Containerlab_Python_Labs
containerlab destroy -t topology/lab.clab.yml --cleanup || true
docker images | grep frr-netmiko
containerlab deploy -t topology/lab.clab.yml
containerlab inspect -t topology/lab.clab.yml
```

Destroying the lab removes the running containers; it does not remove the reusable `frr-netmiko:latest` image.

```text
Docker image = reusable blueprint
Container = disposable running instance
Git = intended state
Netmiko = SSH automation
pytest = network intent validation
JUnit = machine-readable test evidence
Jenkins = CI orchestration
```

---

# Final validation checklist

A successful end-to-end run should prove:

```text
[ ] Docker works
[ ] Containerlab works
[ ] frr-netmiko:latest exists
[ ] R1 and R2 deploy
[ ] R1 = 172.20.20.11
[ ] R2 = 172.20.20.12
[ ] R1/R2 direct peer ping passes
[ ] Zebra is running
[ ] bgpd is running
[ ] BGP is established
[ ] R1 learns 2.2.2.2/32
[ ] R2 learns 1.1.1.1/32
[ ] Loopback ping works both ways
[ ] Manual SSH works
[ ] Netmiko scripts work
[ ] pytest reports 6 passed
[ ] JUnit XML is generated
[ ] Jenkins can deploy the lab
[ ] Jenkins publishes JUnit
[ ] Jenkins cleans the lab
[ ] Intentional BGP defect causes FAILURE
[ ] Restored configuration causes SUCCESS
```

---

## Golden troubleshooting rule

```text
Host/Ubuntu
   ↓
Docker
   ↓
Containerlab
   ↓
Containers
   ↓
Interfaces
   ↓
Direct peer ping
   ↓
Zebra/bgpd
   ↓
BGP
   ↓
Routes
   ↓
Loopback ping
   ↓
SSH
   ↓
Netmiko
   ↓
pytest
   ↓
JUnit
   ↓
Jenkins
```

Always repair the lowest failing layer first.
