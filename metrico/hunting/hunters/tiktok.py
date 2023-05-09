from pytiktok import KitApi

from metrico.hunting import MultiObjCaller
from metrico.hunting.hunters.basic import BasicHunter


class TikTokHunter(BasicHunter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api = self._create_api()

    def _create_api(self):
        if key := self.config.get("key"):
            return KitApi(access_token=key)
        return None


class TikTokHunterMulti(TikTokHunter):
    def _create_api(self):
        if keys := self.config.get("keys"):
            return MultiObjCaller(cls=KitApi, kwargs=[{"access_token": key} for key in keys])
        raise Exception("Fail to create api!")
