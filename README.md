# pgns Python SDK

Python client library for the [pgns](https://pgns.io) webhook relay API.

## Installation

```bash
pip install pgns
```

## Quick Start

```python
from pgns.client import PgnsClient

client = PgnsClient(api_key="your-api-key")

# List roosts
roosts = client.roosts.list()

# Send a pigeon
client.pigeons.send("rst_abc123", payload={"event": "user.created", "data": {"id": 1}})
```

## Async Usage

```python
from pgns.async_client import AsyncPgnsClient

async with AsyncPgnsClient(api_key="your-api-key") as client:
    roosts = await client.roosts.list()
```

## Submodule Imports

The SDK provides targeted submodule imports for better discoverability:

```python
from pgns.client import PgnsClient
from pgns.async_client import AsyncPgnsClient
from pgns.models import Roost, Destination
from pgns.errors import PigeonsError, WebhookVerificationError
from pgns.webhook import Webhook
from pgns.events import event_stream, async_event_stream
from pgns.types import DestinationType, DeliveryStatus
```

Root-level imports (`from pgns.sdk import PgnsClient`) are deprecated and will be removed in a future release.

## Documentation

Full documentation is available at [docs.pgns.io/sdks/python](https://docs.pgns.io/sdks/python).

## License

MIT
