# Examples

## Setup

```bash
cd tiny-grid
uv sync --dev --all-extras
```

Create a `.env` file in this directory:

```bash
cp .env.example .env
# Edit .env with your credentials
```

## ERCOT Credentials

Get credentials from [ERCOT API Explorer](https://apiexplorer.ercot.com/):

1. Register an account
2. Subscribe to API products
3. Copy your subscription key

Your `.env` file needs:

```
ERCOT_USERNAME=your-email@example.com
ERCOT_PASSWORD=your-password
ERCOT_SUBSCRIPTION_KEY=your-key
```

## Running Examples

```bash
# Python script
python examples/ercot_example.py

# Jupyter notebook
jupyter notebook examples/ercot_example.ipynb
```

## Auth Troubleshooting

If authentication fails, run the debug script:

```bash
python examples/debug_auth.py
```

This tests the Azure B2C token endpoint directly.
