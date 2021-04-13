import os
import urllib.request
from pathlib import Path
from typing import List

from src import MonographConfigEntry


def scrape_monographs(monograph_config: List[MonographConfigEntry], data_path: Path) -> None:
    for monograph in monograph_config:
        filename = monograph.url.split('/')[-1]
        path = data_path / filename
        if not os.path.exists(path):
            with urllib.request.urlopen(monograph.url) as f:
                pdf = f.read()
                f2 = open(path, 'wb')
                f2.write(pdf)

        monograph.path = path
