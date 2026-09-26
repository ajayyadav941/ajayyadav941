# Jenkins + Containerlab Network CI — Complete Installation, Configuration and Troubleshooting

This document records the complete Jenkins workflow used for the `Containerlab_Python_Labs` training lab, including the problems encountered, the reason for each fix, and the final working architecture.

> Training architecture only: the Jenkins controller is privileged and has access to the host Docker socket. This is suitable for an isolated classroom VM, not a production Jenkins controller.

---

## 1. Final architecture

```text
GitHub: ajayyadav941/Network_Automation
        |
        | Pipeline from SCM
        v
Jenkins container: network-jenkins:latest
        |
        | copies exact checkout
        v
/home/jenkins/ci/network-testing   <-- host-visible path
        |
        | containerlab deploy
        v
Host Docker daemon via /var/run/docker.sock
        |
        +-- clab-pytest-lab-r1  172.20.20.11
        +-- clab-pytest-lab-r2  172.20.20.12
        |
        v
SSH -> FRR -> BGP -> Netmiko -> pytest -> JUnit
        |
        v
post always -> containerlab destroy
```

Why this design matters: Containerlab running inside Jenkins talks to the **host Docker daemon**. Bind-mount source paths therefore must exist on the Ubuntu host. Jenkins' normal `/var/jenkins_home/workspace/...` lives in the Jenkins volume and is not the correct host path for Containerlab bind sources.

---

## 2. Prerequisites on Ubuntu

The Jenkins image in this repository is built from `jenkins/Dockerfile`. Jenkins itself does **not** need to be installed as a native Ubuntu service; it runs as a Docker container for this classroom lab.

Required host components before Jenkins:
- Ubuntu 22.04/24.04
- Git
- Docker Engine
- Python 3 + venv
- Containerlab
- netcat
- an available `172.20.20.0/24` management subnet
- `frr-netmiko:latest` already built with the same `LAB_PASSWORD` that Jenkins will use



Verify Docker and the project first:

```bash
docker --version
docker ps
containerlab version
python3 --version
git --version
```

Create the persistent Jenkins volume and host-visible CI root:

```bash
docker volume create jenkins_home
export CI_ROOT="$HOME/jenkins-ci"
mkdir -p "$CI_ROOT"
```

The `jenkins_home` volume keeps Jenkins configuration even if the Jenkins container is removed and recreated.

---

## 3. Jenkins Dockerfile

Use `Containerlab_Python_Labs/jenkins/Dockerfile`.

The image must provide:

```text
Jenkins LTS / Java 21
Git
Python 3 + pip + venv
Docker CLI
Containerlab
netcat
iptables / iproute2
clab_admins membership for jenkins
```

A robust Dockerfile pattern is:

```dockerfile
FROM jenkins/jenkins:lts-jdk21

USER root

RUN apt-get update && \
    apt-get install -y \
    curl git python3 python3-pip python3-venv \
    ca-certificates netcat-openbsd sudo iptables iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg \
    -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" \
    > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

RUN bash -c "$(curl -sL https://get.containerlab.dev)"

RUN groupadd -f clab_admins && \
    usermod -aG clab_admins jenkins

USER jenkins
```

Build it:

```bash
cd ~/Network_Automation/Containerlab_Python_Labs
docker build -t network-jenkins:latest -f jenkins/Dockerfile .
```

Verify:

```bash
docker images | grep network-jenkins
```

---

## 4. Determine the host Docker group ID

Do not hard-code a Docker GID because it can differ between machines.

```bash
DOCKER_GID=$(getent group docker | cut -d: -f3)
echo "$DOCKER_GID"
```

Why: `/var/run/docker.sock` is owned by a host group. Jenkins needs the matching numeric group to use the socket.

Verify socket ownership:

```bash
ls -ln /var/run/docker.sock
getent group docker
```

---

## 5. Start Jenkins with the tested runtime options

```bash
DOCKER_GID=$(getent group docker | cut -d: -f3)

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

Why each important option exists:

```text
--privileged        Containerlab needs privileged network operations in this one-VM training design.
--network host      Jenkins/Containerlab must see the host networking context.
--pid host          Required for visibility of host container namespaces/PIDs used by Containerlab.
docker.sock         Jenkins uses the host Docker daemon (Docker-outside-of-Docker).
/var/run/netns      Makes host network namespaces visible.
jenkins_home        Preserves Jenkins state.
$HOME/jenkins-ci
                    Host-visible execution directory for Containerlab bind mounts.
