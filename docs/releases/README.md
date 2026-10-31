# Preparing the next Release

[中文 Logo 发行说明](../logo-assets.zh-CN.md)

Keep existing tags and downloads unchanged. Use the established release checks for the Skill;
the checklist below adds the full-size logo download to future releases.

1. Review and merge the release contents, then wait for CI on the exact commit to pass.
2. Prepare the versioned Skill ZIP, its file manifest and verification record as usual.
   The Skill keeps the 32/128px icons used by its interface metadata.
3. Prepare the separate [full-size logo kit](../../assets/brand/logo-kit/README.md):

   ```sh
   python tools/package_logo_assets.py --out dist/logo-assets-next
   ```

   This creates `deterministic-pixel-art-logos.zip` and a checksum line. It verifies all
   30 PNGs, their editable specifications and supporting files before creating the download.
   The default 256/512px badges are enhanced; 32/64/128px badges and all transparent marks remain simple.
4. Include the logo ZIP alongside the Skill ZIP in the new Release. Add its checksum line to
   that release's `SHA256SUMS.txt`, without dropping the other entries or uploading a second file
   with the same checksum filename. Record the logo ZIP hash in the release verification record.
   Keep English and Chinese release notes readable on the page; they do not need separate downloads.
5. Verify the final draft's files, publish through the normal release process, then download both ZIPs,
   check their hashes and test extraction. Do not replace older release assets or install a Skill
   as part of this logo packaging step.

To redraw the logos after an intentional design change, use a new directory and review the result:

```sh
python assets/brand/build_logo_kit.py --skill skill/deterministic-pixel-art --out output/logo-rebuild
```

Replace the selected assets only after that review. The logo ZIP is a reusable asset attachment;
preparing it does not create a tag or Release.
