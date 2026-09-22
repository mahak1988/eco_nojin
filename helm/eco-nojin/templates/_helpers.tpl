{{- define "eco-nojin.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "eco-nojin.fullname" -}}
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

{{- define "eco-nojin.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "eco-nojin.selectorLabels" . }}
{{- end }}

{{- define "eco-nojin.selectorLabels" -}}
app.kubernetes.io/name: {{ include "eco-nojin.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "eco-nojin.namespace" -}}
{{- .Values.global.namespace | default .Release.Namespace }}
{{- end }}

{{- define "eco-nojin.imagePullSecrets" -}}
{{- if .Values.global.imagePullSecrets }}
{{- toYaml .Values.global.imagePullSecrets | nindent 4 }}
{{- end }}
{{- end }}

{{- define "eco-nojin.storageClass" -}}
{{- .Values.global.storageClass | default "gp3" }}
{{- end }}

{{- define "eco-nojin.domain" -}}
{{- .Values.global.domain | default "eco-nojin.org" }}
{{- end }}

{{- define "eco-nojin.tls.enabled" -}}
{{- .Values.global.tls.enabled | default true }}
{{- end }}

{{- define "eco-nojin.tls.clusterIssuer" -}}
{{- .Values.global.tls.clusterIssuer | default "letsencrypt-prod" }}
{{- end }}