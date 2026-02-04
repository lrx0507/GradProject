# backend/app/api/route.py
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db import get_db
from geoalchemy2.functions import ST_MakeLine, ST_AddPoint, ST_Length_Spheroid
from geoalchemy2.types import Geometry
import random # 模拟坡度/高程（实际需用DEM数据）

router = APIRouter(prefix="/api/route", tags=["route"])

# 路径规划参数模型
class RoutePlanParams(BaseModel):
    start: list[float] # [lng, lat]
    end: list[float] # [lng, lat]
    strategy: str = "leastTime"

# 模拟坡度/高程计算
def calc_slope_elevation(points: list) -> list:
    result = []
    total_distance = 0
    for i, (lng, lat) in enumerate(points):
        # 模拟距离（米）
        distance = total_distance + (i * 100) if i > 0 else 0
        # 模拟坡度（-5% ~ 15%）
        slope = random.uniform(-5, 15)
        # 模拟高程（50 ~ 200米）
        elevation = random.uniform(50, 200)
        result.append({
            "lnglat": [lng, lat],
            "slope": slope,
            "elevation": elevation,
            "distance": distance
        })
        total_distance = distance
    return result

@router.post("/plan")
def plan_route(params: RoutePlanParams, db: Session = Depends(get_db)):
    # 1. PostGIS：构造起点/终点几何对象
    start_geom = f"SRID=4326;POINT({params.start[0]} {params.start[1]})"
    end_geom = f"SRID=4326;POINT({params.end[0]} {params.end[1]})"
    
    # 2. 模拟路线节点（实际需用PostGIS的pgrouting插件做路径分析）
    # 此处简化：生成起点到终点的插值点
    step = 0.001 # 经纬度步长
    lng_diff = params.end[0] - params.start[0]
    lat_diff = params.end[1] - params.start[1]
    steps = max(abs(int(lng_diff / step)), abs(int(lat_diff / step))) or 10
    
    route_points = []
    for i in range(steps + 1):
        lng = params.start[0] + (lng_diff / steps) * i
        lat = params.start[1] + (lat_diff / steps) * i
        route_points.append([lng, lat])
    
    # 3. 计算坡度/高程
    points_with_slope = calc_slope_elevation(route_points)
    
    # 4. 构造高程剖面数据
    elevation_profile = [{"x": p["distance"], "y": p["elevation"]} for p in points_with_slope]
    
    # 5. 计算总距离（PostGIS球面距离）
    line_geom = ST_MakeLine(
        Geometry(start_geom), 
        Geometry(end_geom)
    )
    total_distance = ST_Length_Spheroid(line_geom, "SPHEROID[\"WGS 84\",6378137,298.257223563]")
    
    # 6. 构造返回数据
    return {
        "id": str(random.randint(1000, 9999)),
        "name": f"路线-{params.strategy}",
        "desc": f"{params.strategy}策略路线",
        "points": points_with_slope,
        "totalDistance": float(total_distance),
        "totalDuration": int(total_distance / 10), # 模拟时长（速度10m/s）
        "elevationProfile": elevation_profile
    }