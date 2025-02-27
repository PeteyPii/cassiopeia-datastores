from typing import Any, Iterable, MutableMapping, Type, TypeVar

from cassiopeia.data import Platform, Region
from cassiopeia.datastores.uniquekeys import convert_region_to_platform
from cassiopeia.dto.summoner import SummonerDto
from datapipelines import (
    DataSink,
    DataSource,
    NotFoundError,
    PipelineContext,
    Query,
    validate_query,
)

from .common import SimpleKVDiskService

T = TypeVar("T")


class SummonerDiskService(SimpleKVDiskService):
    @DataSource.dispatch
    def get(self, type: Type[T], query: MutableMapping[str, Any], context: PipelineContext = None) -> T:
        pass

    @DataSource.dispatch
    def get_many(self, type: Type[T], query: MutableMapping[str, Any], context: PipelineContext = None) -> Iterable[T]:
        pass

    @DataSink.dispatch
    def put(self, type: Type[T], item: T, context: PipelineContext = None) -> None:
        pass

    @DataSink.dispatch
    def put_many(self, type: Type[T], items: Iterable[T], context: PipelineContext = None) -> None:
        pass

    ############
    # Summoner #
    ############

    _validate_get_summoner_query = Query. \
        has("id").as_(str). \
        or_("accountId").as_(str). \
        or_("puuid").as_(str).also. \
        has("platform").as_(Platform)

    @get.register(SummonerDto)
    @validate_query(_validate_get_summoner_query, convert_region_to_platform)
    def get_summoner(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> SummonerDto:
        platform_str  = query["platform"].value
        for key in self._store:
            if key.startswith("SummonerDto."):
                _, platform, id_, account_id, puuid = key.split(".")
                if platform == platform_str and any([
                    str(query.get("id", None)).startswith(id_),
                    str(query.get("account_id", None)).startswith(account_id),
                    str(query.get("puuid", None)).startswith(puuid),
                ]):
                    dto = SummonerDto(self._get(key))
                    if any([
                        dto["id"] == str(query.get("id", None)),
                        dto["accountId"] == str(query.get("account_id", None)),
                        dto["puuid"] == str(query.get("puuid", None)),
                    ]):
                        return dto
        else:
            raise NotFoundError

    @put.register(SummonerDto)
    def put_summoner(self, item: SummonerDto, context: PipelineContext = None) -> None:
        platform = Region(item["region"]).platform.value
        key = "{clsname}.{platform}.{id}.{account_id}.{puuid}".format(clsname=SummonerDto.__name__,
                                                                     platform=platform,
                                                                     id=item["id"][:8],
                                                                     account_id=item["accountId"][:8],
                                                                     puuid=item["puuid"][:8],
                                                                     )
        self._put(key, item)
