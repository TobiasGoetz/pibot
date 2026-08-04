{{- define "pibot.name" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "pibot.valkey.host" -}}
{{- printf "%s-valkey" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "pibot.valkey.authSecretName" -}}
{{- printf "%s-valkey-users" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "pibot.valkey.uri" -}}
{{- $host := include "pibot.valkey.host" . -}}
{{- $port := (.Values.valkey.service).port | default 6379 -}}
valkey://{{ $host }}:{{ $port }}/0
{{- end -}}

{{/*
  Returns JSON {"password","uri"} for in-cluster Valkey auth.
  Reuses an existing Secret password across upgrades (lookup).
*/}}
{{- define "pibot.valkey.authCredentials" -}}
{{- $secretName := include "pibot.valkey.authSecretName" . -}}
{{- $host := include "pibot.valkey.host" . -}}
{{- $port := (.Values.valkey.service).port | default 6379 -}}
{{- $existing := lookup "v1" "Secret" .Release.Namespace $secretName -}}
{{- $password := randAlphaNum 32 -}}
{{- if and $existing $existing.data (index $existing.data "default") -}}
{{- $password = index $existing.data "default" | b64dec -}}
{{- end -}}
{{- dict
  "password" $password
  "uri" (printf "valkey://:%s@%s:%v/0" $password $host $port)
  | toJson -}}
{{- end -}}
