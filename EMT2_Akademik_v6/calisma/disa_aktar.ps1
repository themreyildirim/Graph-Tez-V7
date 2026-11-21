# EMT2 v6 raporunu Word ile acar, ALAN KODLARINI gunceller ve PDF uretir.
# Icindekiler, cizelge listesi ve sekil listesi sayfa numaralari burada dolar.
$ErrorActionPreference = 'Stop'
$kok = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$docx = Join-Path $kok 'EMT2_FINAL_REPORT.docx'
$pdf = Join-Path $kok 'EMT2_FINAL_REPORT.pdf'

if (-not (Test-Path $docx)) { throw "Bulunamadi: $docx" }

$app = New-Object -ComObject Word.Application
try {
    $app.Visible = $false
    $app.DisplayAlerts = 0
    $doc = $app.Documents.Open($docx, $false, $false)
    try {
        # Alanlari iki kez guncelle: ilk gecis sayfa akisini degistirir
        foreach ($tur in 1..2) {
            $doc.Fields.Update() | Out-Null
            foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
            $doc.Repaginate()
        }
        $doc.Save()
        $doc.ExportAsFixedFormat($pdf, 17)
        Write-Output ("sayfa: " + $doc.ComputeStatistics(2))
        Write-Output ("kelime: " + $doc.ComputeStatistics(0))
    } finally {
        try { $doc.Close(-1) } catch { Write-Warning 'Word belge kapatilamadi.' }
    }
} finally {
    try { $app.Quit() } catch { Write-Warning 'Word zaten kapandi.' }
}
Write-Output "PDF: $pdf"
