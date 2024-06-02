## Overview

A dummy webapp, where users click a button and things happen. Instrumented with Datadog for Metrics, RUM, Logs and Traces.

![app overview](/app.png)

**NGINX** proxies all incoming HTTP requests.

**Flask** handles cookie-based authentication, web page template rendering and some back-end plumbery.

Clicking the big button increments a counter for that user, stored in **Redis**. But it may fail, and run take 100s of milliseconds to run.

The webapp comes with a basic collection of Datadog Monitors and Dashboards, deployable through a wrapped and dockerized [Terraform CLI](https://developer.hashicorp.com/terraform/cli/commands). 


## How To 

### Setup

1. install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

2. Create a [Datadog Org](https://app.datadoghq.com/signup), and update `DD_SITE` in the `.env` file (see [documentation](https://docs.datadoghq.com/getting_started/site/#access-the-datadog-site) for reference)

3. Get an [API key](https://app.datadoghq.com/organization-settings/api-keys), an [APP key](https://app.datadoghq.com/organization-settings/application-keys) as well as a [Client Token](https://app.datadoghq.com/organization-settings/client-tokens), and update `DD_API_KEY`, `DD_APP_KEY` and `DD_CLIENT_TOKEN` accordingly in the `.env` file.

4. Create a [Datadog RUM Application](https://app.datadoghq.com/rum/application/create) for Javascript, and update `DD_APPLICATION_ID` in the `.env` file.

5. Update the `NOTIF_EMAIL` in the `.env` file with an email where to send datadog notifications (you can use the email you used for your Datadog Account).


### Run

Run `docker compose up` from a terminal at the root of the `redis-sandbox` folder:

```bash
$ docker compose up   
[+] Running 3/3
 ⠿ Container redis    Created      10.0s
 ⠿ Container datadog  Created      10.0s
 ⠿ Container flask    Created      10.0s
```

Ctrl-C would kill the app.


### Play

From a web browser:
* Connect to `http://localhost:8000`. You'll be logged in as a random user `abcd1234@sandbox.com`.
* Alternatively, log in as any user injecting their user_id in the URL (yay... security): `http://localhost:8000/?user_id=john.doe`.


Your cookie expires when you close your browser.


### Terraform

Terraform runs within a docker container, with working directory properly wired to the terraform configuration (see [--chdir option](https://developer.hashicorp.com/terraform/cli/commands#switching-working-directory-with-chdir) )

``` bash
$ ./terraform.sh init
Initializing the backend...
[...]
Terraform has been successfully initialized!
```

``` bash
$ ./terraform.sh apply
[...]
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.
```

``` bash
$ ./terraform.sh output monitor_tags
[
  "env:sandbox",
  "owner:terraform"
]
```

``` bash
$ ./terraform.sh destroy
[...]
Destroy complete! Resources: 3 destroyed.
```

### Observe

* [Service Catalog](https://app.datadoghq.com/metric/summary?tags=env%3Asandbox)
* [Metrics](https://app.datadoghq.com/metric/summary)
* [Logs](https://app.datadoghq.com/logs?query=env%3Asandbox)
* [Trace](https://app.datadoghq.com/apm/traces?query=%40_top_level%3A1%20env%3Asandbox)
* [RUM Events](https://app.datadoghq.com/rum/explorer?query=%40type%3Asession)

... [Dashboards](https://app.datadoghq.com/dashboard/lists), [Monitors](https://app.datadoghq.com/monitors#recommended?q=integration:Redis&p=1)
