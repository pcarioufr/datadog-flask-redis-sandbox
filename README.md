# Overview

A webapp chat interface for Ollama LLM, whose primary intent is to Dogfood Datadog.

![app overview](/app.png)



# Get LLM-2000 up and running

1. install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

2. Install [Ollama](https://ollama.ai/download), and download a model of your choice (suggested: [`mistral`](https://ollama.com/library/mistral)). Update the [`.env/ollama.env`](.env/ollame.env) file:

    - Update `OLLAMA_MODEL` to match one of your downloaded Ollama model (run `ollama ps` to see which models are running).
    - You may use default values for the inference parameters, and/or update later.

3. Create a [Datadog Org](https://app.datadoghq.com/signup), and update the [`.env/datadog.env`](.env/datadog.env) file:

    - Update `DD_SITE`. See [documentation](https://docs.datadoghq.com/getting_started/site/#access-the-datadog-site) for reference.
    - Get an [API key](https://app.datadoghq.com/organization-settings/api-keys), an [APP key](https://app.datadoghq.com/organization-settings/application-keys), and update `DD_API_KEY`, `DD_APP_KEY` accordingly.
    - Update the `NOTIF_EMAIL` with an email where to send datadog notifications (you can use the email you used for your Datadog Account).

4. Run `./terraform.sh init` and then `./terraform.sh apply` from a terminal at the root of the `llm-2000` folder, to create all Datadog resources and update environment variables in the [.env/](.env) folder with a bunch of new IDs and secrets: 
    - a RUM Application and a Client Token
    - a Synthetics Private Location
    - Dashboards, Monitors, etc.

``` bash
$ ./terraform.sh init
Initializing the backend...
[...]
Terraform has been successfully initialized!

$ ./terraform.sh apply
[...]
Apply complete! Resources: 8 added, 0 changed, 0 destroyed.
```

5. Run `docker compose up` from a terminal at the root of the `llm-2000` folder:

    - **nginx** proxies all incoming HTTP requests.
    - **flask** handles cookie-based authentication, web page template rendering, and chat functionality with an ollama integration.
    - **redis** stores chat history for each user.
    - **datadog** is the datadog agent.
    - **synthetics** is the private location that runs synthetic tests.


```bash
$ docker compose up   
[+] Running 5/5
 ✔ Container nginx        Started    0.3s 
 ✔ Container datadog      Started    0.3s 
 ✔ Container redis        Started    0.3s
 ✔ Container synthetics   Started    0.3s
 ✔ Container flask        Started    0.3s
```


# Usage

## Web app usage
From a web browser:

Connect to `http://localhost:8000`. You'll be logged in as a random user `abcd1234@sandbox.com`. Alternatively, log in as any user injecting their user_id in the URL (yay... security): `http://localhost:8000/?user_id=john.doe`.

Your cookie expires when you close your browser.

## API Usage

The application provides a programmatic API endpoint for direct chat interactions. The system prompt is optional:

```bash

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is your favorite color?",
    "system_prompt": "You must respond to all questions with text in CAPITAL LETTERS only."
  }'
```

## Terraform Usage

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
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
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
Destroy complete! Resources: 2 destroyed.
```


# Datadog

## Observe

* [Service Catalog](https://app.datadoghq.com/metric/summary?tags=env%3Asandbox)
* [Metrics](https://app.datadoghq.com/metric/summary)
* [Logs](https://app.datadoghq.com/logs?query=env%3Asandbox)
* [Trace](https://app.datadoghq.com/apm/traces?query=%40_top_level%3A1%20env%3Asandbox)
* [RUM Events](https://app.datadoghq.com/rum/explorer?query=%40type%3Asession)

... [Dashboards](https://app.datadoghq.com/dashboard/lists), [Monitors](https://app.datadoghq.com/monitors#recommended?q=integration:Redis&p=1)


# License

MIT

