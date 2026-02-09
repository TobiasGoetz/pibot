{{- define "pibot.name" -}}
{{- printf "%s-pibot" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
