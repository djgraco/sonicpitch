# Preparing a future release

This is a maintained release checklist, not a submission draft for an already
published version. The repository maintenance work does not publish a release
or change the current NVDA compatibility declaration.

## Metadata

Edit `buildVars.py` before a real release. Set the intended version,
minimum supported NVDA version and last tested NVDA version based on actual
tests. Do not predeclare NVDA 2027.1 compatibility.

The build generates the English manifest and the translated descriptions from
the PO catalogs. The project URL is https://github.com/djgraco/sonicpitch.
Use the license and source URLs in `buildVars.py` when preparing store metadata.

## Release checklist

1. Finish the Windows/NVDA tests in [TESTING.md](../TESTING.md), including
   affected SAPI hosts, dialog cancellation, rapid changes and soundWave integration.
2. Set the new version and verified NVDA compatibility in `buildVars.py`.
3. Move the relevant Unreleased changelog entries under the new version.
4. Regenerate the POT, update PO metadata as needed and run the source checks.
5. Build the final package using the [build instructions](building.md).
6. Validate that exact package and write its SHA-256 sidecar.
7. Install and smoke-test that exact file in the intended NVDA versions.
8. Prepare the release manually with a matching tag and the asset
   `globalSonicPitch-<version>.nvda-addon`. Include its checksum and changes.
9. Submit or update Add-on Store metadata using the exact versioned download
   URL, package checksum, verified NVDA compatibility and descriptions generated
   into that package. Review the Polish and Slovak descriptions as well.

There is no fixed-name `globalSonicPitch.nvda-addon` asset. Do not advertise a
`releases/latest/download/globalSonicPitch.nvda-addon` URL. The release listing
is the general download entry point; a store submission uses the exact asset URL.

## Review and rollback

Keep a record of the source commit, build inputs, tested environments and final
checksum. If a released version has a serious runtime regression, document the
affected version and coordinate the corrected package and store update.
The build workflow provides artifacts for review; it does not publish releases,
delete old releases, change tags or submit to the store.
