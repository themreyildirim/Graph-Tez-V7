# Pure identity validation. No HTTP, inference, download or file writes.
function Assert-WP12GemmaIdentity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$ModelRoot,
        [Parameter(Mandatory=$true)][string]$ApiDigest
    )
    $expectedWrapper = 'sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16'
    $expectedApi = 'sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c'
    $canonicalApi = $ApiDigest.ToLowerInvariant()
    if (-not $canonicalApi.StartsWith('sha256:')) { $canonicalApi = 'sha256:' + $canonicalApi }
    if ($canonicalApi -cne $expectedApi) { throw 'MODEL_DIGEST_MISMATCH: exact approved API/source manifest required' }
    $wrapperPath = Join-Path $ModelRoot 'manifests\registry.ollama.ai\library\gemma3\1b-it-q4_K_M'
    if ((Get-Item -LiteralPath $wrapperPath).Length -gt 1048576) { throw 'LOCAL_MANIFEST_SIZE_UNEXPECTED' }
    $wrapperHash = 'sha256:' + (Get-FileHash -LiteralPath $wrapperPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($wrapperHash -cne $expectedWrapper) { throw 'LOCAL_WRAPPER_SHA256_MISMATCH' }
    $wrapper = Get-Content -LiteralPath $wrapperPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $links = @($wrapper.layers | Where-Object { $_.mediaType -ceq 'application/vnd.docker.distribution.manifest.v2+json' })
    if ($links.Count -ne 1 -or $links[0].digest -cne $expectedApi) { throw 'SOURCE_MANIFEST_LINK_MISMATCH' }
    $sourcePath = Join-Path $ModelRoot ('blobs\' + $expectedApi.Replace(':','-'))
    if ((Get-Item -LiteralPath $sourcePath).Length -gt 1048576) { throw 'SOURCE_MANIFEST_SIZE_UNEXPECTED' }
    $sourceHash = 'sha256:' + (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sourceHash -cne $expectedApi) { throw 'SOURCE_MANIFEST_SHA256_MISMATCH' }
    $source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (($wrapper.config | ConvertTo-Json -Depth 20 -Compress) -cne ($source.config | ConvertTo-Json -Depth 20 -Compress)) {
        throw 'MODEL_CONFIG_REFERENCE_MISMATCH'
    }
    $wrapperLayers = @($wrapper.layers | Where-Object { $_.mediaType -cne 'application/vnd.docker.distribution.manifest.v2+json' })
    $sourceLayers = @($source.layers)
    if ($wrapperLayers.Count -ne $sourceLayers.Count) { throw 'MODEL_LAYER_REFERENCE_COUNT_MISMATCH' }
    for ($i=0; $i -lt $sourceLayers.Count; $i++) {
        if (($wrapperLayers[$i] | ConvertTo-Json -Depth 20 -Compress) -cne ($sourceLayers[$i] | ConvertTo-Json -Depth 20 -Compress)) {
            throw 'MODEL_LAYER_REFERENCE_MISMATCH'
        }
    }
    return [ordered]@{
        identity_binding_version = 'WP12-gemma-api-source-v1'
        observed_API_model_digest = $canonicalApi
        expected_API_model_digest = $expectedApi
        local_wrapper_manifest_file_sha256 = $wrapperHash
        source_manifest_file_sha256 = $sourceHash
        config_and_layer_references_equal = $true
        local_wrapper_path = $wrapperPath
        source_manifest_path = $sourcePath
        hashed_files = @('local_wrapper_manifest','source_manifest')
        weight_bytes_rehashed = $false
        identity_binding_valid = $true
    }
}
