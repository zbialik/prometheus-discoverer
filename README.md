# prometheus-discoverer

A simple python app that implements [File Service Discovery](https://thanos.io/tip/thanos/service-discovery.md/#file-service-discovery) for Thanos Querier by updating a local JSON file with Prometheus endpoints.

NOTE: if the Namespaces that will host Prometheus `Pods` are well-known, it'd be better to simply use [DNS Service Discovery](https://thanos.io/tip/thanos/service-discovery.md/#dns-service-discovery) against the `prometheus-operated` `Services` created by Prometheus Operator. For example:

```
--store=dnssrv+_grpc._tcp.prometheus-operated.monitoring.svc
```

## Use-Case: Discover StoreAPI Endpoints based on Prometheus Pods in Unknown Namespaces

Run this containerized app as a sidecar to `thanos-query` `Pods` for presenting `StoreAPI` endpoints discovered based from Prometheus `Pods` created in any `Namespace`. 

The thanos-query containers should include the following argument to couple the sidecar:

```
--store.sd-files=<path to file sd>
```

## Pre-Reqs

- Kubernetes
- Prometheus Operator
- Thanos Querier

## Objectives

[ ] discover `StoreAPI` endpoints by finding all `Prometheus` `Pods` in the cluster

