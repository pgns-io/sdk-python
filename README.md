# pgns Python SDK

Python client library for the [pgns](https://pgns.io) webhook relay API.

## Installation

```bash
pip install pgns
```

## Quick Start

```python
from pgns import PgnsClient

client = PgnsClient(api_key="your-api-key")

# List roosts
roosts = client.roosts.list()

# Send a pigeon
client.pigeons.send("rst_abc123", payload={"event": "user.created", "data": {"id": 1}})
```

## Async Usage

```python
from pgns import AsyncPgnsClient

async with AsyncPgnsClient(api_key="your-api-key") as client:
    roosts = await client.roosts.list()
```

## Documentation

Full documentation is available at [docs.pgns.io/sdks/python](https://docs.pgns.io/sdks/python).

## License

MIT
