# Releasing Tiny Grid

This document describes the release process for publishing new versions of tinygrid to PyPI.

## Prerequisites

Before creating your first release, ensure:

1. **PyPI Account**: Register at https://pypi.org if you haven't already
2. **API Token**: Generate a PyPI API token
   - Go to https://pypi.org/manage/account/token/
   - Create a new token scoped to the tinygrid project (or use a global token for the first release)
   - Copy the token (it starts with `pypi-`)
3. **GitHub Secret**: Add the PyPI token to GitHub
   - Go to https://github.com/kvkenyon/tinygrid/settings/secrets/actions
   - Create a new secret named `PYPI_TOKEN`
   - Paste your PyPI API token as the value

## Release Process

The release process is fully automated via GitHub Actions. Here's how to create a new release:

### 1. Prepare for Release

```bash
# Ensure you're on main branch with latest changes
git checkout main
git pull

# Verify all tests pass
just check

# Test the build locally (optional but recommended)
just build
ls -lh dist/
```

### 2. Create a GitHub Release

1. Go to https://github.com/kvkenyon/tinygrid/releases/new
2. Click "Choose a tag"
3. Create a new tag with format `vX.Y.Z`:
   - Use semantic versioning: `vMAJOR.MINOR.PATCH`
   - Examples: `v0.2.0`, `v1.0.0`, `v1.2.3`
   - The `v` prefix is required
4. Set the release title (e.g., `v0.2.0` or `Release 0.2.0`)
5. Add release notes describing:
   - New features
   - Bug fixes
   - Breaking changes
   - Dependency updates
6. Click "Publish release"

### 3. Automated Workflow

Once you publish the release, the workflow automatically:

1. ✅ Extracts version from the tag (e.g., `v0.2.0` → `0.2.0`)
2. ✅ Updates `pyproject.toml` with the new version
3. ✅ Updates `tinygrid/__init__.py` with the new version
4. ✅ Builds the package (creates wheel and source distribution)
5. ✅ Publishes to PyPI
6. ✅ Uploads build artifacts to the GitHub Release

### 4. Verify Publication

After the workflow completes:

1. Check the workflow run at https://github.com/kvkenyon/tinygrid/actions
2. Verify the package on PyPI at https://pypi.org/project/tinygrid/
3. Test installation:
   ```bash
   pip install tinygrid==X.Y.Z
   ```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (0.X.0): New functionality, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

Examples:
- `v0.1.0` → `v0.2.0`: Added new unified API methods (minor)
- `v0.2.0` → `v0.2.1`: Fixed a bug in date parsing (patch)
- `v0.9.0` → `v1.0.0`: First stable release (major)

## Troubleshooting

### Release Failed

If the publish workflow fails:

1. Check the workflow logs at https://github.com/kvkenyon/tinygrid/actions
2. Common issues:
   - **PyPI token invalid**: Update the `PYPI_TOKEN` secret
   - **Version already exists**: You can't republish the same version
   - **Build failures**: Fix the issues and create a new release with a new version tag

### Fixing a Failed Release

To fix and retry:

1. Delete the failed release from GitHub
2. Delete the tag: `git push --delete origin vX.Y.Z`
3. Fix any issues locally
4. Create a new release with the same or incremented version

### Version Already Exists on PyPI

If you accidentally created a release but it failed to publish:

- You cannot reuse the same version number on PyPI
- Create a new release with an incremented version (e.g., `v0.2.1` instead of `v0.2.0`)
- Note the issue in the release notes

## Manual Publishing (Emergency)

If the automated workflow is unavailable, you can publish manually:

```bash
# Ensure you're on the release commit
git checkout vX.Y.Z

# Update version in files manually
# Edit pyproject.toml and tinygrid/__init__.py

# Build
just build

# Publish (requires PYPI_TOKEN in environment or ~/.pypirc)
just publish
```

## Pre-releases

For alpha, beta, or release candidate versions:

1. Use version tags like `v0.2.0a1`, `v0.2.0b1`, `v0.2.0rc1`
2. Mark the GitHub Release as a "pre-release"
3. The package will be published to PyPI but marked as pre-release
4. Users must explicitly request pre-releases: `pip install tinygrid==0.2.0a1`

## Release Checklist

Before creating a release, verify:

- [ ] All changes are merged to main
- [ ] CI is passing on main
- [ ] `just check` passes locally
- [ ] Version number follows semantic versioning
- [ ] Release notes are prepared
- [ ] Breaking changes are documented (if any)
- [ ] README is up to date
- [ ] CHANGELOG is updated (if maintained)

After release:

- [ ] Workflow completed successfully
- [ ] Package appears on PyPI
- [ ] Package can be installed via pip
- [ ] Documentation is accurate for the new version

## Notes

- **Version updates are ephemeral**: The workflow updates version numbers for building, but doesn't commit them back to the repository. The git tag is the source of truth.
- **Tag format matters**: Tags must start with `v` followed by semantic version (e.g., `v0.2.0`)
- **Idempotent releases**: If a release fails, you can delete it and recreate it (before it's published to PyPI)
- **No manual version bumping**: Don't update version numbers in code before creating a release - the workflow handles this automatically
