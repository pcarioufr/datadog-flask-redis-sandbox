FROM ubuntu:22.04

ENV TZ=Europe/Paris
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt upgrade -y -qq
RUN apt install -y -qq \
    sudo \
    lsb-release \
    software-properties-common \
    wget

# Install Terraform CLI 
# https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli
RUN wget -O- https://apt.releases.hashicorp.com/gpg | \
        gpg --dearmor | \
        tee /usr/share/keyrings/hashicorp-archive-keyring.gpg

RUN gpg --no-default-keyring \
        --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg \
        --fingerprint

RUN echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
        https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
        tee /etc/apt/sources.list.d/hashicorp.list

RUN apt update
RUN apt install -y -qq \
    terraform

# Create ubuntu user
ENV USERNAME=ubuntu
ENV USER_UID=1001
ENV USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
RUN chown --recursive $USERNAME:$USERNAME /home/$USERNAME

WORKDIR /home/$USERNAME

ENTRYPOINT ["/opt/box/entrypoint.sh"]
