# Kanji Quiz Bot - Task Scheduler Setup Script
# 管理者権限で実行してください

# 現在のディレクトリを取得
$ScriptDir = Split-Path -Parent $MyInvocation.MyLocation
$BatchFile = Join-Path $ScriptDir "run_quiz_bot.bat"

Write-Host "Setting up Kanji Quiz Bot scheduled task..." -ForegroundColor Green
Write-Host "Script location: $ScriptDir" -ForegroundColor Yellow
Write-Host "Batch file: $BatchFile" -ForegroundColor Yellow

# 管理者権限チェック
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Write-Host "Error: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# バッチファイル存在確認
if (-not (Test-Path $BatchFile)) {
    Write-Host "Error: Batch file not found at $BatchFile" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    # 既存タスクの削除（存在する場合）
    $existingTask = Get-ScheduledTask -TaskName "KanjiQuizDaily" -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName "KanjiQuizDaily" -Confirm:$false
    }

    # 新しいタスクの作成
    Write-Host "Creating new scheduled task..." -ForegroundColor Green

    # タスクアクション（実行する内容）
    $action = New-ScheduledTaskAction -Execute $BatchFile -WorkingDirectory $ScriptDir

    # タスクトリガー（実行スケジュール）
    $trigger = New-ScheduledTaskTrigger -Daily -At "07:00"

    # タスク設定
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Hours 2)

    # 現在のユーザー情報を取得
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

    # タスク主体（実行ユーザー）
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType ServiceAccount -RunLevel Highest

    # タスクの登録
    Register-ScheduledTask -TaskName "KanjiQuizDaily" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Kanji Quiz Bot Daily Video Generation and Analysis"

    Write-Host "Task created successfully!" -ForegroundColor Green
    Write-Host "Task Name: KanjiQuizDaily" -ForegroundColor Green
    Write-Host "Schedule: Daily at 7:00 AM" -ForegroundColor Green
    Write-Host "Batch File: $BatchFile" -ForegroundColor Green

    # タスク情報の表示
    Write-Host "`nTask information:" -ForegroundColor Cyan
    Get-ScheduledTask -TaskName "KanjiQuizDaily" | Format-List TaskName, State, Author

    # テスト実行の提案
    Write-Host "`nWould you like to test run the task now? (y/n): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Starting test run..." -ForegroundColor Green
        Start-ScheduledTask -TaskName "KanjiQuizDaily"
        Write-Host "Task started! Check the logs directory for output." -ForegroundColor Green
    }

} catch {
    Write-Host "Error creating scheduled task: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nPress Enter to exit..." -ForegroundColor Gray
Read-Host