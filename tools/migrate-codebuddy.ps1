# migrate-codebuddy.ps1
# 把 CodeBuddy CN 在 C 盘的大目录迁到 D 盘，并用目录联接（junction）指回去，
# 对 CodeBuddy 完全透明——它仍以为文件在原来的位置。
#
# 用法：
#   1. 完全退出 CodeBuddy CN（任务栏图标也要退出）
#   2. 右键「以管理员身份运行 PowerShell」，执行：
#        Set-ExecutionPolicy -Scope Process Bypass -Force
#        & "E:\FDE\tools\migrate-codebuddy.ps1"
#   3. 看到「全部完成」后，重新打开 CodeBuddy，扩展和登录态应该都在
#
# 中途任何一步失败都会停下并提示，不会留下半成品。

$ErrorActionPreference = 'Stop'
$HomeDir  = "C:\Users\王小喵"
$DestRoot = "D:\CodeBuddyData"

# 待迁移目录：源目录 -> 目标目录（按收益从大到小）
$Targets = @(
    @{ Name = '扩展目录';        Src = "$HomeDir\.codebuddycn\extensions";                          Dst = "$DestRoot\extensions" },
    @{ Name = 'WebStorage';      Src = "$HomeDir\AppData\Roaming\CodeBuddy CN\WebStorage";          Dst = "$DestRoot\WebStorage" },
    @{ Name = 'CrashReport';     Src = "$HomeDir\AppData\Roaming\CodeBuddy CN\CrashReport";         Dst = "$DestRoot\CrashReport" },
    @{ Name = 'CachedData';      Src = "$HomeDir\AppData\Roaming\CodeBuddy CN\CachedData";          Dst = "$DestRoot\CachedData" },
    @{ Name = '扩展安装包缓存';   Src = "$HomeDir\AppData\Roaming\CodeBuddy CN\CachedExtensionVSIXs"; Dst = "$DestRoot\CachedExtensionVSIXs" },
    @{ Name = 'Partitions';      Src = "$HomeDir\AppData\Roaming\CodeBuddy CN\Partitions";          Dst = "$DestRoot\Partitions" },
    @{ Name = '日志';            Src = "$HomeDir\AppData\Roaming\CodeBuddy CN\logs";                Dst = "$DestRoot\logs" },
    @{ Name = 'Cache';           Src = "$HomeDir\AppData\Roaming\CodeBuddy CN\Cache";               Dst = "$DestRoot\Cache" },
    @{ Name = 'GPUCache';        Src = "$HomeDir\AppData\Roaming\CodeBuddy CN\GPUCache";            Dst = "$DestRoot\GPUCache" }
)

function Write-Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }

# ---------- 前置检查 ----------
Write-Host "=" * 62 -ForegroundColor DarkGray
Write-Host " CodeBuddy CN 数据迁移到 D 盘" -ForegroundColor White
Write-Host "=" * 62 -ForegroundColor DarkGray

$proc = Get-Process -Name "CodeBuddy CN" -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "`n[中断] CodeBuddy CN 正在运行（$($proc.Count) 个进程）。" -ForegroundColor Red
    Write-Host "请先完全退出 CodeBuddy（包括右下角托盘图标 → 退出），再重新运行本脚本。" -ForegroundColor Yellow
    Read-Host "按回车退出"
    exit 1
}

$freeD = [math]::Round((Get-PSDrive D).Free/1GB, 1)
Write-Host "`nD 盘剩余: $freeD GB"
if ($freeD -lt 2) {
    Write-Host "[中断] D 盘剩余不足 2 GB，先清理再迁移。" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

if (-not (Test-Path -LiteralPath $DestRoot)) {
    New-Item -ItemType Directory -Path $DestRoot -Force | Out-Null
    Write-Host "已创建目标目录: $DestRoot"
}

# ---------- 逐个迁移 ----------
$moved = @()
foreach ($t in $Targets) {
    Write-Step "$($t.Name)：$($t.Src)"

    if (-not (Test-Path -LiteralPath $t.Src)) {
        Write-Host "  跳过（源目录不存在）" -ForegroundColor DarkGray
        continue
    }

    $item = Get-Item -LiteralPath $t.Src -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        Write-Host "  跳过（已经是目录联接）" -ForegroundColor DarkGray
        continue
    }

    $sizeMB = [math]::Round(((Get-ChildItem -LiteralPath $t.Src -Recurse -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum)/1MB, 1)
    Write-Host "  体积: $sizeMB MB -> $($t.Dst)"

    # 1. 复制（不用 MOVE，先确保副本完整）
    $null = & robocopy $t.Src $t.Dst /E /NFL /NDL /NJH /NJS /R:1 /W:1
    $rc = $LASTEXITCODE
    if ($rc -gt 7) {
        Write-Host "  [失败] robocopy 返回码 $rc，源目录未动，可安全重试。" -ForegroundColor Red
        Read-Host "按回车退出"
        exit 1
    }

    # 2. 核对文件数
    $srcCount = (Get-ChildItem -LiteralPath $t.Src -Recurse -Force -ErrorAction SilentlyContinue).Count
    $dstCount = (Get-ChildItem -LiteralPath $t.Dst -Recurse -Force -ErrorAction SilentlyContinue).Count
    Write-Host "  文件数: 源 $srcCount / 目标 $dstCount"
    if ($dstCount -lt $srcCount) {
        Write-Host "  [失败] 目标文件数少于源，已保留源目录，请手动检查。" -ForegroundColor Red
        Read-Host "按回车退出"
        exit 1
    }

    # 3. 删除源目录，建目录联接
    try {
        Remove-Item -LiteralPath $t.Src -Recurse -Force
        $null = cmd /c mklink /J "$($t.Src)" "$($t.Dst)" 2>&1
        if (-not (Test-Path -LiteralPath $t.Src)) { throw "联接创建失败" }
        Write-Host "  [完成] 已迁至 $($t.Dst)，并建立目录联接" -ForegroundColor Green
        $moved += [PSCustomObject]@{ 目录 = $t.Name; MB = $sizeMB }
    }
    catch {
        Write-Host "  [失败] 删除或建联接出错: $_" -ForegroundColor Red
        Write-Host "  数据仍在 $($t.Dst)，源目录若已部分删除可手动恢复。" -ForegroundColor Yellow
        Read-Host "按回车退出"
        exit 1
    }
}

# ---------- 汇总 ----------
Write-Host ""
Write-Host "=" * 62 -ForegroundColor DarkGray
$total = ($moved | Measure-Object -Property MB -Sum).Sum
Write-Host (" 全部完成，共迁移 {0} 个目录，释放 C 盘约 {1:N0} MB" -f $moved.Count, $total) -ForegroundColor Green
Write-Host "=" * 62 -ForegroundColor DarkGray
$moved | Format-Table -AutoSize

Write-Host "`n现在可以重新打开 CodeBuddy。"
Write-Host "验证方法：设置里看扩展列表是否完整，或打开一个 .py 文件试试 Ruff 是否还格式化。"
Write-Host ""
Write-Host "如需回滚：删除 C 盘上对应的目录联接，把 D:\CodeBuddyData 下的目录搬回原处即可。" -ForegroundColor DarkGray
Read-Host "按回车关闭"
