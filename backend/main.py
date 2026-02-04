# 基础依赖导入
from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from shapely.geometry import Point, LineString
from geoalchemy2.shape import from_shape
import re

# 原有依赖保留（FastAPI/NetworkX/numpy/geoalchemy2等）
import gpxpy
import gpxpy.gpx
from fastapi.responses import StreamingResponse
import io
from datetime import datetime

# 项目模块导入
import models
import database

# 路径规划核心依赖
import networkx as nx
import numpy as np
# 原有依赖保留（FastAPI/SQLAlchemy/PostGIS等）
from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from shapely.geometry import Point, LineString
from geoalchemy2.shape import from_shape
import re
import models
import database
from fastapi.middleware.cors import CORSMiddleware

# 跨域中间件导入
from fastapi.middleware.cors import CORSMiddleware

# 初始化FastAPI应用
app = FastAPI(title="徒步路线系统API", version="1.0.0", description="包含POI、路网、地形、系统配置核心接口")

# 自动创建数据库表（开发阶段使用，生产环境建议用Alembic做数据迁移）
models.Base.metadata.create_all(bind=database.engine)

# 数据库会话依赖（每次请求自动创建/关闭，避免连接泄漏）
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 配置CORS跨域（允许前端Vite默认端口5173访问，生产环境替换为实际域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法：GET/POST/PUT/DELETE
    allow_headers=["*"],  # 允许所有请求头
)

# -------------------------- 基础健康检查接口 --------------------------
@app.get("/", summary="服务健康检查")
def health_check():
    return {"code": 200, "message": "徒步路线系统后端服务正常运行", "data": None}

