from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.exception import Exception_
from ...models.report import Report
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    rtd_timestamp_from: str | Unset = UNSET,
    rtd_timestamp_to: str | Unset = UNSET,
    repeat_hour_flag: bool | Unset = UNSET,
    interval_id_from: int | Unset = UNSET,
    interval_id_to: int | Unset = UNSET,
    interval_ending_from: str | Unset = UNSET,
    interval_ending_to: str | Unset = UNSET,
    interval_repeat_hour_flag: bool | Unset = UNSET,
    settlement_point: str | Unset = UNSET,
    settlement_point_type: str | Unset = UNSET,
    lmp_from: float | Unset = UNSET,
    lmp_to: float | Unset = UNSET,
    page: int | Unset = UNSET,
    size: int | Unset = UNSET,
    sort: str | Unset = UNSET,
    dir_: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["RTDTimestampFrom"] = rtd_timestamp_from

    params["RTDTimestampTo"] = rtd_timestamp_to

    params["repeatHourFlag"] = repeat_hour_flag

    params["intervalIdFrom"] = interval_id_from

    params["intervalIdTo"] = interval_id_to

    params["intervalEndingFrom"] = interval_ending_from

    params["intervalEndingTo"] = interval_ending_to

    params["intervalRepeatHourFlag"] = interval_repeat_hour_flag

    params["settlementPoint"] = settlement_point

    params["settlementPointType"] = settlement_point_type

    params["LMPFrom"] = lmp_from

    params["LMPTo"] = lmp_to

    params["page"] = page

    params["size"] = size

    params["sort"] = sort

    params["dir"] = dir_

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/np6-970-cd/rtd_lmp_node_zone_hub",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Exception_ | Report | None:
    if response.status_code == 200:
        response_200 = Report.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Exception_.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = Exception_.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = Exception_.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Exception_ | Report]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    rtd_timestamp_from: str | Unset = UNSET,
    rtd_timestamp_to: str | Unset = UNSET,
    repeat_hour_flag: bool | Unset = UNSET,
    interval_id_from: int | Unset = UNSET,
    interval_id_to: int | Unset = UNSET,
    interval_ending_from: str | Unset = UNSET,
    interval_ending_to: str | Unset = UNSET,
    interval_repeat_hour_flag: bool | Unset = UNSET,
    settlement_point: str | Unset = UNSET,
    settlement_point_type: str | Unset = UNSET,
    lmp_from: float | Unset = UNSET,
    lmp_to: float | Unset = UNSET,
    page: int | Unset = UNSET,
    size: int | Unset = UNSET,
    sort: str | Unset = UNSET,
    dir_: str | Unset = UNSET,
) -> Response[Exception_ | Report]:
    """RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs

     RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs

    Args:
        rtd_timestamp_from (str | Unset):
        rtd_timestamp_to (str | Unset):
        repeat_hour_flag (bool | Unset):
        interval_id_from (int | Unset):
        interval_id_to (int | Unset):
        interval_ending_from (str | Unset):
        interval_ending_to (str | Unset):
        interval_repeat_hour_flag (bool | Unset):
        settlement_point (str | Unset):
        settlement_point_type (str | Unset):
        lmp_from (float | Unset):
        lmp_to (float | Unset):
        page (int | Unset):
        size (int | Unset):
        sort (str | Unset):
        dir_ (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Exception_ | Report]
    """

    kwargs = _get_kwargs(
        rtd_timestamp_from=rtd_timestamp_from,
        rtd_timestamp_to=rtd_timestamp_to,
        repeat_hour_flag=repeat_hour_flag,
        interval_id_from=interval_id_from,
        interval_id_to=interval_id_to,
        interval_ending_from=interval_ending_from,
        interval_ending_to=interval_ending_to,
        interval_repeat_hour_flag=interval_repeat_hour_flag,
        settlement_point=settlement_point,
        settlement_point_type=settlement_point_type,
        lmp_from=lmp_from,
        lmp_to=lmp_to,
        page=page,
        size=size,
        sort=sort,
        dir_=dir_,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    rtd_timestamp_from: str | Unset = UNSET,
    rtd_timestamp_to: str | Unset = UNSET,
    repeat_hour_flag: bool | Unset = UNSET,
    interval_id_from: int | Unset = UNSET,
    interval_id_to: int | Unset = UNSET,
    interval_ending_from: str | Unset = UNSET,
    interval_ending_to: str | Unset = UNSET,
    interval_repeat_hour_flag: bool | Unset = UNSET,
    settlement_point: str | Unset = UNSET,
    settlement_point_type: str | Unset = UNSET,
    lmp_from: float | Unset = UNSET,
    lmp_to: float | Unset = UNSET,
    page: int | Unset = UNSET,
    size: int | Unset = UNSET,
    sort: str | Unset = UNSET,
    dir_: str | Unset = UNSET,
) -> Exception_ | Report | None:
    """RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs

     RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs

    Args:
        rtd_timestamp_from (str | Unset):
        rtd_timestamp_to (str | Unset):
        repeat_hour_flag (bool | Unset):
        interval_id_from (int | Unset):
        interval_id_to (int | Unset):
        interval_ending_from (str | Unset):
        interval_ending_to (str | Unset):
        interval_repeat_hour_flag (bool | Unset):
        settlement_point (str | Unset):
        settlement_point_type (str | Unset):
        lmp_from (float | Unset):
        lmp_to (float | Unset):
        page (int | Unset):
        size (int | Unset):
        sort (str | Unset):
        dir_ (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Exception_ | Report
    """

    return sync_detailed(
        client=client,
        rtd_timestamp_from=rtd_timestamp_from,
        rtd_timestamp_to=rtd_timestamp_to,
        repeat_hour_flag=repeat_hour_flag,
        interval_id_from=interval_id_from,
        interval_id_to=interval_id_to,
        interval_ending_from=interval_ending_from,
        interval_ending_to=interval_ending_to,
        interval_repeat_hour_flag=interval_repeat_hour_flag,
        settlement_point=settlement_point,
        settlement_point_type=settlement_point_type,
        lmp_from=lmp_from,
        lmp_to=lmp_to,
        page=page,
        size=size,
        sort=sort,
        dir_=dir_,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    rtd_timestamp_from: str | Unset = UNSET,
    rtd_timestamp_to: str | Unset = UNSET,
    repeat_hour_flag: bool | Unset = UNSET,
    interval_id_from: int | Unset = UNSET,
    interval_id_to: int | Unset = UNSET,
    interval_ending_from: str | Unset = UNSET,
    interval_ending_to: str | Unset = UNSET,
    interval_repeat_hour_flag: bool | Unset = UNSET,
    settlement_point: str | Unset = UNSET,
    settlement_point_type: str | Unset = UNSET,
    lmp_from: float | Unset = UNSET,
    lmp_to: float | Unset = UNSET,
    page: int | Unset = UNSET,
    size: int | Unset = UNSET,
    sort: str | Unset = UNSET,
    dir_: str | Unset = UNSET,
) -> Response[Exception_ | Report]:
    """RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs

     RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs

    Args:
        rtd_timestamp_from (str | Unset):
        rtd_timestamp_to (str | Unset):
        repeat_hour_flag (bool | Unset):
        interval_id_from (int | Unset):
        interval_id_to (int | Unset):
        interval_ending_from (str | Unset):
        interval_ending_to (str | Unset):
        interval_repeat_hour_flag (bool | Unset):
        settlement_point (str | Unset):
        settlement_point_type (str | Unset):
        lmp_from (float | Unset):
        lmp_to (float | Unset):
        page (int | Unset):
        size (int | Unset):
        sort (str | Unset):
        dir_ (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Exception_ | Report]
    """

    kwargs = _get_kwargs(
        rtd_timestamp_from=rtd_timestamp_from,
        rtd_timestamp_to=rtd_timestamp_to,
        repeat_hour_flag=repeat_hour_flag,
        interval_id_from=interval_id_from,
        interval_id_to=interval_id_to,
        interval_ending_from=interval_ending_from,
        interval_ending_to=interval_ending_to,
        interval_repeat_hour_flag=interval_repeat_hour_flag,
        settlement_point=settlement_point,
        settlement_point_type=settlement_point_type,
        lmp_from=lmp_from,
        lmp_to=lmp_to,
        page=page,
        size=size,
        sort=sort,
        dir_=dir_,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    rtd_timestamp_from: str | Unset = UNSET,
    rtd_timestamp_to: str | Unset = UNSET,
    repeat_hour_flag: bool | Unset = UNSET,
    interval_id_from: int | Unset = UNSET,
    interval_id_to: int | Unset = UNSET,
    interval_ending_from: str | Unset = UNSET,
    interval_ending_to: str | Unset = UNSET,
    interval_repeat_hour_flag: bool | Unset = UNSET,
    settlement_point: str | Unset = UNSET,
    settlement_point_type: str | Unset = UNSET,
    lmp_from: float | Unset = UNSET,
    lmp_to: float | Unset = UNSET,
    page: int | Unset = UNSET,
    size: int | Unset = UNSET,
    sort: str | Unset = UNSET,
    dir_: str | Unset = UNSET,
) -> Exception_ | Report | None:
    """RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs

     RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs

    Args:
        rtd_timestamp_from (str | Unset):
        rtd_timestamp_to (str | Unset):
        repeat_hour_flag (bool | Unset):
        interval_id_from (int | Unset):
        interval_id_to (int | Unset):
        interval_ending_from (str | Unset):
        interval_ending_to (str | Unset):
        interval_repeat_hour_flag (bool | Unset):
        settlement_point (str | Unset):
        settlement_point_type (str | Unset):
        lmp_from (float | Unset):
        lmp_to (float | Unset):
        page (int | Unset):
        size (int | Unset):
        sort (str | Unset):
        dir_ (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Exception_ | Report
    """

    return (
        await asyncio_detailed(
            client=client,
            rtd_timestamp_from=rtd_timestamp_from,
            rtd_timestamp_to=rtd_timestamp_to,
            repeat_hour_flag=repeat_hour_flag,
            interval_id_from=interval_id_from,
            interval_id_to=interval_id_to,
            interval_ending_from=interval_ending_from,
            interval_ending_to=interval_ending_to,
            interval_repeat_hour_flag=interval_repeat_hour_flag,
            settlement_point=settlement_point,
            settlement_point_type=settlement_point_type,
            lmp_from=lmp_from,
            lmp_to=lmp_to,
            page=page,
            size=size,
            sort=sort,
            dir_=dir_,
        )
    ).parsed
