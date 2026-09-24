"""
Production Deployment Infrastructure
=====================================

Provides:
- Kubernetes deployment manifests
- Helm charts for Eco Nojin services
- Horizontal Pod Autoscaler (HPA) configurations
- Service mesh (Istio/Linkerd) integration
- Monitoring stack (Prometheus, Grafana, Alertmanager)
- Logging stack (Loki, Promtail, Grafana)
- Distributed tracing (Tempo/Jaeger)
- CI/CD pipeline integration
- Disaster recovery and backup
- Multi-region deployment
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    """Configuration for Kubernetes deployment."""

    namespace: str = "eco-nojin"
    replicas: int = 3
    image: str = "ghcr.io/eco-nojin/api-gateway:latest"
    image_pull_policy: str = "Always"
    resources: dict[str, str] = field(
        default_factory=lambda: {
            "requests": {"cpu": "500m", "memory": "1Gi"},
            "limits": {"cpu": "2000m", "memory": "4Gi"},
        }
    )
    env_vars: dict[str, str] = field(default_factory=dict)
    secrets: list[str] = field(default_factory=list)
    config_maps: list[str] = field(default_factory=list)
    ports: list[int] = field(default_factory=lambda: [8000])
    health_check_path: str = "/health/live"
    readiness_path: str = "/health/ready"
    liveness_probe: dict = field(
        default_factory=lambda: {
            "initialDelaySeconds": 30,
            "periodSeconds": 10,
            "timeoutSeconds": 5,
            "failureThreshold": 3,
        }
    )
    readiness_probe: dict = field(
        default_factory=lambda: {
            "initialDelaySeconds": 10,
            "periodSeconds": 5,
            "timeoutSeconds": 3,
            "failureThreshold": 3,
        }
    )


class KubernetesManifestGenerator:
    """Generate Kubernetes manifests for Eco Nojin services."""

    def __init__(self, config: DeploymentConfig):
        self.config = config

    def generate_deployment(self) -> dict[str, Any]:
        """Generate Deployment manifest."""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "api-gateway",
                "namespace": self.config.namespace,
                "labels": {
                    "app": "api-gateway",
                    "version": "v1",
                    "component": "backend",
                },
            },
            "spec": {
                "replicas": self.config.replicas,
                "selector": {
                    "matchLabels": {
                        "app": "api-gateway",
                    },
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "api-gateway",
                            "version": "v1",
                        },
                        "annotations": {
                            "prometheus.io/scrape": "true",
                            "prometheus.io/port": "8000",
                            "prometheus.io/path": "/metrics",
                        },
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "api-gateway",
                                "image": self.config.image,
                                "imagePullPolicy": self.config.image_pull_policy,
                                "ports": [
                                    {"containerPort": p, "name": f"http-{p}"}
                                    for p in self.config.ports
                                ],
                                "resources": self.config.resources,
                                "env": [
                                    {"name": k, "value": v} for k, v in self.config.env_vars.items()
                                ],
                                "envFrom": [{"secretRef": {"name": s}} for s in self.config.secrets]
                                + [{"configMapRef": {"name": c}} for c in self.config.config_maps],
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": self.config.health_check_path,
                                        "port": self.config.ports[0],
                                    },
                                    **self.config.liveness_probe,
                                },
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": self.config.readiness_path,
                                        "port": self.config.ports[0],
                                    },
                                    **self.config.readiness_probe,
                                },
                            }
                        ],
                        "serviceAccountName": "api-gateway",
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 1000,
                            "fsGroup": 1000,
                        },
                    },
                },
            },
        }

    def generate_service(self) -> dict[str, Any]:
        """Generate Service manifest."""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "api-gateway",
                "namespace": self.config.namespace,
                "labels": {
                    "app": "api-gateway",
                },
                "annotations": {
                    "service.beta.kubernetes.io/aws-load-balancer-type": "nlb",
                },
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": 80,
                        "targetPort": self.config.ports[0],
                        "protocol": "TCP",
                        "name": "http",
                    }
                ],
                "selector": {
                    "app": "api-gateway",
                },
            },
        }

    def generate_hpa(self) -> dict[str, Any]:
        """Generate HorizontalPodAutoscaler manifest."""
        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": "api-gateway-hpa",
                "namespace": self.config.namespace,
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": "api-gateway",
                },
                "minReplicas": 3,
                "maxReplicas": 50,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": 70,
                            },
                        },
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": 80,
                            },
                        },
                    },
                    {
                        "type": "Pods",
                        "pods": {
                            "metric": {
                                "name": "http_requests_per_second",
                            },
                            "target": {
                                "type": "AverageValue",
                                "averageValue": "1000",
                            },
                        },
                    },
                ],
                "behavior": {
                    "scaleDown": {
                        "stabilizationWindowSeconds": 300,
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 10,
                                "periodSeconds": 60,
                            }
                        ],
                    },
                    "scaleUp": {
                        "stabilizationWindowSeconds": 60,
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 100,
                                "periodSeconds": 30,
                            },
                            {
                                "type": "Pods",
                                "value": 4,
                                "periodSeconds": 30,
                            },
                        ],
                        "selectPolicy": "Max",
                    },
                },
            },
        }

    def generate_pdb(self) -> dict[str, Any]:
        """Generate PodDisruptionBudget manifest."""
        return {
            "apiVersion": "policy/v1",
            "kind": "PodDisruptionBudget",
            "metadata": {
                "name": "api-gateway-pdb",
                "namespace": self.config.namespace,
            },
            "spec": {
                "minAvailable": "50%",
                "selector": {
                    "matchLabels": {
                        "app": "api-gateway",
                    },
                },
            },
        }

    def generate_network_policy(self) -> dict[str, Any]:
        """Generate NetworkPolicy for service mesh."""
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": "api-gateway-netpol",
                "namespace": self.config.namespace,
            },
            "spec": {
                "podSelector": {
                    "matchLabels": {
                        "app": "api-gateway",
                    },
                },
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [
                    {
                        "from": [
                            {"namespaceSelector": {"matchLabels": {"name": "ingress-nginx"}}},
                            {"podSelector": {"matchLabels": {"app": "frontend"}}},
                        ],
                        "ports": [{"protocol": "TCP", "port": p} for p in self.config.ports],
                    },
                ],
                "egress": [
                    {
                        "to": [],
                        "ports": [{"protocol": "TCP", "port": 53}, {"protocol": "UDP", "port": 53}],
                    },  # DNS
                    {
                        "to": [{"namespaceSelector": {"matchLabels": {"name": "monitoring"}}}],
                        "ports": [{"protocol": "TCP", "port": 9090}],
                    },  # Prometheus
                    {
                        "to": [{"namespaceSelector": {}}],
                        "ports": [{"protocol": "TCP", "port": 5432}],
                    },  # PostgreSQL
                    {
                        "to": [{"namespaceSelector": {}}],
                        "ports": [{"protocol": "TCP", "port": 6379}],
                    },  # Redis
                ],
            },
        }

    def generate_all(self, output_dir: Path) -> list[Path]:
        """Generate all manifests to directory."""
        output_dir.mkdir(parents=True, exist_ok=True)

        manifests = {
            "deployment.yaml": self.generate_deployment(),
            "service.yaml": self.generate_service(),
            "hpa.yaml": self.generate_hpa(),
            "pdb.yaml": self.generate_pdb(),
            "network-policy.yaml": self.generate_network_policy(),
        }

        paths = []
        for filename, manifest in manifests.items():
            path = output_dir / filename
            path.write_text(yaml.dump(manifest, default_flow_style=False, sort_keys=False))
            paths.append(path)
            logger.info(f"Generated {path}")

        return paths


class HelmChartGenerator:
    """Generate Helm charts for Eco Nojin."""

    def __init__(self, chart_name: str, version: str, app_version: str):
        self.chart_name = chart_name
        self.version = version
        self.app_version = app_version

    def generate_chart_yaml(self) -> dict[str, Any]:
        return {
            "apiVersion": "v2",
            "name": self.chart_name,
            "description": "Eco Nojin API Gateway Helm Chart",
            "type": "application",
            "version": self.version,
            "appVersion": self.app_version,
            "keywords": ["eco-nojin", "agriculture", "api", "gateway"],
            "maintainers": [
                {
                    "name": "Eco Nojin Team",
                    "email": "team@eco-nojin.org",
                }
            ],
        }

    def generate_values_yaml(self) -> dict[str, Any]:
        return {
            "global": {
                "namespace": "eco-nojin",
                "imageRegistry": "ghcr.io",
                "imagePullSecrets": ["ghcr-credentials"],
            },
            "api-gateway": {
                "replicas": 3,
                "image": {
                    "repository": "eco-nojin/api-gateway",
                    "tag": "latest",
                    "pullPolicy": "Always",
                },
                "resources": {
                    "requests": {"cpu": "500m", "memory": "1Gi"},
                    "limits": {"cpu": "2000m", "memory": "4Gi"},
                },
                "autoscaling": {
                    "enabled": True,
                    "minReplicas": 3,
                    "maxReplicas": 50,
                    "targetCPUUtilization": 70,
                    "targetMemoryUtilization": 80,
                },
                "service": {
                    "type": "ClusterIP",
                    "port": 80,
                },
                "ingress": {
                    "enabled": True,
                    "className": "nginx",
                    "annotations": {
                        "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                        "nginx.ingress.kubernetes.io/rate-limit": "100",
                    },
                    "hosts": [
                        {
                            "host": "api.eco-nojin.org",
                            "paths": [{"path": "/", "pathType": "Prefix"}],
                        }
                    ],
                    "tls": [
                        {
                            "secretName": "api-gateway-tls",
                            "hosts": ["api.eco-nojin.org"],
                        }
                    ],
                },
                "config": {
                    "environment": "production",
                    "logLevel": "info",
                    "redis": {"enabled": True, "host": "redis-master"},
                    "database": {"host": "postgresql", "port": 5432},
                },
            },
            "redis": {
                "enabled": True,
                "architecture": "replication",
                "auth": {"enabled": True, "existingSecret": "redis-auth"},
                "master": {"persistence": {"enabled": True, "size": "10Gi"}},
                "replica": {"replicaCount": 2, "persistence": {"enabled": True, "size": "10Gi"}},
            },
            "postgresql": {
                "enabled": True,
                "auth": {"enabled": True, "existingSecret": "postgresql-auth"},
                "primary": {"persistence": {"enabled": True, "size": "50Gi"}},
                "readReplicas": {"replicaCount": 2},
            },
            "monitoring": {
                "enabled": True,
                "prometheus": {
                    "enabled": True,
                    "serviceMonitors": [
                        {"namespace": "eco-nojin", "selector": {"app": "api-gateway"}}
                    ],
                },
                "grafana": {
                    "enabled": True,
                    "dashboards": {
                        "api-gateway": "dashboards/api-gateway.json",
                    },
                },
                "alertmanager": {
                    "enabled": True,
                    "config": {
                        "receivers": [{"name": "slack", "slack_configs": [{"channel": "#alerts"}]}]
                    },
                },
            },
            "logging": {
                "enabled": True,
                "loki": {"enabled": True},
                "promtail": {"enabled": True},
            },
            "tracing": {
                "enabled": True,
                "tempo": {"enabled": True},
            },
        }

    def generate_templates(self) -> dict[str, str]:
        """Generate template files."""
        return {
            "deployment.yaml": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "api-gateway.fullname" . }}
  namespace: {{ .Values.global.namespace }}
  labels:
    {{- include "api-gateway.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.api-gateway.replicas }}
  selector:
    matchLabels:
      {{- include "api-gateway.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "api-gateway.selectorLabels" . | nindent 8 }}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{{ .Values.api-gateway.service.port }}"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: {{ include "api-gateway.serviceAccountName" . }}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.global.imageRegistry }}/{{ .Values.api-gateway.image.repository }}:{{ .Values.api-gateway.image.tag }}"
          imagePullPolicy: {{ .Values.api-gateway.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.api-gateway.service.port }}
              protocol: TCP
          resources:
            {{- toYaml .Values.api-gateway.resources | nindent 12 }}
          env:
            - name: ENVIRONMENT
              value: {{ .Values.api-gateway.config.environment | quote }}
            - name: LOG_LEVEL
              value: {{ .Values.api-gateway.config.logLevel | quote }}
          livenessProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
          envFrom:
            - secretRef:
                name: {{ include "api-gateway.fullname" . }}-secrets
            - configMapRef:
                name: {{ include "api-gateway.fullname" . }}-config
""",
            "service.yaml": """apiVersion: v1
kind: Service
metadata:
  name: {{ include "api-gateway.fullname" . }}
  namespace: {{ .Values.global.namespace }}
  labels:
    {{- include "api-gateway.labels" . | nindent 4 }}
spec:
  type: {{ .Values.api-gateway.service.type }}
  ports:
    - port: {{ .Values.api-gateway.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "api-gateway.selectorLabels" . | nindent 4 }}
""",
            "hpa.yaml": """{{- if .Values.api-gateway.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "api-gateway.fullname" . }}-hpa
  namespace: {{ .Values.global.namespace }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "api-gateway.fullname" . }}
  minReplicas: {{ .Values.api-gateway.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.api-gateway.autoscaling.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.api-gateway.autoscaling.targetCPUUtilization }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.api-gateway.autoscaling.targetMemoryUtilization }}
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 30
{{- end }}
""",
            "_helpers.tpl": """{{- define "api-gateway.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "api-gateway.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "api-gateway.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "api-gateway.selectorLabels" . }}
{{- end }}

{{- define "api-gateway.selectorLabels" -}}
app.kubernetes.io/name: {{ include "api-gateway.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "api-gateway.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "api-gateway.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- "default" }}
{{- end }}
{{- end }}
""",
        }

    def generate_chart(self, output_dir: Path) -> list[Path]:
        """Generate complete Helm chart."""
        chart_dir = output_dir / self.chart_name
        chart_dir.mkdir(parents=True, exist_ok=True)
        templates_dir = chart_dir / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        # Chart.yaml
        (chart_dir / "Chart.yaml").write_text(
            yaml.dump(self.generate_chart_yaml(), default_flow_style=False)
        )

        # values.yaml
        (chart_dir / "values.yaml").write_text(
            yaml.dump(self.generate_values_yaml(), default_flow_style=False)
        )

        # Templates
        templates = self.generate_templates()
        for filename, content in templates.items():
            (templates_dir / filename).write_text(content)

        logger.info(f"Generated Helm chart: {chart_dir}")
        return [chart_dir]


