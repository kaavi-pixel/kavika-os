# Kavi'ka: ISO byte-reproducibility test, 20 October 2026

Two builds of the same source, from the same pinned base, on the same host with the same toolchain, do **not** produce identical ISO bytes. The payload is identical; the difference is ISO/GPT bookkeeping written at build time. This is evidence, not a claim about cross-machine reproducibility, which was never established either way.

## The two builds

| | Build A (original) | Build B (verification rebuild) |
|---|---|---|
| Output SHA-256 | `bd8407d6393a12f8a5829ef15a86371b854f08834d9fd7df4a85ddbdc8820e0d` | `bff1b107d87a3364a38fa7974bb4fac2908ea659ca6203c2ffe083fb0e9b3935` |
| Size | 3,370,319,872 bytes | 3,370,319,872 bytes |
| Base ISO | `c8295961…` (pinned, verified) | `c8295961…` (pinned, verified) |
| Payload source | same commit | same commit, plus a builder change to GRUB-checker name resolution |

Build B was made to confirm that accepting `grub2-script-check` as well as `grub-script-check` did not alter the image. It did not: the two files that matter are byte-identical.

## Payload is byte-identical

| Component extracted from the ISO | SHA-256 |
|---|---|
| `/boot/grub2/grub.cfg` (both builds) | `b05d29d0d819cbd8bce4152e32ecd5c1bf98b7a32d333077a0062f56d42c7d11` |
| `/boot/kavika-preview.cpio` (both builds) | `2198d7f667be66ad14ac62081ed9f8a2ee207cab01118a35032fa55db8396320` |

The build manifests agree as well: the same 18 payload paths with the same per-file SHA-256 values in both. The two manifests differ only in `builder_sha256` (the builder source changed) and in `output_sha256`/`output_bytes`-adjacent fields.

## What differs: 316 bytes, all bookkeeping

`cmp -l` reports **316 differing bytes out of 3,370,319,872**. They cluster in:

| Region | Differing bytes | What lives there |
|---|---|---|
| First 32 KiB (GPT/MBR area) | 56 | Primary GPT partition entry |
| Rest of the image | 260 | Backup GPT mirror, plus ISO 9660 volume-descriptor identifier fields |

The cause is identifiable. In each 128-byte GPT partition entry, the first 16 bytes are the **partition type GUID** and the next 16 are the **unique partition GUID**. In both images the type GUID is identical (`a2a0d0eb-e5b9-3344-87c0-68b6b72699c7`, Linux filesystem data); the unique GUID differs:

```
bd8407d6… (validated)  bytes 16-31 of the entry:  ee 97 f0 0d ee 04 0d 46 8b 4c ec a0 cf cc 9b 6d
bff1b107… (rebuild)    bytes 16-31 of the entry:  3b 0a 31 29 1f 80 1c 4f ad 2f bc cf 41 3d f9 89
```

`xorriso -report_system_area` on `bd8407d6…` independently reports the same value as its GPT disk GUID (`ee97f00dee040d468b4deca0cfcc9b6d`), which is where this figure was re-checked. An earlier draft of this record had the two GUIDs attributed to the wrong builds; the hashes are given above so the attribution cannot be read ambiguously.

`xorriso` generates a fresh random partition GUID per build (`-boot_image any partition_offset=16`), the backup GPT mirrors it, and a few volume-descriptor identifier fields are also written per build. None of it is content.

## Consequences

- **Do not use the ISO SHA-256 to decide whether two builds are the same.** Same-host rebuilds differ every time. The **manifest** is the correct comparison artifact: it records `base_sha256` and a SHA-256 for every payload file with fixed timestamps.
- The pinned-hash check in the launcher and builder still matters — it guarantees the *input* is the pinned Fedora image and that a specific file is the one tested — but a hash is an identity for one artefact, not a reproducibility signal.
- `docs/build.md`'s existing warning against claiming reproducible builds is now backed by measurement rather than caution. Making the image byte-reproducible would need deterministic GUIDs (for example fixed via `appended_partition`/`-volid` options or a post-pass with `xorriso -boot_image any patch`) and deterministic volume-descriptor fields; that work is not done.
- The validated artefact for the boot test remains build A, `bd8407d6…`. Build B was only a verification rebuild and was not booted.

## Scope

Both builds ran on the Surface Laptop Studio: Fedora 44, kernel `6.19.10-300.fc44`, Python 3.14.8, pycdlib 1.22.0, xorriso 1.5.8.pl02, GNU cpio 2.15, isomd5sum 1.2.5. Build B's output was written to a scratch directory; it is not a release candidate and no ISO is approved for flashing.