--group-add GID     Gives Jenkins access to the host Docker socket group.
```

Because `--network host` is used, **do not add** `-p 8080:8080` or `-p 50000:50000`.

---

## 6. Verify Jenkins container before opening the UI

```bash
docker ps
docker logs jenkins
```

Verify tools inside Jenkins:

```bash
docker exec jenkins whoami
docker exec jenkins docker --version
docker exec jenkins containerlab version
docker exec jenkins python3 --version
docker exec jenkins git --version
docker exec jenkins docker ps
```

Expected user:

```text
jenkins
```

Verify groups:

```bash
docker exec jenkins id jenkins
docker exec jenkins getent group clab_admins
```

---

## 7. Open Jenkins in the browser

Find the Ubuntu VM address:

```bash
ip addr
hostname -I
```

Open:

```text
http://<UBUNTU_VM_IP>:8080
```

If the page does not open:

```bash
docker ps
sudo ss -ltnp | grep 8080
curl -I http://localhost:8080
docker logs jenkins
```

---

## 8. Unlock Jenkins

Get the initial administrator password from the running container:

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Paste it into the Jenkins Unlock page. Do not store this password in Git.

Choose **Install suggested plugins** and allow installation to finish. Then create the Jenkins administrator user and sign in to the dashboard.

---

## 9. Verify required Jenkins functionality

The suggested plugins normally provide the basic Pipeline/Git functionality. The job also needs JUnit result publishing.

From Jenkins, confirm you can create a **Pipeline** job and select **Pipeline script from SCM**.

---

## 10. Configure GitHub credential for the private repository

Use a GitHub Personal Access Token through Jenkins Credentials. Do **not** put the token in the `Jenkinsfile`, `.md`, topology, Python code, or Git repository.

In Jenkins:

```text
Manage Jenkins
  -> Credentials
  -> System
  -> Global credentials
  -> Add Credentials
```

Use the GitHub credential with read access to the private repository. In our working setup the display name was `GitHub Private Repo Access`.

Local developer Git can use SSH while Jenkins SCM uses HTTPS/PAT. These are independent.

---

## 11. Create the Jenkins Pipeline job

Create:

```text
New Item
  -> Network-Testing-Pipeline
  -> Pipeline
```

Configure:

```text
Definition:       Pipeline script from SCM
SCM:              Git
Repository URL:   https://github.com/ajayyadav941/Network_Automation.git
Credentials:      your Jenkins GitHub credential
Branch Specifier: */main
Script Path:      Containerlab_Python_Labs/Jenkinsfile
```

Save the job.

---

## 12. Why we do NOT run Containerlab directly from `$WORKSPACE`

A first design used Jenkins' normal SCM workspace:

```text
/var/jenkins_home/workspace/Network-Testing-Pipeline
```

That is inside the Jenkins persistent Docker volume. Containerlab uses the host Docker daemon. For a topology bind such as:

```yaml
- ../configs/r1/daemons:/etc/frr/daemons
```

Containerlab resolves the source to an absolute path. The host Docker daemon then tries to find that absolute source on the **Ubuntu host**, not only inside the Jenkins container.

Therefore the robust flow is:

```text
GitHub
  -> Jenkins $WORKSPACE
  -> copy exact checkout
  -> /home/jenkins/ci/network-testing
  -> Containerlab
  -> host Docker daemon
