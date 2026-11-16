param([Parameter(Mandatory=$true)][string]$Image)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $project
$env:KUBECONFIG = Join-Path $project 'infra/.terraform/kubeconfig'
New-Item -ItemType Directory -Force loadtest/resultados | Out-Null
$profiles = @(
    @{Id='rampa-final'; Users='1000'; Rate='3.33'; Duration='10m'; Class='EpsIncPlayerUser'},
    @{Id='pico'; Users='1000'; Rate='66.6'; Duration='5m'; Class='EpsIncPlayerUser'},
    @{Id='espectadores'; Users='500'; Rate='25'; Duration='6m'; Class='EpsIncSpectatorUser'}
)
foreach ($profile in $profiles) {
    $id = $profile.Id
    if (Test-Path "loadtest/resultados/$id-report-complete.txt") { continue }
    $existing = kubectl get job "epsinc-locust-$id" --ignore-not-found -o name
    if (-not $existing) {
        kubectl scale deployment/epsinc-locust-workers --replicas=0
        kubectl wait --for=delete pod -l app=epsinc-locust,role=worker --timeout=120s
        if ($LASTEXITCODE -ne 0) { throw 'Previous workers did not stop' }
        kubectl create configmap epsinc-locust --from-file=locustfile.py=loadtest/locustfile.py --dry-run=client -o yaml | kubectl apply -f -
        if ($LASTEXITCODE -ne 0) { throw 'Cannot configure Locust' }
        $job = (Get-Content loadtest/k8s/master-job.yaml -Raw).Replace('__LOCUST_IMAGE__',$Image).Replace('__RUN_ID__',$id).Replace('__USERS__',$profile.Users).Replace('__RATE__',$profile.Rate).Replace('__DURATION__',$profile.Duration).Replace('__USER_CLASS__',$profile.Class)
        if ($job.Contains('__')) { throw 'Unresolved job placeholders' }
        $job | kubectl apply -f -
        if ($LASTEXITCODE -ne 0) { throw 'Cannot create master' }
        kubectl scale deployment/epsinc-locust-workers --replicas=8
        kubectl rollout status deployment/epsinc-locust-workers --timeout=180s
        if ($LASTEXITCODE -ne 0) { throw 'Workers did not become ready' }
    }
    $deadline = (Get-Date).AddMinutes(15)
    $jobUid = kubectl get job "epsinc-locust-$id" -o jsonpath='{.metadata.uid}'
    do {
        $pods = kubectl get pods -l "job-name=epsinc-locust-$id" -o json | ConvertFrom-Json
        $pod = ($pods.items | Where-Object { $_.metadata.ownerReferences.uid -contains $jobUid } | Select-Object -First 1).metadata.name
        if (-not $pod) { throw 'No pod owned by the current master Job' }
        $state = kubectl exec $pod -- sh -c 'if test -f /tmp/finished; then echo finished; else echo running; fi'
        if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect master status' }
        $finished = $state -eq 'finished'
        if (-not $finished) {
            if ((Get-Date) -gt $deadline) { throw "Timed out waiting for $id" }
            Start-Sleep -Seconds 10
        }
    } until ($finished)
    foreach ($suffix in @('_stats.csv','_stats_history.csv','_failures.csv','_exceptions.csv','_report.html')) {
        $ErrorActionPreference = 'Continue'
        kubectl cp "${pod}:/tmp/$id$suffix" "loadtest/resultados/$id$suffix"
        $ErrorActionPreference = 'Stop'
        if ($LASTEXITCODE -ne 0) { throw "Cannot preserve $id$suffix" }
    }
    kubectl logs $pod > "loadtest/resultados/$id-console.txt"
    kubectl logs deployment/epsinc-locust-workers --all-pods=true --prefix=true > "loadtest/resultados/$id-workers.txt"
    kubectl exec $pod -- cat /tmp/finished | Set-Content "loadtest/resultados/$id-exit-code.txt"
    Write-Output "Saved $id at $(Get-Date -Format o)"
    Get-Date -Format o | Set-Content "loadtest/resultados/$id-report-complete.txt"
    kubectl delete job "epsinc-locust-$id" --wait=true
}
