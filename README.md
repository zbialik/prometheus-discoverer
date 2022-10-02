# prometheus-discoverer

A simple python app that implements [File Service Discovery](https://thanos.io/tip/thanos/service-discovery.md/#file-service-discovery) for Thanos Querier by updating a local JSON file with Prometheus endpoints.

NOTE: if the Namespaces that will host Prometheus `Pods` are well-known, it'd be better to simply use [DNS Service Discovery](https://thanos.io/tip/thanos/service-discovery.md/#dns-service-discovery) against the `prometheus-operated` `Services` created by Prometheus Operator. For example:

```
--store=dnssrv+_grpc._tcp.prometheus-operated.monitoring.svc
```

## Pre-Reqs

- Kubernetes
- Prometheus Operator
- Thanos Sidecar Implementation

## Usage

To run:

```bash
usage: prometheus_discoverer [-h] [-s SERVER] [-p PREFIX] [-t TIMEOUT]

optional arguments:
  -h, --help            show this help message and exit
  -t TIMEOUT, --timeout TIMEOUT
                        Kubernetes Watch API timeout in seconds
  -t TIMEOUT, --timeout TIMEOUT
                        Kubernetes Watch API timeout in seconds
```

## Overview

This app monitors Kubernetes `Prometheus` CRD objects via `monitoring.coreos.com/v1` API and will determine Thanos StoreAPI endpoints based on those `Prometheus` objects with a `spec.thanos` declaration

Example:

```yaml
...
spec:
  thanos:
    baseImage: quay.io/thanos/thanos
    version: v0.8.1
...
```

## Use-Case: Discover StoreAPI Endpoints based on Prometheus Pods in Unknown Namespaces

Run this containerized app as a sidecar to `thanos-query` `Pods` for presenting `StoreAPI` endpoints discovered based from Prometheus `Pods` created in any `Namespace`. 

The thanos-query containers should include the following argument to couple the sidecar:

```
--store.sd-files=<path to file sd>
```

## Deployment

### RBAC:

We need permission to read `Prometheus` objects in all `Namespaces`:

```
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: prometheus-discoverer
rules:
- apiGroups: ["monitoring.coreos.com"]
  resources: ["prometheuses"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "list", "watch"]
```
