param(
  [string]$WorkRoot = "D:\pkg_work",
  [string]$EnvName  = "pybt_pkg",
  [string]$SrcRoot  = "D:\yolov5\双均线回测系统"
)

$ErrorActionPreference = "Stop"

Write-Host "=== 一键打包开始 ===" -ForegroundColor Cyan
Write-Host "工作目录: $WorkRoot"
Write-Host "源项目:  $SrcRoot"
Write-Host "环境名:   $EnvName"

# 1) 准备工作目录
if (-not (Test-Path $WorkRoot)) { New-Item -ItemType Directory -Path $WorkRoot | Out-Null }
$PkgRoot = Join-Path $WorkRoot "proj"
if (Test-Path $PkgRoot) { Remove-Item -Recurse -Force $PkgRoot }
New-Item -ItemType Directory -Path $PkgRoot | Out-Null

# 2) 复制必要文件
$needFiles = @(
  "GUI_QT.py",
  "GUI_QT_Interactive.py",
  "interactive_backtest.py",
  "回测示例.py",
  "huatu_mz.py",
  "data_processing.py",
  "trend_line_processing.py",
  "build_exe.py",
  "下载股票历史数据\downloader_bridge.py"
)
foreach ($rel in $needFiles) {
  $src = Join-Path $SrcRoot $rel
  $dst = Join-Path $PkgRoot $rel
  $dstDir = Split-Path $dst -Parent
  if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir | Out-Null }
  if (-not (Test-Path $src)) {
    Write-Host "缺少文件: $rel" -ForegroundColor Yellow
  } else {
    Copy-Item $src $dst
  }
}

# 3) 创建干净 conda 环境 (Python 3.9)
Write-Host "创建 conda 环境 $EnvName (Python 3.9)" -ForegroundColor Cyan
cmd /c "conda env remove -n $EnvName -y" 2>$null | Out-Null
cmd /c "conda create -n $EnvName python=3.9 -y" | Out-Null

# 4) 安装最小依赖（conda）
$condaPkgs = "-n $EnvName -y pyqt=5.15.* pyqtwebengine=5.15.* pandas numpy matplotlib pillow pip"
cmd /c "conda install $condaPkgs" | Out-Null

# 5) 安装 pip 依赖（在该环境）
cmd /c "conda run -n $EnvName pip install backtrader nuitka orderedset zstandard" | Out-Null

# 6) 执行打包
Write-Host "开始打包..." -ForegroundColor Cyan
Push-Location $PkgRoot
try {
  cmd /c "conda run -n $EnvName python build_exe.py"
}
finally {
  Pop-Location
}

Write-Host "`n✅ 完成。可执行文件在: $($PkgRoot)\dist" -ForegroundColor Green
Write-Host "如 onefile 失败会自动回退为 standalone 目录。" -ForegroundColor Green

# 7) 生成交付包
$TimeTag = Get-Date -Format "yyyyMMdd_HHmm"
$DeliveryDir = Join-Path $WorkRoot ("交付包_" + $TimeTag)
if (Test-Path $DeliveryDir) { Remove-Item -Recurse -Force $DeliveryDir }
New-Item -ItemType Directory -Path $DeliveryDir | Out-Null

$DistDir = Join-Path $PkgRoot "dist"
Write-Host "生成交付包: $DeliveryDir" -ForegroundColor Cyan

# 复制 exe 或 standalone 目录
$items = Get-ChildItem $DistDir
foreach ($it in $items) {
  $dst = Join-Path $DeliveryDir $it.Name
  if ($it.PSIsContainer) {
    Copy-Item $it.FullName $dst -Recurse
  } else {
    Copy-Item $it.FullName $dst
  }
}

# 附带文档/资源（如存在）
$extraFiles = @(
  "stock_list_20241219.csv",
  "README.md",
  "使用说明.md"
)
foreach ($rel in $extraFiles) {
  $src = Join-Path $SrcRoot $rel
  if (Test-Path $src) {
    Copy-Item $src (Join-Path $DeliveryDir (Split-Path $src -Leaf))
    Write-Host "附带: $rel" -ForegroundColor Gray
  }
}

# 如果没有说明文件，生成一个简要说明
$readme = Join-Path $DeliveryDir "使用说明_快速开始.txt"
if (-not (Test-Path (Join-Path $DeliveryDir "使用说明.md"))) {
  $txt = @"
交付包快速开始
1) 双击运行 GUI_QT.exe（普通回测）或 GUI_QT_Interactive.exe（交互式回测）。
2) 如未生成单文件，目录中 *.dist 内包含可执行程序，请进入目录运行同名 exe。
3) 若使用交互式回测，出现上方决策条后，可先缩放图表，再选择“按策略执行/跳过”。
4) 如需日线数据源，放置 stock_list_20241219.csv 与程序同目录可用。
注：首次运行可能被安全软件拦截，请允许。
"@
  $txt | Out-File -FilePath $readme -Encoding UTF8
}

Write-Host "交付包已生成: $DeliveryDir" -ForegroundColor Green

Write-Host "=== 一键打包结束 ===" -ForegroundColor Cyan