```

The host directory is mounted into Jenkins with:

```text
-v $HOME/jenkins-ci:$HOME/jenkins-ci
```

---

## 13. CI execution directory

The Jenkinsfile uses:

```groovy
environment {
    CI_DIR = '/home/jenkins/ci/network-testing'
}
```

The Prepare CI Workspace stage should:

```bash
rm -f "$WORKSPACE/results.xml"
mkdir -p "$CI_DIR"
find "$CI_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cp -a "$WORKSPACE/." "$CI_DIR/"
rm -rf "$CI_DIR/.jenkins-venv" "$CI_DIR/reports"
rm -f "$CI_DIR/results.xml"
find "$CI_DIR/topology" -maxdepth 1 -type d -name 'clab-*' -exec rm -rf {} + 2>/dev/null || true
```

Why: every build should run the exact commit Jenkins checked out, without stale venvs, reports, or old Containerlab artifacts.

---

## 14. Use a separate Jenkins Python virtual environment

Do not reuse the developer `.venv` inside Jenkins. We encountered a broken environment/module issue when a host-created venv was reused from Jenkins.

Create a Jenkins-specific environment in the CI directory:

```bash
cd /home/jenkins/ci/network-testing
rm -rf .jenkins-venv
python3 -m venv .jenkins-venv
.jenkins-venv/bin/python -m pip install --upgrade pip
.jenkins-venv/bin/pip install -r requirements.txt
```

Verify:

```bash
.jenkins-venv/bin/python --version
.jenkins-venv/bin/pytest --version
.jenkins-venv/bin/python -c "import netmiko; print(netmiko.__version__)"
```

---

## 15. Pipeline stage order

Use this order:

```text
Checkout from GitHub
        |
Environment Check
        |
Prepare CI Workspace
        |
Install Python Dependencies
        |
Clean Old Lab
        |
Deploy Lab
        |
Wait for SSH
        |
Wait for FRR
        |
Manual BGP Verification
        |
Run Network Tests
        |
Copy JUnit to $WORKSPACE
        |
post always: Publish JUnit + Destroy Lab
```

---

## 16. Environment Check stage

Useful commands:

```bash
whoami
pwd
docker --version
containerlab version
python3 --version
git --version
```

This isolates installation/permission problems before the topology is touched.

---

## 17. Clean and deploy the lab

```bash
cd "$CI_DIR"
containerlab destroy -t topology/lab.clab.yml --cleanup || true
containerlab deploy -t topology/lab.clab.yml
containerlab inspect -t topology/lab.clab.yml
```

Expected:

```text
R1 management: 172.20.20.11
R2 management: 172.20.20.12
```

---

## 18. Wait for SSH instead of using a blind sleep

```bash
for host in 172.20.20.11 172.20.20.12; do
    READY=0
    for i in $(seq 1 30); do
        if nc -z "$host" 22; then
            READY=1
            break
        fi
        sleep 2
    done
    [ "$READY" -eq 1 ] || exit 1
done
```

Why: a Docker container can be `running` before SSH is ready.

---

## 19. Wait for FRR Zebra and bgpd

We observed Zebra starting much later than the container itself, including a successful run where R1 became ready only around retry 28. A fixed short sleep is unreliable.

Use process and functional checks:

```bash
for router in r1 r2; do
    container="clab-pytest-lab-$router"
    READY=0

    for i in $(seq 1 30); do
        ZEBRA=$(docker exec "$container" ps aux | grep '/usr/lib/frr/zebra' | grep -v grep || true)
        BGPD=$(docker exec "$container" ps aux | grep '/usr/lib/frr/bgpd' | grep -v grep || true)

        if [ -n "$ZEBRA" ] && [ -n "$BGPD" ]; then
            sleep 3
            if docker exec "$container" vtysh -c "show zebra" >/dev/null 2>&1; then
                READY=1
                break
            fi
        fi
        sleep 2
    done

    if [ "$READY" -ne 1 ]; then
        docker exec "$container" ps aux || true
        docker logs "$container" || true
        exit 1
    fi
done
```

Note: BusyBox/Alpine `ps` may not support `ps -p` as expected. `ps aux | grep ...` worked in this lab.

---

## 20. Manual BGP diagnostics in Jenkins

Before pytest, print protocol state:

```bash
docker exec clab-pytest-lab-r1 vtysh -c "show ip bgp summary"
docker exec clab-pytest-lab-r2 vtysh -c "show ip bgp summary"
docker exec clab-pytest-lab-r1 vtysh -c "show ip route bgp"
docker exec clab-pytest-lab-r2 vtysh -c "show ip route bgp"
```

This stage is diagnostic. The pytest assertions are the actual pass/fail protocol validation.

---

## 21. Run the canonical six tests

Use explicit test files so old/demo tests are not accidentally collected:

```bash
cd "$CI_DIR"
mkdir -p reports
rm -f reports/results.xml

.jenkins-venv/bin/pytest \
  -v \
  -s \
  tests/test_bgp.py \
  tests/test_ping.py \
  --junitxml=reports/results.xml
