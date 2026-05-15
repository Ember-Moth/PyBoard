"""ServerV2Node 字段全集，不含 id/关系/系统字段。对应 V2Ray 节点表 `server_v2node`。"""

from typing import Any

from sqlmodel import Field, SQLModel

from app.models._columns import jsonb_field


class ServerV2NodeBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    group_id: Any = jsonb_field(nullable=False, default_factory=list)  # 所属分组 ID
    route_id: Any = jsonb_field()  # 路由规则 ID
    name: str = Field(max_length=255)  # 节点名称
    parent_id: int | None = None  # 父节点 ID
    host: str = Field(max_length=255)  # 节点 IP/域名
    listen_ip: str = Field(default="0.0.0.0", max_length=255)  # 监听 IP
    port: str = Field(max_length=11)  # 端口
    server_port: int  # 服务端口
    tags: Any = jsonb_field()  # 标签
    rate: str = Field(max_length=11)  # 倍率
    show: bool = False  # 是否展示
    sort: int | None = None  # 排序权重
    protocol: str = Field(max_length=24)  # 协议类型
    tls: int  # TLS 类型
    tls_settings: Any = jsonb_field()  # TLS 配置
    flow: str | None = Field(default=None, max_length=64)  # VLESS 流控
    network: str = Field(max_length=11)  # 传输类型
    network_settings: Any = jsonb_field()  # 传输配置
    encryption: str | None = Field(default=None, max_length=64)  # VLESS 加密
    encryption_settings: Any = jsonb_field()  # VLESS 加密配置
    disable_sni: bool = False  # Tuic 禁用 SNI
    udp_relay_mode: str | None = Field(default=None, max_length=64)  # Tuic UDP 中继模式
    zero_rtt_handshake: bool = False  # Tuic 0-RTT 握手
    congestion_control: str | None = Field(default=None, max_length=64)  # Tuic 拥塞控制
    cipher: str | None = Field(default=None, max_length=64)  # Shadowsocks 加密方式
    up_mbps: int  # Hysteria 上行带宽
    down_mbps: int  # Hysteria 下行带宽
    obfs: str | None = Field(default=None, max_length=64)  # 混淆方式/密码
    obfs_password: str | None = Field(default=None, max_length=255)  # Hysteria2 混淆密码
    padding_scheme: Any = jsonb_field()  # AnyTLS 填充配置
