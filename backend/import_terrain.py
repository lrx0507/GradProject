# backend/import_terrain.py
from osgeo import gdal 
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from shapely.geometry import Point
from geoalchemy2.shape import from_shape
from database import SQLALCHEMY_DATABASE_URL  # 复用数据库连接配置
from models import ElevationPoint, SlopePoint  # 导入高程/坡度模型
from sqlalchemy.orm import Session

# -------------------------- 1. 修改：DEM文件路径 --------------------------
# 指向 terrain_data 文件夹下的 fangshan_dem.tif
DEM_FILE_PATH = "./terrain_data/fangshan_dem.tiff"
# 生成的坡度文件路径（自动保存到 terrain_data）
SLOPE_FILE_PATH = "./terrain_data/slope.tif"
# 临时CSV文件路径（导入后可删除）
ELEVATION_CSV = "./terrain_data/elevation.csv"
SLOPE_CSV = "./terrain_data/slope.csv"

# -------------------------- 2. 初始化数据库连接（无需修改） --------------------------
engine = create_engine(SQLALCHEMY_DATABASE_URL)
db = Session(bind=engine)

# -------------------------- 3. DEM转CSV（读取fangshan_dem.tif） --------------------------
def tif_to_csv(tif_path, output_csv, is_slope=False):
    """
    将DEM/坡度TIF文件转为CSV（经纬度+高程/坡度）
    :param tif_path: TIF文件路径（fangshan_dem.tif 或 slope.tif）
    :param output_csv: 输出CSV路径
    :param is_slope: 是否为坡度文件（区分高程/坡度字段名）
    """
    # 读取TIF文件（依赖GDAL，需提前安装成功）
    ds = gdal.Open(tif_path)
    if not ds:
        raise FileNotFoundError(f"找不到TIF文件：{tif_path}，请检查路径是否正确")
    
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()  # 读取高程/坡度矩阵
    geotransform = ds.GetGeoTransform()  # 获取地理坐标信息（关键）
    
    # 计算经纬度范围（WGS84坐标，与数据库保持一致）
    min_lon = geotransform[0]  # 左上角经度
    max_lat = geotransform[3]  # 左上角纬度
    lon_res = geotransform[1]  # 经度分辨率（每像素代表的经度差）
    lat_res = geotransform[5]  # 纬度分辨率（每像素代表的纬度差，通常为负数）
    
    # 提取有效数据（过滤NaN/无效值）
    data = []
    for i in range(arr.shape[0]):  # 行（纬度方向）
        for j in range(arr.shape[1]):  # 列（经度方向）
            value = arr[i, j]
            # 过滤无效值（DEM常见无效值为-9999或NaN）
            if value < 0 or np.isnan(value):
                continue
            # 计算当前像素的经纬度
            lon = min_lon + j * lon_res
            lat = max_lat + i * lat_res
            # 按类型添加数据（高程/坡度字段名区分）
            if is_slope:
                data.append({"lon": lon, "lat": lat, "slope_deg": value})
            else:
                data.append({"lon": lon, "lat": lat, "elevation_m": value})
    
    # 保存为CSV（后续导入数据库用）
    pd.DataFrame(data).to_csv(output_csv, index=False, encoding="utf-8")
    print(f"成功生成CSV：{output_csv}，共 {len(data)} 条数据")

# -------------------------- 4. 生成坡度文件（从fangshan_dem.tif派生） --------------------------
def generate_slope_tif():
    """
    从DEM文件生成坡度TIF（依赖GDAL的gdaldem工具）
    """
    # 调用GDAL命令生成坡度（单位：度）
    gdal.DEMProcessing(
        destName=SLOPE_FILE_PATH,
        srcDS=gdal.Open(DEM_FILE_PATH),
        processing="slope",
        computeEdges=True,  # 计算边缘像素坡度
        band=1  # 使用DEM的第1波段（高程数据）
    )
    print(f"成功生成坡度文件：{SLOPE_FILE_PATH}")

# -------------------------- 5. CSV导入数据库（高程点/坡度点） --------------------------
def import_elevation_to_db(csv_path):
    """将高程CSV导入elevation_points表"""
    df = pd.read_csv(csv_path)
    batch_size = 1000  # 批量插入，避免数据库压力
    count = 0
    
    for _, row in df.iterrows():
        # 创建Shapely点（经纬度顺序：lon在前，lat在后）
        point = Point(row["lon"], row["lat"])
        # 转为PostGIS的Geometry类型（SRID=4326，与数据库一致）
        geom = from_shape(point, srid=4326)
        
        # 构造高程点对象
        elev_point = ElevationPoint(
            geom=geom,
            elevation_m=round(row["elevation_m"], 2)  # 保留2位小数
        )
        
        db.add(elev_point)
        count += 1
        
        # 每1000条提交一次
        if count % batch_size == 0:
            db.commit()
            print(f"已导入 {count} 个高程点")
    
    # 提交剩余数据
    db.commit()
    print(f"高程点导入完成，共 {count} 条数据")

def import_slope_to_db(csv_path):
    """将坡度CSV导入slope_points表（逻辑与高程类似）"""
    df = pd.read_csv(csv_path)
    batch_size = 1000
    count = 0
    
    for _, row in df.iterrows():
        point = Point(row["lon"], row["lat"])
        geom = from_shape(point, srid=4326)
        
        slope_point = SlopePoint(
            geom=geom,
            slope_deg=round(row["slope_deg"], 2)
        )
        
        db.add(slope_point)
        count += 1
        
        if count % batch_size == 0:
            db.commit()
            print(f"已导入 {count} 个坡度点")
    
    db.commit()
    print(f"坡度点导入完成，共 {count} 条数据")

# -------------------------- 6. 主执行逻辑（按顺序调用） --------------------------
if __name__ == "__main__":
    try:
        # 步骤1：DEM转高程CSV
        print("=== 开始处理DEM文件 ===")
        tif_to_csv(DEM_FILE_PATH, ELEVATION_CSV, is_slope=False)
        
        # 步骤2：生成坡度TIF
        print("\n=== 开始生成坡度文件 ===")
        generate_slope_tif()
        
        # 步骤3：坡度TIF转CSV
        print("\n=== 开始处理坡度文件 ===")
        tif_to_csv(SLOPE_FILE_PATH, SLOPE_CSV, is_slope=True)
        
        # 步骤4：导入高程数据到数据库
        print("\n=== 开始导入高程点 ===")
        import_elevation_to_db(ELEVATION_CSV)
        
        # 步骤5：导入坡度数据到数据库
        print("\n=== 开始导入坡度点 ===")
        import_slope_to_db(SLOPE_CSV)
        
        print("\n✅ 所有地形数据处理完成！")
    
    except Exception as e:
        print(f"\n❌ 处理失败：{str(e)}")
        db.rollback()  # 出错时回滚数据库
    finally:
        db.close()  # 关闭数据库连接