{{- define "pibot.name" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "pibot.valkey.host" -}}
{{- printf "%s-valkey" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "pibot.valkey.uri" -}}
{{- $host := include "pibot.valkey.host" . -}}
{{- $port := (.Values.valkey.service).port | default 6379 -}}
valkey://{{ $host }}:{{ $port }}/0
{{- end -}}
