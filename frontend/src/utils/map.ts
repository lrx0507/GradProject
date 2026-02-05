// src/utils/map.ts - 纯工具方法，无任何类型声明，所有类型从types/map导入
import type { Ref } from 'vue';
// 仅导入类型，不做任何类型声明
import type { TDMap, TDLngLat, TDTileLayerOptions, TDTileLayer } from '@/types/map';

// 替换为你的有效天地图浏览器端密钥
export const TD_KEY = '83ed38f63fae8ac967cf2e62de6f77a0';
const TD_LOAD_TIMEOUT = 10000;

// 单例防重复加载
let tdScriptLoading = false;

// 加载天地图脚本
const loadTDScript = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (!TD_KEY || TD_KEY.length !== 32) {
      reject(new Error('天地图密钥无效！请替换为32位有效密钥'));
      return;
    }
    if (window.T) {
      resolve();
      return;
    }
    if (tdScriptLoading) {
      const checkLoaded = setInterval(() => {
        window.T && (clearInterval(checkLoaded), resolve());
      }, 100);
      return;
    }
    tdScriptLoading = true;
    const script = document.createElement('script');
    script.src = `https://api.tianditu.gov.cn/api?v=4.0&tk=${TD_KEY}`;
    script.type = 'text/javascript';
    script.onload = () => {
      tdScriptLoading = false;
      window.T ? resolve() : reject(new Error('天地图脚本加载成功，但window.T未定义（密钥错误）'));
    };
    script.onerror = () => {
      tdScriptLoading = false;
      reject(new Error('天地图脚本加载失败（网络/域名限制）'));
    };
    setTimeout(() => {
      tdScriptLoading = false;
      reject(new Error(`天地图加载超时（${TD_LOAD_TIMEOUT/1000}秒）`));
    }, TD_LOAD_TIMEOUT);
    document.head.appendChild(script);
  });
};

// 初始化地图（仅返回TDMap，无类型声明）
export const initTDMap = async (container: Ref<HTMLDivElement | null>): Promise<TDMap> => {
  if (!container.value) {
    throw new Error('地图初始化失败：容器未挂载');
  }
  await loadTDScript();
  // 非空断言安全，loadTDScript已保证window.T存在
  const map = new window.T!.Map(container.value);
   const defaultLngLat = new window.T!.LngLat(118.876202, 31.896178) // 南京方山核心经纬度
  map.centerAndZoom(defaultLngLat, 15); // 缩放级别15（方山区域最佳视野）
  map.enableScrollWheelZoom(true);
  return map;
};

// 添加图层（仅执行逻辑，无类型声明）
export const addTDLayers = (map: TDMap): void => {
  const vecLayer = new window.T!.TileLayer(
    `https://t0.tianditu.gov.cn/vec_w/wmts?tk=${TD_KEY}`,
    { layer: 'vec', style: 'default', tileMatrixSet: 'w', format: 'tiles' } as TDTileLayerOptions
  );
  const cvaLayer = new window.T!.TileLayer(
    `https://t0.tianditu.gov.cn/cva_w/wmts?tk=${TD_KEY}`,
    { layer: 'cva', style: 'default', tileMatrixSet: 'w', format: 'tiles' } as TDTileLayerOptions
  );
  map.addLayer(vecLayer as TDTileLayer);
  map.addLayer(cvaLayer as TDTileLayer);
};