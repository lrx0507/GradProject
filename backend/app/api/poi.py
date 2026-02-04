# backend/app/api/poi.py
from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db import get_db
from app.models.poi import POI as POIModel
from geoalchemy2.functions import ST_AsText

router = APIRouter(prefix="/api/poi", tags=["poi"])

@router.get("/list")
def get_poi_list(db: Session = Depends(get_db)):
    # PostGIS查询：获取POI并转换几何字段为WKT
    poi_list = db.query(
        POIModel.id,
        POIModel.name,
        POIModel.type,
        POIModel.address,
        ST_AsText(POIModel.geom).label("geom"),
        # 提取经纬度（PostGIS函数）
        ST_AsText(ST_X(POIModel.geom)).label("lng"),
        ST_AsText(ST_Y(POIModel.geom)).label("lat")
    ).all()
    
    # 格式化返回
    result = []
    for poi in poi_list:
        result.append({
            "id": poi.id,
            "name": poi.name,
            "type": poi.type,
            "address": poi.address,
            "lnglat": [float(poi.lng), float(poi.lat)],
            "geom": poi.geom
        })
    return result

    # backend/app/api/poi.py
@router.get("/nearby")
def get_nearby_poi(
    lng: float,
    lat: float,
    type: str,
    radius: int = 1000,
    db: Session = Depends(get_db)
):
    # 1. 构造当前位置的几何对象（WGS84坐标系）
    current_geom = f"SRID=4326;POINT({lng} {lat})"
    
    # 2. PostGIS查询：
    # - 筛选类型
    # - 空间范围：半径radius米（ST_DWithin + 球面距离）
    # - 计算距离（ST_Distance_Spheroid）
    # - 按距离排序
    poi_list = db.query(
        POIModel.id,
        POIModel.name,
        POIModel.type,
        POIModel.address,
        ST_AsText(ST_X(POIModel.geom)).label("lng"),
        ST_AsText(ST_Y(POIModel.geom)).label("lat"),
        # 计算球面距离（米）
        ST_Distance_Spheroid(
            POIModel.geom,
            Geometry(current_geom),
            "SPHEROID[\"WGS 84\",6378137,298.257223563]"
        ).label("distance")
    ).filter(
        POIModel.type == type,
        # 空间范围筛选（半径radius米）
        ST_DWithin(
            POIModel.geom,
            Geometry(current_geom),
            radius,
            True # 使用球面距离
        )
    ).order_by("distance").all()
    
    # 3. 格式化返回
    result = []
    for poi in poi_list:
        result.append({
            "id": poi.id,
            "name": poi.name,
            "type": poi.type,
            "address": poi.address,
            "lnglat": [float(poi.lng), float(poi.lat)],
            "distance": float(poi.distance)
        })
    return result