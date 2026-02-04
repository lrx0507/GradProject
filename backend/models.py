from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB  # PostgreSQL专属JSONB类型
from sqlalchemy.sql import func
from geoalchemy2 import Geometry  # 空间类型依赖，适配PostGIS
from database import Base  # 继承基础模型类

# 1. POI模型（徒步场景专属，核心业务表）
class Poi(Base):
    __tablename__ = "pois"  # 数据库表名（小写+复数，PostgreSQL规范）
    id = Column(Integer, primary_key=True, index=True, comment="POI唯一ID")
    name = Column(String(100), nullable=False, comment="POI名称")
    type = Column(String(50), nullable=False, comment="POI类型：entrance/view/rest/exit")
    description = Column(Text, nullable=True, comment="POI描述")
    geom = Column(Geometry("POINT", srid=4326), nullable=False, comment="空间点坐标（WGS84/经纬度）")
    is_active = Column(Boolean, default=True, comment="是否启用：True-启用，False-禁用")
    create_time = Column(DateTime, default=func.now(), comment="创建时间（自动生成）")

# 2. 路网点模型（路网拓扑结构-节点，如路口、拐点）
# 路网点模型（路网拓扑结构-节点，如路口、拐点）
class NetworkNode(Base):
    __tablename__ = "network_nodes"
    id = Column(Integer, primary_key=True, index=True, comment="节点唯一ID")
    geom = Column(Geometry("POINT", srid=4326), nullable=False, comment="节点空间坐标（WGS84/经纬度）")
    degree = Column(Integer, default=0, comment="节点度数（连接的边数量，拓扑构建时自动计算）")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")

# 3. 路网边模型（路网拓扑结构-边，连接两个节点的路径）
class NetworkEdge(Base):
    __tablename__ = "network_edges"
    id = Column(Integer, primary_key=True, index=True, comment="边唯一ID")
    source = Column(Integer, nullable=False, comment="起点节点ID（关联network_nodes.id）")
    target = Column(Integer, nullable=False, comment="终点节点ID（关联network_nodes.id）")
    geom = Column(Geometry("LINESTRING", srid=4326), nullable=False, comment="路径线坐标（WGS84）")
    length_m = Column(Numeric(10,2), nullable=False, comment="路径长度（米）")
    type = Column(String(20), nullable=False, comment="道路类型：主路/支路/POI连接线")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")

# 4. 高程点模型（地形数据-海拔，由DEM文件导入）
class ElevationPoint(Base):
    __tablename__ = "elevation_points"
    id = Column(Integer, primary_key=True, index=True, comment="高程点唯一ID")
    geom = Column(Geometry("POINT", srid=4326), nullable=False, comment="空间点坐标（WGS84）")
    elevation_m = Column(Numeric(10,2), nullable=False, comment="海拔高度（米）")
    create_time = Column(DateTime, default=func.now(), comment="导入时间")

# 5. 坡度点模型（地形数据-坡度，由DEM文件派生）
class SlopePoint(Base):
    __tablename__ = "slope_points"
    id = Column(Integer, primary_key=True, index=True, comment="坡度点唯一ID")
    geom = Column(Geometry("POINT", srid=4326), nullable=False, comment="空间点坐标（WGS84）")
    slope_deg = Column(Numeric(5,2), nullable=False, comment="坡度（度），范围0-90")
    create_time = Column(DateTime, default=func.now(), comment="导入时间")

# 6. 特色路线模型（组合POI的推荐路线，如观景路线、休闲路线）
class TourRoute(Base):
    __tablename__ = "tour_routes"
    id = Column(Integer, primary_key=True, index=True, comment="路线唯一ID")
    name = Column(String(100), nullable=False, comment="路线名称")
    description = Column(Text, nullable=True, comment="路线描述")
    cover_image = Column(String(255), nullable=True, comment="路线封面图URL")
    poi_sequence = Column(JSONB, nullable=False, comment="途经POI序列：[poi_id1, poi_id2, ...]")
    is_active = Column(Boolean, default=True, comment="是否启用")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")

# 7. 系统配置模型（全局参数，如坡度权重α、路径偏好等）
class SystemConfig(Base):
    __tablename__ = "system_config"
    key = Column(String(50), primary_key=True, comment="配置键（如slope_weight_alpha）")
    value = Column(Text, nullable=False, comment="配置值（字符串格式，可解析为数字/JSON）")
    description = Column(Text, nullable=True, comment="配置说明")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间（自动触发）")