# Kavi'ka OS: uploaded project review

Reviewed 15 October 2026 | Input: user-supplied `kavika-os.zip`.

The archive extends the existing Fedora/KDE and full-Windows concept into an installable-OS roadmap. It adds a Windows preflight tool and preliminary evidence, but no working desktop integration or bootable image.

## Changes retained

- **OS roadmap:** `os-implementation-plan.md` adds OS0–OS6, RPM packaging, isolated live-image development, installer tests, a hardware pilot, and release maintenance.
- **Windows preflight:** `tools/Test-KavikaHost.ps1` queries CIM and prints JSON. Its source is imported unchanged; this review does not rewrite or run it.
- **M0 evidence:** `docs/validation/m0.md` includes archive-reported Windows edition, CPU/memory/storage, GPU name, and virtualisation indicators. These are retained with explicit provenance limits.
- **Cross-links:** README, features, prototype plan, and hand-off now link the OS roadmap and evidence worksheet.
- **Existing constraints:** full Windows including Comet, no app allowlist, the original brief, and approved logo remain intact.

Ignoring CRLF/LF differences, existing issue templates, `.gitignore`, branding notes, and the original brief have no semantic changes. The logo matches the existing original byte-for-byte; the archive's `.git` directory, hooks, config, and objects are not imported into the connected checkout or executed.

## Corrections made

- **Status:** replace “no implementation/testing” statements with “diagnostics exist; integration and OS gates have not passed.”
- **Scope:** describe the installable OS as a later deliverable and keep the integration prototype distinct from an OS release. Repository development does not authorise laptop disk changes.
- **Gate mapping:** move F08/setup removal to OS2/M5 and explicitly include T14/T15 there.
- **Distribution tests:** define O01–O04 and T17–T23 for image provenance, live boot, safe installation, first-run consent, host Secure Boot, upgrades/recovery, and release/legal readiness.
- **Live tracker:** add OS3–OS6 tasks #12–#15 and note the preliminary evidence/provenance limits on M0 issue #1. All remain open; no hardware gate is marked complete.
- **Evidence attribution:** retain supplied preflight values but do not present the archive's earlier run as an execution performed during this review. Source machine, script hash, and reviewed output remain acceptance prerequisites.
- **Build references:** clarify that the Fedora wiki's Fedora 39 example is historical and not a selected base; keep potentially dangerous installer tooling confined to an expendable VM.

## Static tool concerns

The script contains queries and formatting/output/error handling, with no explicit configuration-changing commands found. Its `installedMemoryGiB` key is a naming mismatch for `Win32_ComputerSystem.TotalPhysicalMemory`; the worksheet now distinguishes this from installed-module capacity and guest-memory availability.

Its single generic catch block may hide which CIM query failed and prevent partial results. GPU names are not full device/driver validation, fixed-volume space is not validation of an external installation target, and false/null virtualisation fields are not automatically a capability verdict.

These are source-review findings, not reproduced runtime bugs. The tool remains unchanged because this request is for review and Markdown reconciliation; code revisions and Windows execution require a separate implementation/test step.

## Evidence and safety limits

No raw preflight JSON or independently verifiable execution record accompanied the summary. This review did not probe the target laptop, run PowerShell, provision Windows, install Linux, build an ISO, modify firmware, or change physical disks.

The image build mechanism is plausible: Lorax documents Anaconda/Kickstart-based live media and warns about real-device risks in `--no-virt` mode ([Lorax documentation](https://github.com/weldr/lorax/blob/master/docs/livemedia-creator.rst)). Fedora's wiki example targets Fedora 39, so it must be adapted and validated for the chosen supported release rather than copied as current instructions ([Fedora workflow](https://fedoraproject.org/wiki/Livemedia-creator-_How_to_create_and_use_a_Live_CD)).

No theme specification or implemented theme was present in the ZIP. The previously drafted theme remains a separate unapproved design; importing these project changes does not approve or implement it.

## Next step

Finish M0 with attributed target-machine results, a legitimate guest-licensing decision, backup readiness, and a separately approved reversible Linux test route. Validate Linux KVM and actual touchpad/device support before treating the Windows preflight as more than preliminary evidence.
