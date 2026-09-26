FROM frrouting/frr:latest

RUN apk add --no-cache openssh
RUN ssh-keygen -A

ARG LAB_PASSWORD
RUN test -n "$LAB_PASSWORD" && echo "root:${LAB_PASSWORD}" | chpasswd

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config || true
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config || true

CMD ["/bin/sh", "-c", "/usr/sbin/sshd && /usr/lib/frr/docker-start"]