class MonitoringStack:
    """Generate monitoring stack configurations."""

    @staticmethod
    def generate_prometheus_rules() -> dict[str, Any]:
        return {
            "groups": [
                {
                    "name": "api-gateway-alerts",
                    "rules": [
                        {
                            "alert": "HighErrorRate",
                            "expr": 'rate(http_requests_total{status=~"5.."}[5m]) > 0.05',
                            "for": "2m",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "High error rate on {{ $labels.instance }}",
                                "description": "{{ $value }}% of requests are failing",
                            },
                        },
                        {
                            "alert": "HighLatency",
                            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2",
                            "for": "5m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "High P99 latency on {{ $labels.instance }}",
                                "description": "P99 latency is {{ $value }}s",
                            },
                        },
                        {
                            "alert": "HighMemoryUsage",
                            "expr": "container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.85",
                            "for": "10m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "High memory usage on {{ $labels.pod }}",
                                "description": "Memory usage is {{ $value | humanizePercentage }}",
                            },
                        },
                        {
                            "alert": "PodNotReady",
                            "expr": 'kube_pod_status_ready{condition="true"} == 0',
                            "for": "5m",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "Pod {{ $labels.pod }} not ready",
                                "description": "Pod has been not ready for 5 minutes",
                            },
                        },
                        {
                            "alert": "DataFabricationDetected",
                            "expr": "increase(data_fabrication_total[1h]) > 0",
                            "for": "0m",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "Data fabrication detected!",
                                "description": "Simulated data presented as real without disclosure",
                            },
                        },
                    ],
                }
            ]
        }

    @staticmethod
    def generate_grafana_dashboard() -> dict[str, Any]:
        return {
            "dashboard": {
                "title": "Eco Nojin API Gateway",
                "uid": "eco-nojin-api",
                "tags": ["eco-nojin", "api", "gateway"],
                "timezone": "utc",
                "panels": [
                    {
                        "title": "Request Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "sum(rate(http_requests_total[5m])) by (method, status)",
                                "legendFormat": "{{method}} {{status}}",
                            }
                        ],
                    },
                    {
                        "title": "Latency (P50, P95, P99)",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                                "legendFormat": "P50",
                            },
                            {
                                "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                                "legendFormat": "P95",
                            },
                            {
                                "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                                "legendFormat": "P99",
                            },
                        ],
                    },
                    {
                        "title": "Cache Hit Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "sum(rate(cache_hits_total[5m])) / sum(rate(cache_requests_total[5m]))",
                                "legendFormat": "Hit Rate",
                            }
                        ],
                    },
                    {
                        "title": "Data Source Breakdown",
                        "type": "piechart",
                        "targets": [
                            {
                                "expr": "sum(increase(data_source_total[1h])) by (source)",
                                "legendFormat": "{{source}}",
                            }
                        ],
                    },
                    {
                        "title": "Scientific Model Executions",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "sum(rate(model_executions_total[5m])) by (model, status)",
                                "legendFormat": "{{model}} {{status}}",
                            }
                        ],
                    },
                ],
            }
        }

    @staticmethod
    def generate_service_monitor() -> dict[str, Any]:
        return {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": "api-gateway-monitor",
                "namespace": "eco-nojin",
                "labels": {"release": "prometheus"},
            },
            "spec": {
                "selector": {
                    "matchLabels": {"app": "api-gateway"},
                },
                "endpoints": [
                    {
                        "port": "http",
                        "path": "/metrics",
                        "interval": "30s",
                    }
                ],
            },
        }