```

Expected healthy result:

```text
6 passed
```

---

## 22. Preserve JUnit even when pytest fails

Do not use a simple Jenkins `sh` step followed by a copy because a non-zero pytest exit can stop the stage before the XML is copied.

Use `returnStatus: true`, copy the report, then explicitly fail the build:

```groovy
script {
    int pytestStatus = sh(
        script: '''
            cd "$CI_DIR"
            mkdir -p reports
            rm -f reports/results.xml
            .jenkins-venv/bin/pytest -v -s \
                tests/test_bgp.py tests/test_ping.py \
                --junitxml=reports/results.xml
        ''',
        returnStatus: true
    )

    sh '''
        if [ -f "$CI_DIR/reports/results.xml" ]; then
            cp "$CI_DIR/reports/results.xml" "$WORKSPACE/results.xml"
        fi
    '''

    if (pytestStatus != 0) {
        error("Network tests failed")
    }
}
```

Why: failed tests are most useful when Jenkins still publishes their individual JUnit results.

---

## 23. Always publish and clean up

Use Jenkins `post { always { ... } }`:

```groovy
post {
    always {
        junit allowEmptyResults: true, testResults: 'results.xml'
        sh '''
            if [ -f "$CI_DIR/topology/lab.clab.yml" ]; then
                cd "$CI_DIR"
                containerlab destroy -t topology/lab.clab.yml --cleanup || true
            fi
        '''
    }
}
```

Why: a failed test must not leave stale R1/R2 containers that contaminate the next build.

---

# Troubleshooting from the actual setup

## 24. Jenkins reports `clab_admins` membership error

Cause: adding only the Docker socket numeric GID does not satisfy Containerlab's named `clab_admins` check.

Verify:

```bash
docker exec jenkins id jenkins
docker exec jenkins getent group clab_admins
```

Temporary fix for an already-running older image:

```bash
docker exec -u root jenkins groupadd -f clab_admins
docker exec -u root jenkins usermod -aG clab_admins jenkins
docker restart jenkins
```

Permanent fix: put this in the Jenkins Dockerfile and rebuild:

```dockerfile
RUN groupadd -f clab_admins && \
    usermod -aG clab_admins jenkins