# -------------------------- POI 核心CRUD接口 --------------------------
@app.get("/pois", summary="查询所有POI（支持筛选启用状态）")
def get_all_pois(
    db: Session = Depends(get_db),
    is_active: bool = True  # 可选参数：默认查询启用的POI
):
    pois = db.query(models.Poi).filter(models.Poi.is_active == is_active).all()
    # 解析空间坐标为前端可识别的经纬度
    result = []
    for poi in pois:
        geom_wkt = db.execute(func.ST_AsText(poi.geom)).scalar()
        lng, lat = _parse_wkt_to_lnglat(geom_wkt)
        result.append({
            "id": poi.id,
            "name": poi.name,
            "type": poi.type,
            "description": poi.description or "",
            "lat": lat,
            "lng": lng,
            "is_active": poi.is_active,
            "create_time": poi.create_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return {"code": 200, "message": "查询成功", "data": result}

@app.get("/pois/{poi_id}", summary="根据ID查询单个POI")
def get_poi_by_id(poi_id: int, db: Session = Depends(get_db)):
    poi = db.query(models.Poi).filter(models.Poi.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail=f"POI不存在，ID：{poi_id}")
    # 解析空间坐标
    geom_wkt = db.execute(func.ST_AsText(poi.geom)).scalar()
    lng, lat = _parse_wkt_to_lnglat(geom_wkt)
    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "id": poi.id,
            "name": poi.name,
            "type": poi.type,
            "description": poi.description or "",
            "lat": lat,
            "lng": lng,
            "is_active": poi.is_active,
            "create_time": poi.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

@app.post("/pois", summary="新增POI")
def create_poi(
    poi_data: dict = Body(...),  # 接收前端JSON数据
    db: Session = Depends(get_db)
):
    # 1. 校验必填字段
    required_fields = ["name", "type", "lat", "lng"]
    for field in required_fields:
        if field not in poi_data or not str(poi_data[field]).strip():
            raise HTTPException(status_code=400, detail=f"缺失必填字段或字段为空：{field}")
    # 2. 校验POI类型合法性
    valid_types = ["entrance", "view", "rest", "exit"]
    if poi_data["type"] not in valid_types:
        raise HTTPException(status_code=400, detail=f"POI类型无效，仅支持：{valid_types}")
    # 3. 校验经纬度格式（数字类型）
    try:
        lat = float(poi_data["lat"])
        lng = float(poi_data["lng"])
        # 经纬度范围校验（WGS84规范）
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise HTTPException(status_code=400, detail="经纬度超出合法范围（lat：-90~90，lng：-180~180）")
    except ValueError:
        raise HTTPException(status_code=400, detail="经纬度必须为数字格式")
    # 4. 经纬度转PostGIS空间点（lng在前，lat在后，符合WGS84）
    point = Point(lng, lat)
    geom = from_shape(point, srid=4326)
    # 5. 创建POI对象并入库
    db_poi = models.Poi(
        name=poi_data["name"].strip(),
        type=poi_data["type"],
        description=poi_data.get("description", "").strip(),
        geom=geom,
        is_active=poi_data.get("is_active", True)
    )
    db.add(db_poi)
    db.commit()
    db.refresh(db_poi)
    # 6. 返回创建结果（含解析后的经纬度）
    return {
        "code": 201,
        "message": "POI创建成功",
        "data": {
            "id": db_poi.id,
            "name": db_poi.name,
            "type": db_poi.type,
            "lat": lat,
            "lng": lng,
            "is_active": db_poi.is_active
        }
    }

@app.put("/pois/{poi_id}", summary="修改POI（支持名称、类型、描述、启用状态）")
def update_poi(
    poi_id: int,
    poi_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    # 1. 检查POI是否存在
    db_poi = db.query(models.Poi).filter(models.Poi.id == poi_id).first()
    if not db_poi:
        raise HTTPException(status_code=404, detail=f"POI不存在，ID：{poi_id}")
    # 2. 校验并更新类型（若传参）
    if "type" in poi_data and poi_data["type"]:
        valid_types = ["entrance", "view", "rest", "exit"]
        if poi_data["type"] not in valid_types:
            raise HTTPException(status_code=400, detail=f"POI类型无效，仅支持：{valid_types}")
        db_poi.type = poi_data["type"]
    # 3. 更新名称、描述（若传参，去空格）
    if "name" in poi_data and poi_data["name"]:
        db_poi.name = poi_data["name"].strip()
    if "description" in poi_data:
        db_poi.description = poi_data["description"].strip()
    # 4. 更新启用状态（若传参）
    if "is_active" in poi_data:
        db_poi.is_active = bool(poi_data["is_active"])
    # 5. 提交更新
    db.commit()
    db.refresh(db_poi)
    # 6. 解析空间坐标返回
    geom_wkt = db.execute(func.ST_AsText(db_poi.geom)).scalar()
    lng, lat = _parse_wkt_to_lnglat(geom_wkt)
    return {
        "code": 200,
        "message": "POI更新成功",
        "data": {
            "id": db_poi.id,
            "name": db_poi.name,
            "type": db_poi.type,
            "description": db_poi.description or "",
            "lat": lat,
            "lng": lng,
            "is_active": db_poi.is_active
        }
    }

@app.delete("/pois/{poi_id}", summary="删除POI（物理删除，生产环境可改为逻辑删除）")
def delete_poi(poi_id: int, db: Session = Depends(get_db)):
    db_poi = db.query(models.Poi).filter(models.Poi.id == poi_id).first()
    if not db_poi:
        raise HTTPException(status_code=404, detail=f"POI不存在，ID：{poi_id}")
    db.delete(db_poi)
    db.commit()
    return {"code": 200, "message": f"POI删除成功，ID：{poi_id}", "data": None}

# -------------------------- 路网（节点+边）核心接口 --------------------------
# 1. 路网点接口
@app.get("/network/nodes", summary="查询所有路网点")
def get_all_nodes(db: Session = Depends(get_db)):
    nodes = db.query(models.NetworkNode).all()
    result = []
    for node in nodes:
        geom_wkt = db.execute(func.ST_AsText(node.geom)).scalar()
        lng, lat = _parse_wkt_to_lnglat(geom_wkt)
        result.append({
            "id": node.id,
            "lat": lat,
            "lng": lng,
            "degree": node.degree,
            "create_time": node.create_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return {"code": 200, "message": "查询成功", "data": result}

@app.post("/network/nodes", summary="新增路网点")
def create_node(
    node_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    # 校验经纬度
    try:
        lat = float(node_data["lat"])
        lng = float(node_data["lng"])
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise HTTPException(status_code=400, detail="经纬度超出合法范围")
    except (KeyError, ValueError):
        raise HTTPException(status_code=400, detail="经纬度为必填项，且必须为数字格式")
    # 转空间点
    point = Point(lng, lat)
    geom = from_shape(point, srid=4326)
    # 入库
    db_node = models.NetworkNode(geom=geom, degree=node_data.get("degree", 0))
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return {
        "code": 201,
        "message": "路网点创建成功",
        "data": {"id": db_node.id, "lat": lat, "lng": lng, "degree": db_node.degree}
    }

@app.delete("/network/nodes/{node_id}", summary="删除路网点（需确保无关联边）")
def delete_node(node_id: int, db: Session = Depends(get_db)):
    # 检查节点是否存在
    node = db.query(models.NetworkNode).filter(models.NetworkNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail=f"路网点不存在，ID：{node_id}")
    # 检查是否有关联的边（外键约束，避免孤立边）
    has_edge = db.query(models.NetworkEdge).filter(
        (models.NetworkEdge.source == node_id) | (models.NetworkEdge.target == node_id)
    ).first()
    if has_edge:
        raise HTTPException(status_code=400, detail=f"路网点关联有路网边，无法直接删除（ID：{node_id}）")
    # 删除节点
    db.delete(node)
    db.commit()
    return {"code": 200, "message": f"路网点删除成功，ID：{node_id}", "data": None}

# 2. 路网边接口
@app.get("/network/edges", summary="查询所有路网边")
def get_all_edges(db: Session = Depends(get_db)):
    edges = db.query(models.NetworkEdge).all()
    result = []
    for edge in edges:
        # 解析线坐标为经纬度数组
        geom_wkt = db.execute(func.ST_AsText(edge.geom)).scalar()
        coords = _parse_linestring_wkt(geom_wkt)
        result.append({
            "id": edge.id,
            "source": edge.source,  # 起点节点ID
            "target": edge.target,  # 终点节点ID
            "coords": coords,       # 路径经纬度数组：[[lng1,lat1], [lng2,lat2], ...]
            "length_m": float(edge.length_m),
            "type": edge.type,
            "create_time": edge.create_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return {"code": 200, "message": "查询成功", "data": result}

@app.post("/network/edges", summary="新增路网边（需先创建起点/终点节点）")
def create_edge(
    edge_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    # 1. 校验必填字段
    required_fields = ["source", "target", "coords", "length_m", "type"]
    for field in required_fields:
        if field not in edge_data or not edge_data[field]:
            raise HTTPException(status_code=400, detail=f"缺失必填字段：{field}")
    # 2. 校验起点/终点节点是否存在
    source = edge_data["source"]
    target = edge_data["target"]
    if not db.query(models.NetworkNode).filter(models.NetworkNode.id == source).first():
        raise HTTPException(status_code=404, detail=f"起点节点不存在，ID：{source}")
    if not db.query(models.NetworkNode).filter(models.NetworkNode.id == target).first():
        raise HTTPException(status_code=404, detail=f"终点节点不存在，ID：{target}")
    # 3. 校验路径坐标（二维数组，经纬度）
    try:
        coords = edge_data["coords"]
        if not isinstance(coords, list) or len(coords) < 2:
            raise ValueError("坐标数组至少包含2个点")
        # 转换为shapely LineString（lng在前，lat在后）
        line_coords = [(float(p[0]), float(p[1])) for p in coords]
        line = LineString(line_coords)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"坐标格式无效：{str(e)}")
    # 4. 校验长度和类型
    try:
        length_m = float(edge_data["length_m"])
        if length_m <= 0:
            raise HTTPException(status_code=400, detail="路径长度必须大于0")
    except ValueError:
        raise HTTPException(status_code=400, detail="路径长度必须为数字")
    valid_edge_types = ["主路", "支路", "POI连接线"]
    if edge_data["type"] not in valid_edge_types:
        raise HTTPException(status_code=400, detail=f"道路类型无效，仅支持：{valid_edge_types}")
    # 5. 转PostGIS空间线
    geom = from_shape(line, srid=4326)
    # 6. 入库并更新节点度数
    db_edge = models.NetworkEdge(
        source=source,
        target=target,
        geom=geom,
        length_m=length_m,
        type=edge_data["type"]
    )
    db.add(db_edge)
    # 更新起点/终点节点度数
    db.query(models.NetworkNode).filter(models.NetworkNode.id == source).update({"degree": models.NetworkNode.degree + 1})
    db.query(models.NetworkNode).filter(models.NetworkNode.id == target).update({"degree": models.NetworkNode.degree + 1})
    # 提交事务
    db.commit()
    db.refresh(db_edge)
    return {
        "code": 201,
        "message": "路网边创建成功",
        "data": {
            "id": db_edge.id,
            "source": source,
            "target": target,
            "length_m": length_m,
            "type": db_edge.type
        }
    }

@app.delete("/network/edges/{edge_id}", summary="删除路网边（自动更新节点度数）")
def delete_edge(edge_id: int, db: Session = Depends(get_db)):
    # 1. 检查边是否存在
    edge = db.query(models.NetworkEdge).filter(models.NetworkEdge.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail=f"路网边不存在，ID：{edge_id}")
    # 2. 记录起点/终点，用于更新度数
    source = edge.source
    target = edge.target
    # 3. 删除边并更新节点度数（度数至少为0）
    db.delete(edge)
    db.query(models.NetworkNode).filter(models.NetworkNode.id == source).update({"degree": func.max(models.NetworkNode.degree - 1, 0)})
    db.query(models.NetworkNode).filter(models.NetworkNode.id == target).update({"degree": func.max(models.NetworkNode.degree - 1, 0)})
    # 提交事务
    db.commit()
    return {"code": 200, "message": f"路网边删除成功，ID：{edge_id}", "data": None}


# -------------------------- 路网拓扑构建核心接口 --------------------------
@app.post("/network/build-topology", summary="自动构建路网拓扑：从network_edges生成network_nodes并计算度数")
def build_network_topology(db: Session = Depends(get_db)):
    """
    核心逻辑：ST_Union(合并边) → ST_Node(节点化) → ST_DumpPoints(拆解节点)
    步骤：1. 清空现有network_nodes（避免重复） 2. 生成新节点 3. 计算并更新节点度数
    """
    try:
        # 步骤1：检查是否有路网边，无则直接返回
        edge_count = db.query(models.NetworkEdge).count()
        if edge_count == 0:
            raise HTTPException(status_code=400, detail="无路网边数据，请先导入/新增network_edges数据后再构建拓扑")
        
        # 步骤2：清空现有network_nodes表（保证拓扑一致性，避免旧数据干扰）
        db.query(models.NetworkNode).delete()
        db.commit()
        print(f"ℹ️  已清空现有{edge_count}条路网点数据")

        # 步骤3：核心SQL - 调用PostGIS函数生成节点，插入network_nodes
        # ST_Union(geom)：合并所有边 → ST_Node：节点化 → ST_DumpPoints：拆解为单个点
        create_nodes_sql = """
        INSERT INTO network_nodes (geom, create_time)
        SELECT 
            (ST_DumpPoints(ST_Node(ST_Union(geom)))).geom AS node_geom,
            NOW() AS create_time
        FROM network_edges;
        """
        # 执行原生SQL（PostGIS空间函数需原生执行，SQLAlchemyORM暂不支持复杂空间函数嵌套）
        db.execute(create_nodes_sql)
        db.commit()

        # 步骤4：查询生成的节点数量
        node_count = db.query(models.NetworkNode).count()
        if node_count == 0:
            raise HTTPException(status_code=500, detail="拓扑构建失败，未生成任何路网点")
        
        # 步骤5：计算并更新节点度数（核心：统计每个节点作为起点/终点的边数量）
        # 度数=该节点作为source的边数 + 作为target的边数
        update_degree_sql = """
        UPDATE network_nodes n
        SET degree = COALESCE(s.source_count, 0) + COALESCE(t.target_count, 0)
        FROM (
            SELECT source, COUNT(*) AS source_count FROM network_edges GROUP BY source
        ) s
        FULL JOIN (
            SELECT target, COUNT(*) AS target_count FROM network_edges GROUP BY target
        ) t ON s.source = t.target
        WHERE n.id = COALESCE(s.source, t.target);
        """
        db.execute(update_degree_sql)
        db.commit()

        # 步骤6：查询最终更新度数后的节点数量
        final_node_count = db.query(models.NetworkNode).count()
        return {
            "code": 200,
            "message": f"路网拓扑构建成功！",
            "data": {
                "network_edges_count": edge_count,  # 参与构建的路网边数量
                "network_nodes_count": final_node_count,  # 生成的路网点数量
                "tip": "已自动计算所有节点度数（连接的边数量）"
            }
        }

    except HTTPException as e:
        # 主动抛出的业务异常直接返回
        raise e
    except Exception as e:
        # 其他未知异常回滚事务，避免数据脏读
        db.rollback()
        print(f"❌ 拓扑构建异常：{str(e)}")
        raise HTTPException(status_code=500, detail=f"路网拓扑构建失败，异常信息：{str(e)[:200]}")

# -------------------------- 系统配置（坡度权重α）接口 --------------------------
@app.get("/system-config/{key}", summary="查询系统配置（如slope_weight_alpha：坡度权重α）")
def get_system_config(key: str, db: Session = Depends(get_db)):
    config = db.query(models.SystemConfig).filter(models.SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"配置项不存在，KEY：{key}")
    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "key": config.key,
            "value": config.value,
            "description": config.description or "",
            "update_time": config.update_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

@app.put("/system-config/{key}", summary="更新系统配置（核心：修改坡度权重α参数）")
def update_system_config(
    key: str,
    new_value: str = Body(..., embed=True),  # 单独传值，前端传{"new_value": "0.7"}
    db: Session = Depends(get_db)
):
    # 1. 检查配置项是否存在
    config = db.query(models.SystemConfig).filter(models.SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail=f"配置项不存在，KEY：{key}")
    # 2. 坡度权重α专属校验（若key为slope_weight_alpha，值必须为0-1的数字）
    if key == "slope_weight_alpha":
        try:
            alpha = float(new_value)
            if not (0 <= alpha <= 1):
                raise HTTPException(status_code=400, detail="坡度权重α必须为0~1之间的数字（0：不考虑坡度，1：优先坡度）")
        except ValueError:
            raise HTTPException(status_code=400, detail="坡度权重α必须为数字格式")
    # 3. 更新配置值（自动触发update_time）
    config.value = new_value.strip()
    db.commit()
    db.refresh(config)
    return {
        "code": 200,
        "message": "配置更新成功",
        "data": {
            "key": config.key,
            "value": config.value,
            "update_time": config.update_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

# -------------------------- 工具函数（内部使用，不对外暴露） --------------------------
def _parse_wkt_to_lnglat(wkt: str) -> (float, float):
    """解析WKT格式POINT为经纬度（lng, lat），异常返回(0,0)"""
    if not wkt or not wkt.startswith("POINT"):
        return 0.0, 0.0
    try:
        # 匹配POINT (lng lat) 格式，提取数字
        coords = re.findall(r"POINT\s*\((-?\d+\.?\d*)\s+(-?\d+\.?\d*)\)", wkt)[0]
        return float(coords[0]), float(coords[1])
    except (IndexError, ValueError):
        return 0.0, 0.0

def _parse_linestring_wkt(wkt: str) -> list:
    """解析WKT格式LINESTRING为经纬度二维数组[[lng1,lat1], ...]，异常返回空数组"""
    if not wkt or not wkt.startswith("LINESTRING"):
        return []
    try:
        # 提取括号内的坐标串，按逗号分割
        coord_str = re.findall(r"LINESTRING\s*\((.*)\)", wkt)[0]
        coord_pairs = coord_str.split(",")
        # 解析每个坐标对
        coords = []
        for pair in coord_pairs:
            lng, lat = pair.strip().split()
            coords.append([float(lng), float(lat)])
        return coords
    except (IndexError, ValueError):
        return []

        # -------------------------- 系统配置自动初始化（坡度权重α） --------------------------
@app.on_event("startup")
def init_default_config(db: Session = Depends(get_db)):
    """FastAPI启动事件：服务启动时自动初始化默认配置（仅当配置项不存在时执行）"""
    # 手动创建数据库会话（启动事件中无法直接使用依赖注入，需手动初始化）
    db = database.SessionLocal()
    try:
        # 检查坡度权重α配置是否存在
        alpha_config = db.query(models.SystemConfig).filter(models.SystemConfig.key == "slope_weight_alpha").first()
        if not alpha_config:
            # 不存在则插入默认值（0.5，兼顾距离和坡度）
            default_alpha = models.SystemConfig(
                key="slope_weight_alpha",
                value="0.5",
                description="坡度权重α：0-1，值越大越优先选择低坡度路径，0表示不考虑坡度"
            )
            db.add(default_alpha)
            db.commit()
            print("✅ 系统配置初始化成功：已插入默认坡度权重α=0.5")
        else:
            print(f"✅ 坡度权重α配置已存在，当前值：{alpha_config.value}")
    except Exception as e:
        db.rollback()
        print(f"⚠️  系统配置初始化失败：{str(e)}")
    finally:
        db.close()


# -------------------------- 路径规划工具函数（内部调用） --------------------------
def get_edge_slope_avg(edge_geom, db: Session) -> float:
    """
    计算单条路网边的平均坡度slope_avg
    :param edge_geom: 路网边的PostGIS Geometry(LINESTRING)对象
    :param db: 数据库会话
    :return: 平均坡度（度），无坡度点时返回0
    """
    try:
        # 空间关联：查询与路网边相交的所有坡度点（ST_Intersects实现空间匹配）
        slope_points = db.query(models.SlopePoint.slope_deg).filter(
            func.ST_Intersects(models.SlopePoint.geom, edge_geom)
        ).all()
        if not slope_points:
            return 0.0  # 无坡度点，默认坡度为0
        # 提取坡度值并计算平均值（NumPy高效计算）
        slope_vals = np.array([p[0] for p in slope_points], dtype=np.float64)
        slope_avg = np.mean(slope_vals).round(2)  # 保留2位小数
        return max(slope_avg, 0.0)  # 坡度非负，避免异常值
    except Exception as e:
        print(f"计算边平均坡度失败：{str(e)}")
        return 0.0

def build_networkx_graph(db: Session) -> nx.DiGraph:
    """
    构建NetworkX有向内存图（支持单向路，无向路可添加双向边）
    :param db: 数据库会话
    :return: 带边属性的NetworkX DiGraph对象
    """
    # 初始化有向图
    G = nx.DiGraph()
    # 1. 加载所有路网边
    edges = db.query(models.NetworkEdge).all()
    if not edges:
        raise HTTPException(status_code=400, detail="无路网边数据，无法构建路径规划图")
    # 2. 遍历每条边，添加到图中并计算属性
    for edge in edges:
        # 计算当前边的平均坡度
        slope_avg = get_edge_slope_avg(edge.geom, db)
        # 向图中添加边：source→target，挂载基础属性
        G.add_edge(
            edge.source,  # 起点节点ID
            edge.target,  # 终点节点ID
            length_m=float(edge.length_m),
            slope_avg=slope_avg,
            edge_id=edge.id,
            type=edge.type
        )
        # 若为无向路（主路/支路），添加反向边（target→source），属性与正向边一致
        if edge.type in ["主路", "支路"]:
            G.add_edge(
                edge.target,
                edge.source,
                length_m=float(edge.length_m),
                slope_avg=slope_avg,
                edge_id=edge.id,
                type=edge.type
            )
    # 3. 检查图是否有节点
    if G.number_of_nodes() == 0:
        raise HTTPException(status_code=400, detail="路径规划图无节点，路网数据异常")
    print(f"✅ NetworkX图构建成功：节点数{G.number_of_nodes()}，边数{G.number_of_edges()}")
    return G

def get_slope_weight_alpha(db: Session) -> float:
    """
    从系统配置获取坡度权重α，校验值范围0~1
    :return: 坡度权重α（浮点数）
    """
    alpha_config = db.query(models.SystemConfig).filter(
        models.SystemConfig.key == "slope_weight_alpha"
    ).first()
    if not alpha_config:
        raise HTTPException(status_code=404, detail="系统配置中未找到坡度权重α（slope_weight_alpha）")
    try:
        alpha = float(alpha_config.value)
        # 校验α范围，超出则强制设为0.5（默认值）
        if not (0 <= alpha <= 1):
            alpha = 0.5
            print(f"⚠️  坡度权重α超出0~1范围，强制设为默认值0.5")
        return alpha
    except ValueError:
        raise HTTPException(status_code=400, detail="坡度权重α必须为数字格式（0~1）")


# -------------------------- 路径高程/坡度插值工具函数 --------------------------
import math
from shapely.ops import substring
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint, ST_DWithin

def haversine_distance(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """
    哈维正弦公式计算WGS84经纬度两点间的地理距离（米）
    :param lng1/lat1: 点1经纬度
    :param lng2/lat2: 点2经纬度
    :return: 两点间距离（米）
    """
    # 地球半径（米）
    R = 6371000.0
    # 角度转弧度
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    # 哈维正弦公式
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def path_20m_sampling(coord_path: list) -> list:
    """
    对路径经纬度序列做20米等距采样，生成采样点序列
    :param coord_path: 路径规划返回的coord_path（[{"node_id":x, "lng":x, "lat":x}, ...]）
    :return: 20米等距采样点序列 [{"lng":x, "lat":x, "distance_m":x}, ...]，distance_m为距起点累计距离
    """
    try:
        # 1. 提取路径经纬度，构建Shapely LineString（lng在前，lat在后）
        line_coords = [(p["lng"], p["lat"]) for p in coord_path]
        if len(line_coords) < 2:
            return []
        path_line = LineString(line_coords)
        
        # 2. 计算路径总长度（米），基于哈维正弦公式累加
        total_length = 0.0
        for i in range(len(line_coords)-1):
            lng1, lat1 = line_coords[i]
            lng2, lat2 = line_coords[i+1]
            total_length += haversine_distance(lng1, lat1, lng2, lat2)
        if total_length < 20:
            # 路径短于20米，仅返回起点和终点
            return [
                {"lng": line_coords[0][0], "lat": line_coords[0][1], "distance_m": 0.0},
                {"lng": line_coords[-1][0], "lat": line_coords[-1][1], "distance_m": round(total_length, 2)}
            ]
        
        # 3. 20米等距采样，生成采样点
        sampling_points = []
        step = 20.0  # 采样步长（米）
        current_distance = 0.0
        
        # 添加起点
        sampling_points.append({
            "lng": line_coords[0][0],
            "lat": line_coords[0][1],
            "distance_m": 0.0
        })
        
        # 按步长采样
        while current_distance + step < total_length:
            current_distance += step
            # Shapely substring按长度比例截取点（0-1为比例）
            ratio = current_distance / total_length
            sample_point = substring(path_line, ratio, ratio, normalized=True)
            lng, lat = sample_point.x, sample_point.y
            sampling_points.append({
                "lng": round(lng, 6),
                "lat": round(lat, 6),
                "distance_m": round(current_distance, 2)
            })
        
        # 添加终点
        sampling_points.append({
            "lng": line_coords[-1][0],
            "lat": line_coords[-1][1],
            "distance_m": round(total_length, 2)
        })
        
        return sampling_points
    except Exception as e:
        print(f"路径20米采样失败：{str(e)}")
        return []

def get_point_elevation(lng: float, lat: float, db: Session, distance_threshold: float = 5.0) -> float:
    """
    空间插值获取单个采样点的高程（米），取最近N个高程点的平均值
    :param lng/lat: 采样点经纬度
    :param db: 数据库会话
    :param distance_threshold: 空间匹配阈值（米），匹配范围内最近的点
    :return: 插值高程（米），无匹配点返回0.0
    """
    try:
        # 构建PostGIS POINT对象（SRID=4326）
        point_geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        # 空间查询：匹配阈值范围内的所有高程点，按距离升序排列
        elevation_records = db.query(models.ElevationPoint.elevation_m).filter(
            ST_DWithin(models.ElevationPoint.geom, point_geom, distance_threshold)
        ).order_by(
            models.ElevationPoint.geom.distance(point_geom)
        ).limit(3).all()  # 取最近3个点做插值
        
        if not elevation_records:
            return 0.0
        # 计算平均值（简单空间插值）
        elevation_vals = [float(r[0]) for r in elevation_records]
        avg_elevation = round(sum(elevation_vals) / len(elevation_vals), 2)
        return avg_elevation
    except Exception as e:
        print(f"获取采样点高程失败：{str(e)}")
        return 0.0

def get_point_slope(lng: float, lat: float, db: Session, distance_threshold: float = 5.0) -> float:
    """
    空间插值获取单个采样点的坡度（度），取最近N个坡度点的平均值
    :param lng/lat: 采样点经纬度
    :param db: 数据库会话
    :param distance_threshold: 空间匹配阈值（米）
    :return: 插值坡度（度），无匹配点返回0.0，坡度非负
    """
    try:
        # 构建PostGIS POINT对象（SRID=4326）
        point_geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        # 空间查询：匹配阈值范围内的所有坡度点，按距离升序排列
        slope_records = db.query(models.SlopePoint.slope_deg).filter(
            ST_DWithin(models.SlopePoint.geom, point_geom, distance_threshold)
        ).order_by(
            models.SlopePoint.geom.distance(point_geom)
        ).limit(3).all()  # 取最近3个点做插值
        
        if not slope_records:
            return 0.0
        # 计算平均值，坡度非负
        slope_vals = [max(float(r[0]), 0.0) for r in slope_records]
        avg_slope = round(sum(slope_vals) / len(slope_vals), 2)
        return avg_slope
    except Exception as e:
        print(f"获取采样点坡度失败：{str(e)}")
        return 0.0

def path_interpolate_elevation_slope(sampling_points: list, db: Session) -> list:
    """
    对采样点序列批量插值高程和坡度，返回最终采样点结果
    :param sampling_points: 20米等距采样点序列（path_20m_sampling返回结果）
    :param db: 数据库会话
    :return: 带高程/坡度的采样点序列
    """
    try:
        result = []
        for point in sampling_points:
            lng = point["lng"]
            lat = point["lat"]
            # 插值高程和坡度
            elevation = get_point_elevation(lng, lat, db)
            slope = get_point_slope(lng, lat, db)
            result.append({
                "lng": lng,
                "lat": lat,
                "distance_m": point["distance_m"],  # 距起点累计距离（米）
                "elevation_m": elevation,            # 高程（米）
                "slope_deg": slope                   # 坡度（度）
            })
        return result
    except Exception as e:
        print(f"采样点高程坡度插值失败：{str(e)}")
        return []

# -------------------------- GPX导出核心工具函数 --------------------------
def create_gpx_from_path(sampling_result: list, strategy: str, statistics: dict) -> gpxpy.gpx.GPX:
    """
    从路径采样结果生成标准GPX 1.1对象
    :param sampling_result: 路径20米采样点序列（含lng/lat/elevation_m/slope_deg/distance_m）
    :param strategy: 路径规划策略（shortest/gentlest）
    :param statistics: 路径统计信息（total_length_m/avg_slope_deg等）
    :return: 初始化完成的gpxpy.GPX对象
    """
    # 1. 初始化GPX对象，设置标准属性（GPX 1.1 + WGS84坐标系）
    gpx = gpxpy.gpx.GPX()
    gpx.version = "1.1"
    gpx.creator = "徒步路线系统API"  # 生成器标识
    gpx.name = f"徒步路线_{'最短距离' if strategy == 'shortest' else '坡度最平缓'}"
    gpx.description = f"总长度：{statistics['total_length_m']}米 | 平均坡度：{statistics['avg_slope_deg']}度 | 采样点数量：{statistics['sampling_count']}个"

    # 2. 创建GPX轨迹和轨迹段（单个路径为一个轨迹段）
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = gpx.name
    gpx_track.description = gpx.description
    gpx.add_track(gpx_track)

    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.add_segment(gpx_segment)

    # 3. 遍历采样点，添加轨迹点（优先使用采样点，无数据则跳过）
    if not sampling_result:
        return gpx
    
    for point in sampling_result:
        # 3.1 初始化GPX轨迹点（纬度lat在前，经度lng在后，符合GPX标准！！！）
        # 注意：GPX标准中trkpt的属性是lat（纬度）、lon（经度），且顺序与项目存储相反，必须转换
        gpx_point = gpxpy.gpx.GPXTrackPoint(
            latitude=point["lat"],
            longitude=point["lng"],
            elevation=point["elevation_m"],  # 高程（原生属性，兼容所有软件）
            time=None  # 无时间信息则设为None，也可设置为当前时间：datetime.utcnow()
        )

        # 3.2 添加扩展属性（坡度、距起点距离，不破坏标准GPX结构）
        gpx_point.extensions = [
            # 坡度（度）
            gpxpy.gpx.GPXExtensionElement(
                tag="slope_deg",
                text=str(point["slope_deg"])
            ),
            # 距起点累计距离（米）
            gpxpy.gpx.GPXExtensionElement(
                tag="distance_m",
                text=str(point["distance_m"])
            )
        ]

        # 3.3 将轨迹点添加到轨迹段
        gpx_segment.add_point(gpx_point)

    return gpx

def gpx_to_file_stream(gpx: gpxpy.gpx.GPX, strategy: str) -> StreamingResponse:
    """
    将GPX对象转为FastAPI文件流响应，支持前端直接下载
    :param gpx: 初始化完成的gpxpy.GPX对象
    :param strategy: 路径规划策略（用于生成文件名）
    :return: FastAPI StreamingResponse（GPX文件流）
    """
    # 1. 将GPX对象转为UTF-8编码的XML字符串
    gpx_xml = gpx.to_xml(encoding="utf-8")
    # 2. 转为内存字节流（无需写入本地磁盘）
    stream = io.BytesIO(gpx_xml)
    stream.seek(0)  # 将文件指针移到开头，保证流式读取完整

    # 3. 生成动态文件名（策略_时间戳.gpx，避免重名）
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    strategy_cn = "shortest" if strategy == "shortest" else "gentlest"
    filename = f"hiking_path_{strategy_cn}_{timestamp}.gpx"

    # 4. 构建StreamingResponse，设置响应头（指定文件类型、下载文件名）
    response = StreamingResponse(
        content=stream,
        media_type="application/gpx+xml"  # GPX标准MIME类型，兼容浏览器/下载工具
    )
    # 设置响应头，让浏览器识别为附件并下载
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    # 附加文件大小信息
    response.headers["Content-Length"] = str(len(gpx_xml))

    return response

# -------------------------- 路径规划核心接口 --------------------------
@app.post("/path-planning", summary="路径规划：最短距离/坡度最平缓双策略")
def path_planning(
    start_node_id: int = Body(..., description="起点路网点ID"),
    end_node_id: int = Body(..., description="终点路网点ID"),
    strategy: str = Body(..., description="规划策略：shortest=最短距离，gentlest=坡度最平缓"),
    db: Session = Depends(get_db)
):
    """
    基于NetworkX+Dijkstra算法的路径规划，权重公式：length_m × (1 + α × slope_avg)
    :param start_node_id: 起点节点ID（从/network/nodes接口获取）
    :param end_node_id: 终点节点ID（从/network/nodes接口获取）
    :param strategy: 规划策略，仅支持shortest/gentlest
    :return: 路径节点、经纬度、总长度、平均坡度等信息
    """
    try:
        # 1. 校验策略参数
        valid_strategies = ["shortest", "gentlest"]
        if strategy not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"策略无效，仅支持{valid_strategies}")
        
        # 2. 构建NetworkX内存图
        G = build_networkx_graph(db)
        
        # 3. 校验起点/终点是否在图中
        if start_node_id not in G.nodes:
            raise HTTPException(status_code=404, detail=f"起点节点ID{start_node_id}不在路网中")
        if end_node_id not in G.nodes:
            raise HTTPException(status_code=404, detail=f"终点节点ID{end_node_id}不在路网中")
        if start_node_id == end_node_id:
            raise HTTPException(status_code=400, detail="起点和终点节点ID不能相同")
        
        # 4. 获取坡度权重α，根据策略调整
        alpha = get_slope_weight_alpha(db)
        if strategy == "shortest":
            alpha = 0.0  # 最短距离策略：强制α=0，忽略坡度
        print(f"📌 路径规划参数：策略={strategy}，坡度权重α={alpha}")
        
        # 5. 定义边权重计算函数（适配NetworkX的Dijkstra算法）
        def edge_weight(u, v, d):
            """
            u: 起点节点ID，v: 终点节点ID，d: 边属性字典
            返回：单条边的最终权重
            """
            return d["length_m"] * (1 + alpha * d["slope_avg"])
        
        # 6. 执行Dijkstra算法，计算最短路径（基于自定义权重）
        # 若路径不存在，nx会抛出NetworkXNoPath异常
        node_path = nx.dijkstra_path(G, source=start_node_id, target=end_node_id, weight=edge_weight)
        edge_path = nx.utils.pairwise(node_path)  # 路径边对：(n1,n2), (n2,n3), ...
        
        # 7. 统计路径整体信息（总长度、总坡度、平均坡度等）
        total_length = 0.0  # 总长度（米）
        total_slope = 0.0   # 总坡度和
        edge_count = 0      # 路径边数
        path_edges = []     # 路径边详情
        for u, v in edge_path:
            d = G[u][v]
            total_length += d["length_m"]
            total_slope += d["slope_avg"]
            edge_count += 1
            path_edges.append({
                "edge_id": d["edge_id"],
                "source": u,
                "target": v,
                "length_m": round(d["length_m"], 2),
                "slope_avg": d["slope_avg"],
                "type": d["type"],
                "weight": round(edge_weight(u, v, d), 2)
            })
        # 计算平均坡度（避免除0）
        avg_slope = round(total_slope / edge_count, 2) if edge_count > 0 else 0.0
        total_length = round(total_length, 2)
        
        # 8. 路径节点ID转经纬度坐标（前端地图渲染核心）
        coord_path = []
        for node_id in node_path:
            node = db.query(models.NetworkNode).filter(models.NetworkNode.id == node_id).first()
            if node:
                # 解析节点空间坐标为经纬度
                geom_wkt = db.execute(func.ST_AsText(node.geom)).scalar()
                lng, lat = _parse_wkt_to_lnglat(geom_wkt)  # 复用原有工具函数
                coord_path.append({
                    "node_id": node_id,
                    "lng": lng,
                    "lat": lat
                })
        
        # 步骤8.1：20米等距采样
        sampling_points = path_20m_sampling(coord_path)
        # 步骤8.2：采样点高程、坡度空间插值
        path_sampling_result = path_interpolate_elevation_slope(sampling_points, db)
        # ==========================================================================
        

        # 9. 构造返回结果
        return {
            "code": 200,
            "message": f"路径规划成功（{strategy}策略）",
            "data": {
                "strategy": strategy,
                "slope_weight_alpha": alpha,
                "node_path": node_path,  # 路径节点ID序列 [n1, n2, n3, ...]
                "coord_path": coord_path,  # 路径经纬度序列 [{"node_id":n1, "lng":x, "lat":y}, ...]
                "path_edges": path_edges,  # 路径边详情
                "statistics": {  # 路径统计信息
                    "total_length_m": total_length,
                    "avg_slope_deg": avg_slope,
                    "node_count": len(node_path),
                    "edge_count": edge_count,
                    "sampling_count": len(path_sampling_result),  # 新增：采样点数量
                    "tip": f"α={alpha}：值越大，坡度对路径选择的影响越大"
                },
                "sampling_result": path_sampling_result  # 核心新增：20米采样点（含高程/坡度）
            }
        }

    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail=f"起点{start_node_id}到终点{end_node_id}无可达路径")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ 路径规划失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"路径规划异常：{str(e)[:200]}")

# -------------------------- GPX导出核心接口 --------------------------
@app.post("/path-planning/export-gpx", summary="路径规划GPX导出：生成标准GPX文件流（直接下载）")
def export_path_to_gpx(
    start_node_id: int = Body(..., description="起点路网点ID"),
    end_node_id: int = Body(..., description="终点路网点ID"),
    strategy: str = Body(..., description="规划策略：shortest=最短距离，gentlest=坡度最平缓"),
    db: Session = Depends(get_db)
):
    """
    基于路径规划结果生成标准GPX 1.1文件，直接返回文件流供前端下载
    适配户外导航设备/软件（Garmin、奥维互动地图、两步路等），包含高程/坡度/距起点距离信息
    """
    try:
        # ====================== 复用原有路径规划核心逻辑 ======================
        # 1. 校验策略参数
        valid_strategies = ["shortest", "gentlest"]
        if strategy not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"策略无效，仅支持{valid_strategies}")
        
        # 2. 构建NetworkX内存图
        G = build_networkx_graph(db)
        
        # 3. 校验起点/终点
        if start_node_id not in G.nodes:
            raise HTTPException(status_code=404, detail=f"起点节点ID{start_node_id}不在路网中")
        if end_node_id not in G.nodes:
            raise HTTPException(status_code=404, detail=f"终点节点ID{end_node_id}不在路网中")
        if start_node_id == end_node_id:
            raise HTTPException(status_code=400, detail="起点和终点节点ID不能相同")
        
        # 4. 获取坡度权重α并调整
        alpha = get_slope_weight_alpha(db)
        if strategy == "shortest":
            alpha = 0.0
        
        # 5. 定义边权重函数
        def edge_weight(u, v, d):
            return d["length_m"] * (1 + alpha * d["slope_avg"])
        
        # 6. 执行Dijkstra算法
        node_path = nx.dijkstra_path(G, source=start_node_id, target=end_node_id, weight=edge_weight)
        edge_path = nx.utils.pairwise(node_path)
        
        # 7. 统计路径信息
        total_length = 0.0
        total_slope = 0.0
        edge_count = 0
        for u, v in edge_path:
            d = G[u][v]
            total_length += d["length_m"]
            total_slope += d["slope_avg"]
            edge_count += 1
        avg_slope = round(total_slope / edge_count, 2) if edge_count > 0 else 0.0
        total_length = round(total_length, 2)
        
        # 8. 节点转经纬度坐标
        coord_path = []
        for node_id in node_path:
            node = db.query(models.NetworkNode).filter(models.NetworkNode.id == node_id).first()
            if node:
                geom_wkt = db.execute(func.ST_AsText(node.geom)).scalar()
                lng, lat = _parse_wkt_to_lnglat(geom_wkt)
                coord_path.append({
                    "node_id": node_id,
                    "lng": lng,
                    "lat": lat
                })
        
        # 9. 路径20米采样+高程坡度插值
        sampling_points = path_20m_sampling(coord_path)
        path_sampling_result = path_interpolate_elevation_slope(sampling_points, db)
        sampling_count = len(path_sampling_result)
        # ======================================================================

        # 10. 构造路径统计信息（与路径规划接口一致）
        statistics = {
            "total_length_m": total_length,
            "avg_slope_deg": avg_slope,
            "node_count": len(node_path),
            "edge_count": edge_count,
            "sampling_count": sampling_count
        }

        # 11. 生成GPX对象并转为文件流响应
        gpx_obj = create_gpx_from_path(path_sampling_result, strategy, statistics)
        return gpx_to_file_stream(gpx_obj, strategy)

    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail=f"起点{start_node_id}到终点{end_node_id}无可达路径")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ GPX导出失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"GPX导出异常：{str(e)[:200]}")