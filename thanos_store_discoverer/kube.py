import os
import base64
import json
import logging
from kubernetes import client, config, watch

GROUP = "monitoring.coreos.com"
VERSION = "v1"
PLURAL = "prometheuses"
CLUSTER_DOMAIN = 'cluster.local'
PROMETHEUS_SUBDOMAIN = "prometheus-operated"
STORE_API_PORT = "10901"
KUBERNETES_SECRET="store-api-endpoints"
DISCOVERY_FILENAME="store-api-endpoints.json"
PROMETHEUS_NAMESPACE="monitoring"

class KubeClient:
    def __init__(self, kubeconfig = None):
        try:
            if not kubeconfig:
                config.load_incluster_config()
            else:
                config.load_kube_config(kubeconfig)
        except config.ConfigException:
            config.load_kube_config()
        
        self.client = client.CoreV1Api()
        self.client_crd = client.CustomObjectsApi()

    def list_prometheuses(self, group=GROUP, version=VERSION, plural=PLURAL, resource_version=0, timeout=86400):
        return self.client_crd.list_cluster_custom_object(
            group=group,
            version=version,
            plural=plural,
            resource_version=resource_version, 
            timeout_seconds=timeout, 
            watch=False
        )

    def list_prometheus_operated_services(self, headless_service_name = PROMETHEUS_SUBDOMAIN, cluster_domain = CLUSTER_DOMAIN, ignore_namespace = PROMETHEUS_NAMESPACE):
        res = self.client.list_service_for_all_namespaces(
            field_selector = f"metadata.name={headless_service_name},metadata.namespace!={ignore_namespace}",
            watch=False
        )
        
        return [f"{headless_service_name}.{svc.metadata.namespace}.svc.{cluster_domain}:{STORE_API_PORT}" for svc in res.items]

    def list_thanos_sidecar_endpoints(self, group=GROUP, version=VERSION, plural=PLURAL, resource_version=0, timeout=86400):
        
        prometheus_listing_response = self.list_prometheuses()
        store_api_pod_label_selector = ''

        for prom in prometheus_listing_response['items']:
            if 'thanos' not in prom['spec']:
                store_api_pod_label_selector += f"operator.prometheus.io/name!={prom['metadata']['name']},"
        store_api_pod_label_selector.append('operator.prometheus.io/name') # lastly, make sure to filter for prom pods
        
        store_api_pods = self.client.list_pod_for_all_namespaces(
            label_selector = store_api_pod_label_selector,
            watch=False
        )
        
        return [f"{pod.status.podIP}:{STORE_API_PORT}" for pod in store_api_pods.items]
    
    def reconcile_secret(self, store_api_endpoints, secret_name, secret_namespace):
        # get secret
        secret = self.client.read_namespaced_secret(secret_name, secret_namespace)

        # extract data
        secret_data = base64.b64decode(secret.data[DISCOVERY_FILENAME]).decode('utf-8')
        curr_targets = json.loads(secret_data)[0]['targets']

        # sort then compare
        curr_targets.sort()
        store_api_endpoints.sort()
        if curr_targets == store_api_endpoints:
            logging.info("current targets match discovered")
        else:
            # patch secret
            new_json = [{ 'targets': store_api_endpoints }]

            patch = [{"op": "replace", "path": f"/data/{DISCOVERY_FILENAME}", "value": base64.urlsafe_b64encode(json.dumps(new_json).encode()).decode()}]
            
            resp = self.client.patch_namespaced_secret(
                name=secret_name, namespace=secret_namespace, body=patch
            )
    
    def reconcile(self, store_api_endpoints, secret_name = KUBERNETES_SECRET, secret_namespace = PROMETHEUS_NAMESPACE):
        self.reconcile_secret(store_api_endpoints, secret_name, secret_namespace)
