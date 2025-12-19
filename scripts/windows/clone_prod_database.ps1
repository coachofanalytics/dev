# Clone Production Database to Local (Windows PowerShell Version)
# Creates an exact copy of production PostgreSQL database locally

Write-Host 'CODA Database Cloning Tool (Windows)' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'This will create an EXACT copy of production database locally.'
Write-Host 'You can then work with real production data safely.'
Write-Host ''

# Configuration
$PROD_APP = 'codatrainingapp'
$LOCAL_DB_NAME = 'coda_prod_clone'
$LOCAL_DB_USER = 'postgres'
$BACKUP_FILE = "$env:TEMP\coda_prod_latest.dump"
$PG_BIN = 'C:\Program Files\PostgreSQL\18\bin'

# Add PostgreSQL to PATH for this session
$env:Path += ";$PG_BIN"

Write-Host 'Options:' -ForegroundColor Yellow
Write-Host '  1. Full PostgreSQL clone (recommended)'
Write-Host '  2. SQLite conversion (quick examination)'
Write-Host ''
$choice = Read-Host 'Choose option (1 or 2)'

if ($choice -eq '1') {
    Write-Host ''
    Write-Host 'Option 1: Full PostgreSQL Clone' -ForegroundColor Blue
    Write-Host '================================'
    
    # Check if PostgreSQL is installed
    try {
        $psqlVersion = & "$PG_BIN\psql.exe" --version
        Write-Host "PostgreSQL found: $psqlVersion" -ForegroundColor Green
    }
    catch {
        Write-Host 'PostgreSQL not installed' -ForegroundColor Red
        exit 1
    }
    
    # Check if PostgreSQL service is running
    $service = Get-Service -Name 'postgresql-x64-18' -ErrorAction SilentlyContinue
    if ($service.Status -ne 'Running') {
        Write-Host 'PostgreSQL service not running' -ForegroundColor Red
        Write-Host 'Starting PostgreSQL service...'
        Start-Service -Name 'postgresql-x64-18'
        Start-Sleep -Seconds 3
    }
    Write-Host 'PostgreSQL service running' -ForegroundColor Green
    
    Write-Host ''
    Write-Host 'Step 1: Creating Heroku backup...' -ForegroundColor Cyan
    Write-Host 'This may take 1-5 minutes...'
    
    # Create backup
    heroku pg:backups:capture --app $PROD_APP
    Write-Host 'Backup created' -ForegroundColor Green
    
    # Get backup URL and download
    Write-Host ''
    Write-Host 'Step 2: Downloading backup...' -ForegroundColor Cyan
    $backupUrl = heroku pg:backups:url --app $PROD_APP
    Invoke-WebRequest -Uri $backupUrl -OutFile $BACKUP_FILE
    $fileSize = [math]::Round((Get-Item $BACKUP_FILE).Length / 1MB, 2)
    Write-Host "Downloaded $fileSize MB" -ForegroundColor Green
    
    Write-Host ''
    Write-Host 'Step 3: Preparing local database...' -ForegroundColor Cyan
    
    # Drop existing database if it exists
    & "$PG_BIN\dropdb.exe" -U $LOCAL_DB_USER --if-exists $LOCAL_DB_NAME 2>$null
    
    # Create database
    & "$PG_BIN\createdb.exe" -U $LOCAL_DB_USER $LOCAL_DB_NAME
    Write-Host 'Database created' -ForegroundColor Green
    
    Write-Host ''
    Write-Host 'Step 4: Restoring backup...' -ForegroundColor Cyan
    Write-Host 'This may take 2-5 minutes...'
    
    # Restore backup
    & "$PG_BIN\pg_restore.exe" -U $LOCAL_DB_USER --no-acl --no-owner -d $LOCAL_DB_NAME $BACKUP_FILE 2>$null
    
    Write-Host ''
    Write-Host 'Restore complete!' -ForegroundColor Green
    
    # Verify
    $tableCount = & "$PG_BIN\psql.exe" -U $LOCAL_DB_USER -d $LOCAL_DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
    Write-Host "Found $($tableCount.Trim()) tables" -ForegroundColor Green
    
    Write-Host ''
    Write-Host 'SUCCESS! Production database cloned locally!' -ForegroundColor Green
    Write-Host ''
    Write-Host 'Next steps:' -ForegroundColor Cyan
    Write-Host '  cd coda'
    Write-Host '  python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings'
    Write-Host ''
    
    # Cleanup
    Remove-Item $BACKUP_FILE -ErrorAction SilentlyContinue
}
else {
    Write-Host 'Use: python scripts/pull_prod_data_to_local.py' -ForegroundColor Yellow
}
