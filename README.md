## Redis Sandbox

A dummy Flask-Redis webapp to count stuff, instrumented with Datadog for Metrics, Logs and Traces.


## Redis Sandbox How To 

### Setup

1. install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Create a [Datadog Org](https://app.datadoghq.com/signup) and get an [API key](https://app.datadoghq.com/organization-settings/api-keys)
3. In the `.env`file, update
    * `DD_API_KEY` with the aforementioned API key
    * `DD_SITE` with the Datadog site you use - see our [user doc](https://docs.datadoghq.com/getting_started/site/#access-the-datadog-site) for reference 


From a terminal at the root of the `redis-sandbox` folder:

```bash
% docker compose up   
[+] Running 3/3
 ⠿ Container redis    Created      10.0s
 ⠿ Container datadog  Created      10.0s
 ⠿ Container flask    Created      10.0s
```

Ctrl-C would kill the app

### Run

From a(nother) terminal at the root of the `redis-sandbox` folder:


```bash
curl "http://localhost:8000"
<p>Hello, World!</p>%    
```

```bash
curl -XPOST "http://localhost:8000/count/hello"
{"count":"1","key":"hello"}
```


### Observe

* [Logs](https://app.datadoghq.com/logs?query=env%3Asandbox)
* [Trace](https://app.datadoghq.com/apm/traces?query=%40_top_level%3A1%20env%3Asandbox)
* [Service Catalog](https://app.datadoghq.com/services?env=sandbox)

... [Dashboards](https://app.datadoghq.com/dashboard/lists), [Monitors](https://app.datadoghq.com/monitors#recommended?q=integration:Redis&p=1)

