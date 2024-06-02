FROM nginx:1.26.0

# Update packages to download Datadog NGINX Module 
RUN apt-get update 
RUN apt-get install -y wget tar curl jq

# Download Datadog NGINX Module
COPY datadog-module.sh datadog-module.sh 
RUN chmod +x datadog-module.sh
RUN ./datadog-module.sh 1.26.0 

RUN rm datadog-module.sh