class DisasterRecovery:
    """Disaster recovery and backup configurations."""

    @staticmethod
    def generate_velero_backup() -> dict[str, Any]:
        return {
            "apiVersion": "velero.io/v1",
            "kind": "Backup",
            "metadata": {
                "name": "eco-nojin-backup-{{ .Release.Time }}",
                "namespace": "velero",
            },
            "spec": {
                "includedNamespaces": ["eco-nojin", "monitoring", "logging"],
                "labelSelector": {
                    "matchLabels": {"app.kubernetes.io/managed-by": "Helm"},
                },
                "snapshotVolumes": True,
                "ttl": "720h",
                "storageLocation": "default",
            },
        }

    @staticmethod
    def generate_restore_plan() -> dict[str, Any]:
        return {
            "apiVersion": "velero.io/v1",
            "kind": "Restore",
            "metadata": {
                "name": "eco-nojin-restore-{{ .Release.Time }}",
                "namespace": "velero",
            },
            "spec": {
                "backupName": "eco-nojin-backup-latest",
                "includedNamespaces": ["eco-nojin"],
                "restorePVs": True,
            },
        }


class MultiRegionDeployment:
    """Multi-region deployment configuration."""

    REGIONS = {
        "us-east-1": {"primary": True, "replicas": 5},
        "eu-west-1": {"primary": False, "replicas": 3},
        "ap-southeast-1": {"primary": False, "replicas": 2},
    }

    @staticmethod
    def generate_global_load_balancer() -> dict[str, Any]:
        return {
            "apiVersion": "networking.gke.io/v1",
            "kind": "GlobalLoadBalancer",
            "metadata": {
                "name": "eco-nojin-global-lb",
                "namespace": "eco-nojin",
            },
            "spec": {
                "frontend": {
                    "ports": [80, 443],
                    "sslPolicy": "modern",
                },
                "backends": [
                    {
                        "region": region,
                        "service": "api-gateway",
                        "weight": config["replicas"],
                        "healthCheck": {"path": "/health/ready", "interval": "10s"},
                    }
                    for region, config in MultiRegionDeployment.REGIONS.items()
                ],
                "failover": {
                    "enabled": True,
                    "threshold": 3,
                    "interval": "30s",
                },
            },
        }


# Export main classes
__all__ = [
    "DeploymentConfig",
    "DisasterRecovery",
    "HelmChartGenerator",
    "KubernetesManifestGenerator",
    "MonitoringStack",
    "MultiRegionDeployment",
]
