"""ServerV2Node DTO，接口视图，不做持久化。"""

from typing import Any

from sqlmodel import SQLModel


class ServerV2NodeCreate(SQLModel):
    group_id: list[int] | str
    route_id: list[int] | str | None = None
    name: str
    parent_id: int | None = None
    host: str
    listen_ip: str = "0.0.0.0"
    port: str
    server_port: int
    tags: list[str] | str | None = None
    rate: str = "1"
    show: bool = False
    sort: int | None = None
    protocol: str
    tls: int
    tls_settings: dict | str | None = None
    flow: str | None = None
    network: str
    network_settings: dict | str | None = None
    encryption: str | None = None
    encryption_settings: dict | str | None = None
    disable_sni: bool = False
    udp_relay_mode: str | None = None
    zero_rtt_handshake: bool = False
    congestion_control: str | None = None
    cipher: str | None = None
    up_mbps: int = 0
    down_mbps: int = 0
    obfs: str | None = None
    obfs_password: str | None = None
    padding_scheme: list[str] | str | None = None


class ServerV2NodeUpdate(SQLModel):
    group_id: list[int] | str | None = None
    route_id: list[int] | str | None = None
    name: str | None = None
    parent_id: int | None = None
    host: str | None = None
    listen_ip: str | None = None
    port: str | None = None
    server_port: int | None = None
    tags: list[str] | str | None = None
    rate: str | None = None
    show: bool | None = None
    sort: int | None = None
    protocol: str | None = None
    tls: int | None = None
    tls_settings: dict | str | None = None
    flow: str | None = None
    network: str | None = None
    network_settings: dict | str | None = None
    encryption: str | None = None
    encryption_settings: dict | str | None = None
    disable_sni: bool | None = None
    udp_relay_mode: str | None = None
    zero_rtt_handshake: bool | None = None
    congestion_control: str | None = None
    cipher: str | None = None
    up_mbps: int | None = None
    down_mbps: int | None = None
    obfs: str | None = None
    obfs_password: str | None = None
    padding_scheme: list[str] | str | None = None


class ServerV2NodePublic(SQLModel):
    """V2Ray 节点列表公开视图。"""

    id: int
    created_at: int


class ServerV2NodeRead(SQLModel):
    """V2Ray 节点详情视图。"""

    id: int
    group_id: list[int] | str
    route_id: list[int] | str | None
    name: str
    parent_id: int | None
    host: str
    listen_ip: str
    port: str
    server_port: int
    tags: list[str] | str | None
    rate: str
    show: bool
    sort: int | None
    protocol: str
    tls: int
    tls_settings: dict[str, Any] | str | None
    flow: str | None
    network: str
    network_settings: dict[str, Any] | str | None
    encryption: str | None
    encryption_settings: dict[str, Any] | str | None
    disable_sni: bool
    udp_relay_mode: str | None
    zero_rtt_handshake: bool
    congestion_control: str | None
    cipher: str | None
    up_mbps: int
    down_mbps: int
    obfs: str | None
    obfs_password: str | None
    padding_scheme: list[str] | str | None
    created_at: int
    updated_at: int