```

Important: changes made with `usermod` inside a container are lost when that container is replaced. `jenkins_home` preserves Jenkins application state, not `/etc/group` from the old container.

---

## 25. `groups: cannot find name for group ID ...`

This can occur for the numeric host Docker GID passed with `--group-add` when no matching group name exists inside the container.

If:

```bash
docker exec jenkins docker ps
```

works, the numeric Docker socket access is functioning. Separately verify the named `clab_admins` group.

---

## 26. `sudo` inside Jenkins asks for a password

Do not rely on interactive `sudo` inside the Jenkins container. Execute administrative fixes from the Ubuntu host:

```bash
docker exec -u root jenkins <command>
```

Then make the change permanent in the Dockerfile.

---

## 27. `rp_filter` is read-only

This was resolved by running the training Jenkins container with:

```text
--privileged
```

Recreate the Jenkins container with the final tested runtime options.

---

## 28. Containerlab reports bridge `Link not found`

In this Dockerized-Containerlab design, Jenkins needed the host network namespace:

```text
--network host
```

Do not combine this with `-p 8080:8080`; host networking already exposes Jenkins on the host's port 8080.

---

## 29. `namespace path not available for container`

The working setup required host PID visibility and netns mounting:

```text
--pid host
-v /var/run/netns:/var/run/netns
```

---

## 30. Missing `iptables` or `ip6tables`

Install network tooling in the Jenkins image:

```dockerfile
RUN apt-get update && \
    apt-get install -y iptables iproute2 && \
    rm -rf /var/lib/apt/lists/*
```

Rebuild and recreate Jenkins.

---

## 31. Jenkins cannot use `/var/run/docker.sock`

Check the host:

```bash
getent group docker
ls -ln /var/run/docker.sock
```

Check Jenkins:

```bash
docker exec jenkins id
docker exec jenkins docker ps
```

Recreate using the dynamic GID:

```bash
DOCKER_GID=$(getent group docker | cut -d: -f3)
```

and:

```text
--group-add "$DOCKER_GID"
```

---

## 32. Jenkins browser does not open

```bash
docker ps
docker logs jenkins
sudo ss -ltnp | grep 8080
curl -I http://localhost:8080
```

Remember: with `--network host`, use:

```text
http://<Ubuntu-VM-IP>:8080
```

---

## 33. Jenkins `dir(...)` / `@tmp` AccessDeniedException

Jenkins Durable Task may create a sibling `@tmp` directory. If a host-mounted path causes permissions trouble, avoid depending on `dir('/host/path')` for shell execution. Use a shell block and `cd` explicitly:

```groovy
sh '''
    cd "$CI_DIR"
    ...
'''
```

This also keeps Jenkins' own durable-task files in its normal workspace.

---

## 34. Python `_pytest` / module error in Jenkins

Cause encountered: reusing an environment created in a different context.

Fix:

```bash
cd "$CI_DIR"
rm -rf .jenkins-venv
python3 -m venv .jenkins-venv
.jenkins-venv/bin/python -m pip install --upgrade pip
.jenkins-venv/bin/pip install -r requirements.txt
```

Do not reuse the developer `.venv` for Jenkins.

---

## 35. Containerlab bind source path does not exist

Do not deploy from `/var/jenkins_home/workspace/...` when Containerlab is using the host Docker daemon.

Verify:

```bash
ls -la /home/jenkins/ci/network-testing
find /home/jenkins/ci/network-testing/configs -maxdepth 2 -type f -print
```

Deploy from:

```bash
cd /home/jenkins/ci/network-testing
containerlab deploy -t topology/lab.clab.yml
```

---

## 36. FRR readiness fails while containers are running

Check:

```bash
docker exec clab-pytest-lab-r1 ps aux | grep -E 'zebra|bgpd|staticd'
docker exec clab-pytest-lab-r1 cat /etc/frr/daemons
docker exec clab-pytest-lab-r1 vtysh -c "show zebra"
docker logs clab-pytest-lab-r1
```

Repeat for R2. Container `running` does not mean Zebra and bgpd are ready. Keep retry logic.

---

## 37. Zebra PID lock when starting Zebra manually

Before manually starting another Zebra process, inspect the existing process and PID file:

```bash
docker exec clab-pytest-lab-r1 ps aux | grep zebra
docker exec clab-pytest-lab-r1 cat /var/run/frr/zebra.pid
```

If Zebra is already running, starting a second copy can fail because the PID lock is correct behavior.

---

## 38. BGP is Active or Idle

Troubleshoot in layers:

```bash
docker exec clab-pytest-lab-r1 ip addr show eth1
docker exec clab-pytest-lab-r2 ip addr show eth1
docker exec clab-pytest-lab-r1 ping -c 3 10.1.100.2
docker exec clab-pytest-lab-r2 ping -c 3 10.1.100.1
docker exec clab-pytest-lab-r1 vtysh -c "show ip bgp summary"
docker exec clab-pytest-lab-r2 vtysh -c "show ip bgp summary"
```

Then verify neighbor IP and remote AS in both `bgpd.conf` files.

---

## 39. BGP shows `(Policy)`

Both routers require for this classroom lab:

```text
no bgp ebgp-requires-policy
```

---

## 40. Harmless `vtysh.conf` warning

You may see:

```text
% Can't open configuration file /etc/frr/vtysh.conf due to 'No such file or directory'.
```

If `vtysh -c` still returns the expected FRR data, this warning does not invalidate the test.

---

## 41. pytest unexpectedly runs old tests

Check collection:

```bash
pytest --collect-only -q
```

Canonical regression:

```bash
pytest -v -s tests/test_bgp.py tests/test_ping.py
```

Expected:

```text
6 passed
```

---

## 42. pytest fails and Jenkins shows no JUnit report

Use `returnStatus: true`, generate XML with `--junitxml`, copy it to `$WORKSPACE/results.xml`, then call `error(...)`. Publish from `post { always { ... } }`.

This preserves test evidence even when the network regression fails.

---

## 43. Stale JUnit result appears in a later build

Remove the old workspace result before the run:

```bash
rm -f "$WORKSPACE/results.xml"
```

Also recreate the CI report directory for each build.

---

## 44. Stale Containerlab artifacts affect a later build

Clean both the previous lab and copied artifacts:

```bash
containerlab destroy -t topology/lab.clab.yml --cleanup || true
find "$CI_DIR/topology" -maxdepth 1 -type d -name 'clab-*' -exec rm -rf {} + 2>/dev/null || true
```

Always keep final cleanup in `post { always { ... } }`.

---

## 45. Git reports dubious ownership

If the local project was created or modified as root:

```bash
sudo chown -R ajay:ajay $HOME/Network_Automation
```

Use the normal user for routine Git work.

---

## 46. Local GitHub SSH authentication fails

Generate a developer SSH key if needed:

```bash
ssh-keygen -t ed25519 -C "your-github-email"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
```

Add only the **public** key to GitHub, then test:

```bash
ssh -T git@github.com
```

Never share or commit the private key.

---

## 47. GitHub hostname/DNS resolution fails

Test IP connectivity and DNS separately:

```bash
ping -c 3 8.8.8.8
ping -c 3 github.com
getent hosts github.com
```

Then, if needed:

```bash
sudo systemctl restart systemd-resolved
```

Retest Git/SSH after DNS is healthy.

---

## 48. Git histories are unrelated

When a local repository and remote repository were initialized separately, the merge may require:

```bash
git pull origin main --allow-unrelated-histories --no-rebase
```

Resolve any conflicts, commit, then push.

---

# Negative test and recovery

## 49. Prove Jenkins detects a real network defect

Temporarily change R2:

```text
neighbor 10.1.100.1 remote-as 65001
```

to:

```text
neighbor 10.1.100.1 remote-as 65100
```

Commit/push and run Jenkins.

Expected:

```text
SCM checkout       PASS
Container deploy   PASS
SSH readiness      PASS
FRR readiness      PASS
BGP correctness    FAIL
pytest              FAIL
JUnit               PUBLISHED
cleanup             RUNS
Jenkins             FAILURE
```

Why this is a good demonstration: infrastructure is healthy, but the network intent is wrong. pytest catches the protocol defect.

Restore:

```text
neighbor 10.1.100.1 remote-as 65001
```

Run again.

Expected:

```text
R1/R2 BGP Established
R1 learns 2.2.2.2/32
R2 learns 1.1.1.1/32
both loopback pings pass
6 pytest tests pass
JUnit is published
Containerlab is destroyed in cleanup
Jenkins finishes SUCCESS
```

---

# Final classroom workflow

## 50. Fresh start for each class

The custom FRR image is built once and reused. Destroying Containerlab removes the running routers, not the Docker image.

```bash
cd ~/Network_Automation/Containerlab_Python_Labs
containerlab destroy -t topology/lab.clab.yml --cleanup || true
docker images | grep frr-netmiko
containerlab deploy -t topology/lab.clab.yml
containerlab inspect -t topology/lab.clab.yml
```

Teaching progression:

```text
Manual interface ping
        -> Manual BGP
        -> Manual route verification
        -> Manual SSH
        -> Python
        -> Netmiko
        -> pytest assertions
        -> six-test regression
        -> JUnit
        -> Git/GitHub
        -> Jenkins SCM
        -> Containerlab CI
        -> intentional failure
        -> fix
        -> Jenkins SUCCESS
```

## 51. Final success checklist

```text
[ ] Docker works for the normal Ubuntu user
[ ] Containerlab works on the Ubuntu host
[ ] frr-netmiko:latest exists
[ ] R1 = 172.20.20.11
[ ] R2 = 172.20.20.12
[ ] 10.1.100.1 <-> 10.1.100.2 ping succeeds
[ ] Zebra and bgpd are ready
[ ] BGP is Established
[ ] R1 learns 2.2.2.2/32
[ ] R2 learns 1.1.1.1/32
[ ] loopback pings succeed
[ ] Netmiko works
[ ] pytest reports 6 passed
[ ] JUnit XML is generated
[ ] Jenkins can use host Docker
[ ] Jenkins is in clab_admins
[ ] CI_DIR is host-visible
[ ] Jenkins checks out Network_Automation/main
[ ] Jenkins uses Containerlab_Python_Labs/Jenkinsfile
[ ] JUnit publishes on success and failure
[ ] cleanup runs on success and failure
[ ] intentional BGP defect produces Jenkins FAILURE
[ ] restored BGP produces Jenkins SUCCESS
```
