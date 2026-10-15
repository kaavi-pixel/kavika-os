# Read-only preliminary Windows host checks. Does not provision or change settings.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') {
    throw 'Run this preliminary check on Windows. Linux validation is a separate M0 task.'
}

try {
    $system = Get-CimInstance Win32_ComputerSystem
    $processors = @(Get-CimInstance Win32_Processor)
    $volumes = @(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3')
    $windows = Get-CimInstance Win32_OperatingSystem
    $graphics = @(Get-CimInstance Win32_VideoController)
    $report = [ordered]@{
        checkedAtUtc = [DateTime]::UtcNow.ToString('o')
        purpose = 'Read-only Windows preflight; not a Linux or VM compatibility pass'
        windowsEdition = $windows.Caption
        windowsVersion = $windows.Version
        installedMemoryGiB = [math]::Round($system.TotalPhysicalMemory / 1GB, 2)
        hypervisorPresent = $system.HypervisorPresent
        processors = @($processors | ForEach-Object {
            [ordered]@{
                model = $_.Name
                logicalProcessors = $_.NumberOfLogicalProcessors
                virtualisationFirmwareEnabled = $_.VirtualizationFirmwareEnabled
                secondLevelAddressTranslation = $_.SecondLevelAddressTranslationExtensions
            }
        })
        graphics = @($graphics | ForEach-Object { $_.Name })
        fixedVolumes = @($volumes | ForEach-Object {
            [ordered]@{
                drive = $_.DeviceID
                capacityGiB = [math]::Round($_.Size / 1GB, 2)
                freeGiB = [math]::Round($_.FreeSpace / 1GB, 2)
            }
        })
        interpretation = @(
            'Null or false virtualisation fields need investigation; an active hypervisor may affect reporting.'
            'Windows capacity and GPU names do not establish Linux support or VM performance.'
            'Review before sharing. No serials, keys, usernames, network addresses or file contents are collected.'
        )
        pending = @(
            'Windows VM licensing decision and additional representative workloads'
            'Backups, recovery readiness and an approved reversible Linux test environment'
            'Linux /dev/kvm, actual GPU inventory and four-finger touchpad input'
            'Linux Wi-Fi, audio, keyboard, brightness, touch/pen and suspend'
            'Exact Linux stack versions and VM-off CPU/RAM/battery baseline'
        )
    }
    $report | ConvertTo-Json -Depth 6
} catch {
    throw 'Read-only host check failed. Verify CIM access locally; no configuration changes were attempted.'
}
