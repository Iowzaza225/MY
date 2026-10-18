# TEAMMOD27

Standalone iOS application build repository. The production source and UI identity are TEAMMOD27. This repository is separate from RUIZEN and does not modify RUIZEN source.

Build via `.github/workflows/build-teammod27.yml` using a macOS GitHub Actions runner. The IPA is unsigned and requires appropriate authorized signing before installation. The iOS bundle identifier is preserved as requested; this does **not** confer special file-system permissions or guarantee installation.

**Never commit license keys, pairing credentials, PINs, provisioning profiles or signing secrets.**
