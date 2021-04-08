import os
import urllib.request


def scrape_monographs(urls, data_path):
    paths = []
    for url in urls:
        filename = url.split('/')[-1]
        path = data_path / filename
        if not os.path.exists(path):
            with urllib.request.urlopen(url) as f:
                pdf = f.read()
                f2 = open(path, 'wb')
                f2.write(pdf)
        paths.append(path)
    return paths
