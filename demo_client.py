#!/usr/bin/env python3
"""Send a named synthetic scenario to the local scoring API."""

import argparse
import json
from urllib.request import Request, urlopen

from scenarios import SCENARIOS, get_scenario_payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "scenario", nargs="?", choices=sorted(SCENARIOS), default="teleport",
        help="synthetic scenario to submit (default: teleport)",
    )
    parser.add_argument("--url", default="http://127.0.0.1:8000/score")
    args = parser.parse_args()

    payload = get_scenario_payload(args.scenario)
    request = Request(
        args.url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        print(response.read().decode())


if __name__ == "__main__":
    main()
