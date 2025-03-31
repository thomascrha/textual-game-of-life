# Publishing to PyPI with OpenID Connect

This project uses GitHub Actions with OpenID Connect (OIDC) for secure authentication when publishing to PyPI.

## Setup Instructions

### 1. Configure PyPI OIDC Integration

1. Log in to your PyPI account at https://pypi.org
2. Navigate to Account Settings → Add API token
3. Instead of creating a token, look for "Configure a new pending publisher"
4. Enter the following information:
   - **Name**: `textual-game-of-life`
   - **Workflow Name**: `Publish to PyPI` (must match the name in the workflow file)
   - **Environment**: Leave blank (uses default)
   - **Repository Owner**: `thomascrha` (your GitHub username)
   - **Repository Name**: `textual-game-of-life`

5. Click "Create" to create the pending publisher

### 2. Verify Integration Works

The OIDC integration will be activated after the first successful workflow run. To trigger a release:

1. Update the version in `pyproject.toml`
2. Commit and push your changes
3. Run `make pypi` to create and push a version tag
4. GitHub Actions will automatically build and publish the package

## How It Works

1. When you push a tag starting with "v" (e.g., v0.6.0), GitHub Actions runs the publish workflow
2. The workflow uses OpenID Connect to authenticate with PyPI without needing API tokens
3. PyPI verifies the GitHub repository and workflow name match the configured publisher
4. The package is published securely

## Troubleshooting

- If the publication fails with an OIDC error, ensure that:
  - The workflow name matches exactly what's configured in PyPI
  - The repository owner and name are correctly set in PyPI
  - The package name in `pyproject.toml` matches the PyPI publisher name

For more information, see [PyPI's documentation on trusted publishing](https://docs.pypi.org/trusted-publishers/).

