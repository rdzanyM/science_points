import yaml
from typing import Dict, List


class MonographConfigEntry:
    def __init__(self, raw_config: Dict[str, str]):
        self.url = raw_config['url']
        self.date = raw_config['date']
        self.title = raw_config['title']
        self.path = None


class Config:
    def __init__(self):
        with open('config.yaml') as file:
            self._config = yaml.safe_load(file)

    def get_setting(self, key: str):
        """
        Return a setting from the config
        :param key: key for the setting
        :return: value of the setting
        """
        return self._config[key]

    def get_monograph_config(self) -> List[MonographConfigEntry]:
        """
        :return: List of monograph config entries
        """
        return [MonographConfigEntry(entry) for entry in self._config['monographs']]
